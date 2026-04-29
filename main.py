import random
import re
Progs = ["prog1.txt"]
pcbs = []
pcbs_blocked = []
pcbs_waiting = []

# PROCESS CONTROL BLOCK
# cadastro de cada processo -> guarda tudo que precisa pra continuar de onde parou
# temos duas categorias neste caso -> estado de exec. e info. de escalonamento
class PCB:
    def __init__(self, name, instructions, data, period, ci, arrival_time):
        self.name = name #nome do processo

        #EXECUCAO -> salva o processo quando ele eh pausado
        self.instructions = instructions    # instrucoes parseadas de .code
        self.data = data                    # dic. de vars dda memoria do processo
        self.pc = 0                         # idx da proxima instrucao
        self.acc = 0                        # acumulador

        #ESCALONAMENTO -> o que o EDF vai usar para tomar decisoes
        self.state ="ready"                     # estado do processo -> running/ready/blocked
        self.period = period                    # periodo da tarefa -> intervalo entre ativacoes
        self.ci = ci                            # tempo de computacao maxima
        self.used_ci = 0                        # tempo de computacao usado
        self.arrival_time = arrival_time        # instate que tarefa chega ao sistema
        self.deadline = arrival_time + period   # deadline absoluto
        self.block_time = 0                     # contador regressivo -> usar no SYSCALL


# PARSER - separar code de data - carrega e inicializa programas
def parser(file_name, period, ci, arrival_time):
    instructions = []       # lista de instrucoes
    data = {}               # dic. vars do processo
    labels = {}             # dic. para onde labels apontam (loop -> idx3)
    mode = None             # secao atual do arquivo

    # 1 -> separar modes, add labels e data
    # le o arquivo linha  linha separando codigo de dado, tira comentarios
    lines_code_raw = []
    with open(file_name, "r") as f:
        for line in f:

            # remove comentarios e linhas vazias
            line = line.strip()
            if not line or line.startswith("#"): continue
            line = re.split(r'\s+#(?!\S)', line)[0].strip()

            # mode define qual secao o parser ta agr
            if line == ".code": mode = "code"
            elif line == ".endcode": mode = None
            elif line == ".data": mode = "data"
            elif line == ".enddata": mode = None

            elif mode == "code": lines_code_raw.append(line)
            elif mode == "data":
                part = line.split()
                data[part[0]] = int(part[1])


    # 2 -> mapear labels para os indices
    # percorre codigo identificando labels e registrando a que indx aponta
    # instrucoes de salto vao referenciar essas labels pelo nome
    # prog2 deve ficar -> {"loop": 0, "fim": 6}
    idx =0
    no_label_lines = []
    for line in lines_code_raw:
        # percorre linhas do code procurando por qql coisa com :
        if ":" in line:
            part = line.split(":")
            labels[part[0].strip()] = idx   # registra indx da label
            rest = part[1].strip()
            if not rest: continue           # label sozinha, sem mais instrucoes
            line = rest                     # continua com a instrucao que tava depois do :
        no_label_lines.append(line)         # labels somem da lista de instrucoes, so existem no dic. labels
        idx += 1


    # 3 -> monta lista final trocando os nomes de label por indx
    # cada instrucao deve ficar como uma lista ["LOAD", "a"], ["SUB", "#1"], ["BRZERO", 6]
    jumps = {"BRANY", "BRPOS", "BRZERO", "BRNEG"}
    for line in no_label_lines:
        part = line.split()
        opcode = part[0].upper()
        if opcode in jumps:
            part[1] = labels[part[1]]
        instructions.append(part)

    return PCB(file_name, instructions, data, period, ci, arrival_time)


def executar():
    syscall = 0 #flag do SO
    active = 0
    time = 0
    acc = 0 # apenas para flag do SO

    MAX_TIME = 100
    while (len(pcbs) > 0 or len(pcbs_blocked) > 0 or len(pcbs_waiting) >0) and time < MAX_TIME:

        # 1-> ==== ATUALIZA BLOQUEADOS ================================================================
        for pcb in pcbs_blocked[:]:
            pcb.block_time -= 1
            if pcb.block_time <= 0:  # dareDY E TROCA DE FILA
                pcb.state = "ready"
                pcb.deadline = time + pcb.period
                pcbs.append(pcb)
                pcbs_blocked.remove(pcb)

        # 2-> ==== VERIFICA ARRIVAL TIME ================================================================
        for pcb in pcbs_waiting[:]:
            if pcb.arrival_time <= time:
                pcb.state = "ready"
                pcbs.append(pcb)
                pcbs_waiting.remove(pcb)

        # 3-> ==== TRATA SYSCALL ================================================================
        if syscall == 1:
            if acc == 0:  # termina o programa
                print(f"Processo {pcbs[active].name} terminou, matando processo")
                pcbs.pop(active)
                syscall = 0
            elif acc == 1:  # imprime o valor do acc
                print(f"Processo {pcbs[active].name} pediu para imprimir valor: {pcbs[active].acc}")
                pcbs[active].block_time = random.randint(1, 3)
                pcbs[active].state = "blocked"
                pcbs_blocked.append(pcbs.pop(active))  # remove do pcbs e coloca no blocked
                syscall = 0
            elif acc == 2:  # le um valor inteiro e salva no acc
                pcbs[active].acc = int(input(f"Processo {pcbs[active].name} pediu para ler um valor inteiro: "))
                pcbs[active].block_time = random.randint(1, 3)
                pcbs[active].state = "blocked"
                pcbs_blocked.append(pcbs.pop(active))  # remove do pcbs e coloca no blocked
                syscall = 0
            active = escalonar(active, time)
            continue

        # 4-> ==== CHAMA ESCALONADOR ================================================================
        if len (pcbs) == 0:
            time +=1
            continue
        active = escalonar(active, time)

        # 5-> ==== EXECUTA INSTRUCOES ================================================================
        pcbs[active].state = "running"
        instr = pcbs[active].instructions[pcbs[active].pc]
        #print(f"DEBUG: [t={time}] {pcbs[active].name} | pc={pcbs[active].pc} | acc={pcbs[active].acc} | instr={instr}")
        # ARITMETICO ---------------------------------------
        if instr[0] == "add":
            if instr[1].startswith("#"):  # imediato
                pcbs[active].acc += int(instr[1][1:])
            else:  # variavel
                pcbs[active].acc += pcbs[active].data[instr[1]]
        elif instr[0] == "sub":
            if instr[1].startswith("#"):
                pcbs[active].acc -= int(instr[1][1:])
            else:
                pcbs[active].acc -= pcbs[active].data[instr[1]]
        elif instr[0] == "mult":
            if instr[1].startswith("#"):
                pcbs[active].acc *= int(instr[1][1:])
            else:
                pcbs[active].acc *= pcbs[active].data[instr[1]]
        elif instr[0] == "div":
            if instr[1].startswith("#"):
                pcbs[active].acc /= int(instr[1][1:])
            else:
                pcbs[active].acc /= pcbs[active].data[instr[1]]
        # MEMORIA ---------------------------------------
        elif instr[0] == "load":
            if instr[1].startswith("#"):
                pcbs[active].acc -= int(instr[1][1:])
            else:
                pcbs[active].acc = pcbs[active].data[instr[1]]
        elif instr[0] == "store":
            pcbs[active].data[instr[1]] = pcbs[active].acc
        # SALTO -----------------------------------------
        elif instr[0] == "BRANY":
            pcbs[active].pc = instr[1]
            pcbs[active].used_ci += 1
            time += 1
            continue
        elif instr[0] == "BRPOS":
            if pcbs[active].acc > 0:
                pcbs[active].pc = instr[1]
                pcbs[active].used_ci += 1
                time += 1
                continue
        elif instr[0] == "BRZERO":
            if pcbs[active].acc == 0:
                pcbs[active].pc = instr[1]
                pcbs[active].used_ci += 1
                time += 1
                continue
        # eu sei que nos exemplos nao tem BRNEG mas vai que ne
        elif instr[0] == "BRNEG":
            if pcbs[active].acc < 0:
                pcbs[active].pc = instr[1]
                pcbs[active].used_ci += 1
                time += 1
                continue
        # SISTEMA ---------------------------------------
        elif instr[0] == "syscall":
            # salva contexto e mando pro SO
            pcbs[active].state = "ready"
            acc = int(instr[1])  # acc recebe o pedido do processo
            syscall = 1

        # 6-> ==== VERIFICA CI E REAGENDA ================================================================
        pcbs[active].pc += 1
        pcbs[active].used_ci += 1
        if pcbs[active].used_ci >= pcbs[active].ci:
            pcbs[active].used_ci = 0
            pcbs[active].pc = 0
            pcbs[active].acc = 0
            pcbs[active].deadline = time + pcbs[active].period
            pcbs[active].state = "ready"

        # 7-> ==== VERIFICA DEADLINE ================================================================
        for pcb in pcbs + pcbs_blocked:
            if time > pcb.deadline:
                print(f"Deadline perdido: {pcb.name} no instante {time}")

        time +=1

# ESCALONADOR - implementa EDF
def escalonar(active, time):
    if len(pcbs) == 0:
        return 0
    smallest = 0
    for n in range(len(pcbs)):
        if pcbs[n].deadline < pcbs[smallest].deadline:
            smallest = n
    if smallest != active:
        print(f"[t={time}] Escalonando: {pcbs[smallest].name} (deadline: {pcbs[smallest].deadline})")
    return smallest

# INTERFACE - entrada e saida
def interface(pcb):
    pass
    # tipo perguntar se quer rodar a proxima intrucao ou imprimir contexto, e tbm tem q separa os blocked e ready

if __name__ == '__main__':
    pcb1 = parser("prog1.txt", period=10, ci=6, arrival_time=0)
    pcb2 = parser("prog2.txt", period=20, ci=19, arrival_time=3)
    pcb3 = parser("prog3.txt", period=10, ci=7, arrival_time=5)
    pcbs_waiting.extend([pcb1, pcb2, pcb3])
    executar()


