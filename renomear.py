import random
import re
import sys

# sch_pol = 1 e exigencia do enunciado para identificar a politica usada (1 = EDF)
sch_pol = 1


# ---------------------------------------------------------------------------
# PCB - Process Control Block
# Guarda todo o estado de um processo: o que ele precisa para continuar de
# onde parou (contexto de execucao) e o que o escalonador precisa para tomar
# decisoes (informacoes de escalonamento).
# ---------------------------------------------------------------------------
class PCB:
    def __init__(self, name, instructions, data, period, ci, arrival_time):
        self.name = name

        # --- contexto de execucao (salvo/restaurado a cada troca de contexto) ---
        self.instructions = instructions  # lista de instrucoes parseadas do .code
        self.data = data                  # dicionario de variaveis da area .data
        self.pc = 0                       # program counter: indice da proxima instrucao
        self.acc = 0                      # acumulador: unico registrador de calculo

        # --- informacoes de escalonamento (usadas pelo EDF) ---
        self.state = "ready"              # estado atual: "ready", "running" ou "blocked"
        self.period = period              # periodo da tarefa (Pi): intervalo entre ativacoes
        self.ci = ci                      # tempo de computacao maximo por periodo (Ci - WCET)
        self.ci_remaining = ci            # quanto do Ci ainda resta no periodo atual
        self.arrival_time = arrival_time  # instante em que a tarefa entra no sistema
        self.deadline = arrival_time + period  # deadline absoluto: arrival + period (di = Pi)
        self.block_time = 0               # contador regressivo de bloqueio (SYSCALL 1 e 2)


# ---------------------------------------------------------------------------
# PARSER
# Le um arquivo .asm com secoes .code/.data e devolve um PCB pronto.
# O processo tem 3 passagens:
#   1. Separa as linhas de codigo das de dado, removendo comentarios
#   2. Mapeia labels (ex: "loop:") para o indice numerico da instrucao seguinte
#   3. Monta a lista final de instrucoes, substituindo nomes de label por indice
# ---------------------------------------------------------------------------
def parser(file_name, period, ci, arrival_time):
    instructions = []
    data = {}
    labels = {}   # ex: {"loop": 3, "fim": 15}
    mode = None
    lines_code_raw = []

    # Passagem 1: separar secoes e remover comentarios
    with open(file_name, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # remove comentario inline (ex: "ADD #1  # soma 1") -> "ADD #1"
            line = re.split(r'\s+#(?!\S)', line)[0].strip()

            if line == ".code":
                mode = "code"
            elif line == ".endcode":
                mode = None
            elif line == ".data":
                mode = "data"
            elif line == ".enddata":
                mode = None
            elif mode == "code":
                lines_code_raw.append(line)
            elif mode == "data":
                part = line.split()
                data[part[0]] = int(part[1])

    # Passagem 2: identificar labels e registrar o indice para onde cada uma aponta
    # Ex: "loop: BRZERO fim" -> labels["loop"] = idx_atual, instrucao = "BRZERO fim"
    idx = 0
    no_label_lines = []
    for line in lines_code_raw:
        if ":" in line:
            part = line.split(":", 1)
            labels[part[0].strip()] = idx
            rest = part[1].strip()
            if not rest:
                continue   # linha so tinha o label, sem instrucao junto
            line = rest
        no_label_lines.append(line)
        idx += 1

    # Passagem 3: montar lista de instrucoes substituindo nomes de label por indice
    # instrucoes de salto ficam como ex: ["BRZERO", 15] em vez de ["BRZERO", "fim"]
    # isso evita ter que resolver o nome toda vez que a instrucao executa
    jumps = {"BRANY", "BRPOS", "BRZERO", "BRNEG"}
    for line in no_label_lines:
        part = line.split()
        part[0] = part[0].upper()   # normaliza opcode para maiusculo
        if part[0] in jumps:
            part[1] = labels[part[1]]
        instructions.append(part)

    return PCB(file_name, instructions, data, period, ci, arrival_time)


# ---------------------------------------------------------------------------
# EXECUTE_INSTRUCTION
# Executa UMA instrucao do processo pcb (a instrucao apontada por pc).
# Atualiza acc, data e pc conforme o opcode.
# Retorna o valor do SYSCALL se a instrucao for SYSCALL, ou None caso contrario.
#
# Sobre o PC:
#   - instrucoes normais: pc += 1 ao final
#   - instrucoes de salto: pc = indice_alvo (jumped=True impede o += 1)
#   - SYSCALL: pc += 1 antes de retornar, para que ao retomar o processo
#     ele execute a instrucao SEGUINTE ao SYSCALL, nao o proprio SYSCALL de novo
# ---------------------------------------------------------------------------
def execute_instruction(pcb):
    instr = pcb.instructions[pcb.pc]
    jumped = False
    syscall_val = None

    # resolve o operando: "#5" -> 5 (imediato), "a" -> data["a"] (direto)
    def operand(op):
        return int(op[1:]) if op.startswith("#") else pcb.data[op]

    if instr[0] == "ADD":
        pcb.acc += operand(instr[1])
    elif instr[0] == "SUB":
        pcb.acc -= operand(instr[1])
    elif instr[0] == "MULT":
        pcb.acc *= operand(instr[1])
    elif instr[0] == "DIV":
        pcb.acc //= operand(instr[1])   # divisao inteira, como esperado em assembly
    elif instr[0] == "LOAD":
        pcb.acc = operand(instr[1])
    elif instr[0] == "STORE":
        pcb.data[instr[1]] = pcb.acc    # STORE so suporta modo direto (nome de variavel)
    elif instr[0] == "BRANY":
        pcb.pc = instr[1]
        jumped = True
    elif instr[0] == "BRPOS":
        if pcb.acc > 0:
            pcb.pc = instr[1]
            jumped = True
    elif instr[0] == "BRZERO":
        if pcb.acc == 0:
            pcb.pc = instr[1]
            jumped = True
    elif instr[0] == "BRNEG":
        if pcb.acc < 0:
            pcb.pc = instr[1]
            jumped = True
    elif instr[0] == "SYSCALL":
        syscall_val = int(instr[1])

    if not jumped:
        pcb.pc += 1

    return syscall_val


# ---------------------------------------------------------------------------
# ESCALONADOR EDF (Earliest Deadline First)
# Recebe a fila de prontos e o processo em execucao.
# Ordena a fila por deadline absoluto (menor deadline = maior prioridade).
# Se o processo no topo da fila tiver deadline menor que o processo rodando,
# faz a preempcao: salva o contexto do atual e coloca o novo para rodar.
# O contexto (pc, acc, ci_remaining) ja esta no PCB, nao precisa copiar nada.
# ---------------------------------------------------------------------------
def escalonar(ready_queue, running):
    ready_queue.sort(key=lambda p: p.deadline)

    if not ready_queue:
        return running

    # nenhum processo rodando: pega o primeiro da fila
    if running is None:
        proc = ready_queue.pop(0)
        proc.state = "running"
        return proc

    # preempcao: processo na fila tem deadline mais urgente que o atual
    if ready_queue[0].deadline < running.deadline:
        running.state = "ready"
        ready_queue.append(running)
        ready_queue.sort(key=lambda p: p.deadline)
        proc = ready_queue.pop(0)
        proc.state = "running"
        return proc

    return running


# ---------------------------------------------------------------------------
# _NOVO_PERIODO
# Chamada quando um processo termina seu periodo atual, seja por:
#   - SYSCALL 0 (halt): o programa chegou ao fim naturalmente
#   - CI esgotado: usou todo o tempo de CPU permitido no periodo
# Reseta o estado de execucao (pc=0, acc=0, ci=ci_max) e calcula o novo
# deadline absoluto somando mais um periodo ao deadline anterior.
# A area .data NAO e resetada: o estado de memoria persiste entre periodos.
# ---------------------------------------------------------------------------
def _novo_periodo(pcb, time, ready_queue):
    pcb.deadline += pcb.period  # novo deadline = deadline_anterior + periodo
    pcb.pc = 0
    pcb.acc = 0
    pcb.ci_remaining = pcb.ci
    pcb.state = "ready"
    ready_queue.append(pcb)


# ---------------------------------------------------------------------------
# INTERFACE
# Imprime o estado do sistema a cada tick e registra na timeline.
# Exibe: processo rodando, instrucao executada, acc, deadline, ci restante,
# filas de prontos e bloqueados.
# ---------------------------------------------------------------------------
def interface(time, last_instr, running, ready_queue, blocked_queue, timeline):
    nome = running.name if running else "IDLE"
    timeline.append((time, nome))

    print(f"[t={time:3d}] {nome:<20}", end="")
    if running:
        print(f" instr={str(last_instr):<25} acc={running.acc:<6} deadline={running.deadline:<5} ci_rem={running.ci_remaining}", end="")
    print()

    if ready_queue:
        nomes = ", ".join(f"{p.name}(d={p.deadline})" for p in ready_queue)
        print(f"         prontos   : {nomes}")
    if blocked_queue:
        nomes = ", ".join(f"{p.name}(bt={p.block_time})" for p in blocked_queue)
        print(f"         bloqueados: {nomes}")


# ---------------------------------------------------------------------------
# EXECUTAR
# Loop principal da simulacao. Cada iteracao representa um tick de tempo.
# Ordem de operacoes por tick:
#   1. Chegada de processos com arrival_time <= time
#   2. Decremento do block_time dos bloqueados; desbloqueia quem zerou
#   3. Deteccao de deadline miss
#   4. Escalonamento EDF (pode causar preempcao)
#   5. Execucao de UMA instrucao do processo ativo
#   6. Tratamento do resultado: SYSCALL ou CI esgotado
# ---------------------------------------------------------------------------
def executar(all_pcbs):
    time = 0
    ready_queue = []    # processos prontos para executar, ordenados por deadline
    blocked_queue = []  # processos aguardando fim de operacao de I/O
    running = None      # processo ocupando a CPU agora (None = CPU ociosa)
    pending = sorted(list(all_pcbs), key=lambda p: p.arrival_time)  # ainda nao chegaram
    timeline = []       # historico de (tempo, nome) para exibir ao final

    max_time = 500  # limite de seguranca para nao rodar infinitamente

    print("\n=== INICIO DA SIMULACAO ===\n")

    while time < max_time:
        # condicao de termino: nenhum processo em nenhum estado
        if not pending and not ready_queue and not blocked_queue and running is None:
            print(f"\n=== Simulacao concluida no tempo {time} ===")
            break

        # 1. Chegada de novos processos
        novos = [p for p in pending if p.arrival_time <= time]
        for p in novos:
            p.state = "ready"
            ready_queue.append(p)
            pending.remove(p)
            print(f"[t={time:3d}] >>> {p.name} chegou (periodo={p.period}, ci={p.ci}, deadline={p.deadline})")

        # 2. Desbloquear processos cujo block_time expirou
        ainda_bloqueados = []
        for pcb in blocked_queue:
            pcb.block_time -= 1
            if pcb.block_time <= 0:
                if pcb.ci_remaining <= 0:
                    # o processo usou todo o CI antes de bloquear: inicia novo periodo
                    # sem voltar para ready, pois nao tem mais CPU budget neste periodo
                    print(f"[t={time:3d}]     {pcb.name} CI esgotado ao desbloquear -> novo deadline={pcb.deadline + pcb.period}")
                    _novo_periodo(pcb, time, ready_queue)
                else:
                    pcb.state = "ready"
                    ready_queue.append(pcb)
                    print(f"[t={time:3d}] >>> {pcb.name} desbloqueado")
            else:
                ainda_bloqueados.append(pcb)
        blocked_queue = ainda_bloqueados

        # 3. Verificar perda de deadline
        todos = ready_queue + blocked_queue + ([running] if running else [])
        for pcb in todos:
            if time > pcb.deadline:
                print(f"[t={time:3d}] [!] DEADLINE MISS: {pcb.name} (deadline={pcb.deadline})")

        # 4. Escalonar (EDF): pode trocar o processo que esta rodando
        running = escalonar(ready_queue, running)

        # 5. Executar uma instrucao
        if running is None:
            timeline.append((time, "IDLE"))
            print(f"[t={time:3d}] CPU ociosa")
            time += 1
            continue

        last_instr = running.instructions[running.pc]
        syscall_val = execute_instruction(running)
        running.ci_remaining -= 1   # cada instrucao consome 1 unidade de CI

        interface(time, last_instr, running, ready_queue, blocked_queue, timeline)
        time += 1

        # 6. Tratar resultado da instrucao executada
        if syscall_val == 0:
            # SYSCALL 0: halt - programa finalizou, reinicia no proximo periodo
            print(f"[t={time-1:3d}]     {running.name} finalizou periodo (SYSCALL 0) -> novo deadline={running.deadline + running.period}")
            _novo_periodo(running, time - 1, ready_queue)
            running = None

        elif syscall_val == 1:
            # SYSCALL 1: imprime o valor do acumulador e bloqueia por 1-3 ticks
            print(f"[t={time-1:3d}]     {running.name} imprime: {running.acc}")
            running.block_time = random.randint(1, 3)
            running.state = "blocked"
            blocked_queue.append(running)
            running = None

        elif syscall_val == 2:
            # SYSCALL 2: le um inteiro do teclado, salva no acc e bloqueia por 1-3 ticks
            val = int(input(f"[t={time-1:3d}]     {running.name} le inteiro: "))
            running.acc = val
            running.block_time = random.randint(1, 3)
            running.state = "blocked"
            blocked_queue.append(running)
            running = None

        elif running is not None and running.ci_remaining <= 0:
            # CI esgotado por instrucao normal (nao por SYSCALL): fim do periodo
            print(f"[t={time-1:3d}]     {running.name} esgotou CI -> novo deadline={running.deadline + running.period}")
            _novo_periodo(running, time - 1, ready_queue)
            running = None

    # Exibe a timeline completa ao final da simulacao
    print("\n=== TIMELINE DE ESCALONAMENTO ===")
    print("Tempo | Processo")
    print("------+--------------------")
    for t, nome in timeline:
        print(f"  {t:3d} | {nome}")


# ---------------------------------------------------------------------------
# CARREGAR_PROCESSOS
# Interface de entrada: pede ao usuario o arquivo .asm, periodo, CI e
# arrival time de cada processo. Repete ate o usuario pressionar Enter vazio.
# ---------------------------------------------------------------------------
def carregar_processos():
    processos = []
    print("=== Carregamento de processos ===")
    print("Digite os dados de cada processo. Pressione Enter sem arquivo para iniciar.\n")

    while True:
        nome = input("Arquivo do programa (ou Enter para iniciar simulacao): ").strip()
        if not nome:
            break
        try:
            period = int(input(f"  Periodo de '{nome}': "))
            ci = int(input(f"  Tempo de computacao (CI) de '{nome}': "))
            arrival = int(input(f"  Arrival time de '{nome}': "))
            pcb = parser(nome, period, ci, arrival)
            processos.append(pcb)
            print(f"  '{nome}' carregado com sucesso.\n")
        except Exception as e:
            print(f"  Erro ao carregar '{nome}': {e}\n")

    return processos


# ---------------------------------------------------------------------------
# _Tee: duplica a saida para terminal e arquivo ao mesmo tempo.
# Necessario porque sys.stdout = arquivo redirecionaria so para o arquivo,
# perdendo a visualizacao no terminal durante a execucao.
# ---------------------------------------------------------------------------
class _Tee:
    def __init__(self, log_file):
        self._term = sys.__stdout__
        self._file = log_file

    def write(self, s):
        self._term.write(s)
        self._file.write(s)

    def flush(self):
        self._term.flush()
        self._file.flush()


if __name__ == '__main__':
    processos = carregar_processos()
    if not processos:
        print("Nenhum processo carregado. Encerrando.")
    else:
        with open('simulacao.txt', 'w', encoding='utf-8') as f:
            sys.stdout = _Tee(f)
            try:
                executar(processos)
            finally:
                sys.stdout = sys.__stdout__
        print("Saida salva em simulacao.txt")
