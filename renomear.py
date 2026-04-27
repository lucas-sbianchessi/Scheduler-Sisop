import queue
import threading
import re
Progs = ["prog1.txt"]
pcbs = []
validInstrs = ["ADD", "SUB", "MULT", "DIV", "LOAD", "STORE", "BRANY", "BRPOS", "BRZERO", "SYSCALL"] #pra veificacao no carregarProgs


# PARTIDO COMUNISTA BRASILEIRO ou PROCESS CONTROL BLOCK
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
        self.arrival_time = arrival_time        # instate que tarefa chega ao sistema
        self.deadline = arrival_time + period   # deadline absoluto TODO ta com cara errada
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



# EXECUCAO - Execucao em geral do trabalho

# EXECUTOR - execucao geral

    # para cada tick de tempo:

        # 1-> verificar processos bloqueados
            # decrementar block_time de cada processo bloqueado
            # se block_time = 0, muda estado para ready

        # 2-> verificar a chegada de novos processos
            # se arrival_time de algum processo == tempo_atual, adiciona na fila de prontos

        # 3-> chamar o escalonador (CHAMADO TODA VEZ QUE ENTRA NOVO PROCESSO)
            # ordena fila de prontos por deadline (menor = maior prioridade)
            # se o processo no topo da lista for diferente do que esta rodando, preempta

        # 4-> executar uma instrucao do processo ativo
            # pega instrucao em instructions(pc)
            # executa de acordo com opcode
            # incrementa pc
            # incrementa tempo

        # 5-> tratar resultado da instrucao
            # SYSCALL 0 = termina o processo, remove da lista
            # SYSCALL 1 = imprime acc, bloqueia processo com tempo entre 1 e 3
            # SYSCALL 2 = le do teclado, salva no acc, bloqueia com tempo entre 1 e 3
            # SALTO = pc ja foi atualizado pela instrucao, nao incrementa de novo
                #

        # 6-> verificar deadline
            # se tempo atual >= deadline de algum processo, reporta perda de deadline com o nome e instante

def executar(channel):
    syscall = 1 #flag do SO
    acc = 0 # acc ativo
    pc = 0 # pc ativo
    active = 0 # guarda o processo ativo, se 0 e o SO
    time = 0
    while len(pcbs) > 0:

        if syscall == 1:
            if acc == 0: # termina o programa
                print(f"Processo {pcbs[active].name} terminou, matando processo")
                pcbs.remove(pcbs[active])
                syscall = 0
                escalonar()
            elif acc == 1: # imprime o valor do acc
                print(f"Processo {pcbs[active].name} pediu para imprimir valor: {acc}")
                syscall = 0
            elif acc == 2: # le um valor inteiro e salva no acc
                acc = int(input(f"Processo {pcbs[active].name} pediu para ler um valor inteiro: "))
                syscall = 0


        else:
            pc =  pcbs[active].pc
            acc = pcbs[active].acc
            pcbs[active].state = "running"

            while active != 0:
                instr = pcbs[active].instructions[pc]

                # ARITMETICO ---------------------------------------
                if instr[0] == "ADD":
                    if instr[1].startswith("#"): #imediato
                        acc += int(instr[1][1:])
                    else: #variavel
                        acc += pcbs[active].data[instr[1]]
                elif instr[0] == "SUB":
                    if instr[1].startswith("#"):
                        acc -= int(instr[1][1:])
                    else:
                        acc -= pcbs[active].data[instr[1]]
                elif instr[0] == "MULT":
                    if instr[1].startswith("#"):
                        acc *= int(instr[1][1:])
                    else:
                        acc *= pcbs[active].data[instr[1]]
                elif instr[0] == "DIV":
                    if instr[1].startswith("#"):
                        acc /= int(instr[1][1:])
                    else:
                        acc /= pcbs[active].data[instr[1]]

                # MEMORIA ---------------------------------------
                elif instr[0] == "LOAD":
                    acc = pcbs[active].data[instr[1]]
                elif instr[0] == "STORE":
                    pcbs[active].data[instr[1]] = acc

                # SALTO -----------------------------------------
                elif instr[0] == "BRANY":
                    pcbs[active].pc = pcbs[active].data[instr[1]]
                elif instr[0] == "BRPOS":
                    if acc > 0:
                        pcbs[active].pc = pcbs[active].data[instr[1]]
                elif instr[0] == "BRZERO":
                    if acc == 0:
                        pcbs[active].pc = pcbs[active].data[instr[1]]
                
                # SISTEMA ---------------------------------------
                elif instr[0] == "SYSCALL":
                    # salva contexto e mando pro SO
                    pcbs[active].pc = pc
                    pcbs[active].acc = acc
                    pcbs[active].state = "ready"
                    acc = int(instr[1]) # acc recebe o pedido do processo
                    syscall = 1

                # checa a interrupcao TODO fiquei com pena de apagar
                #if not channel.empty():
                    # nova tarefa chegou, salva contexto e manda pro SO
                    #pcbs[active].pc = pc
                    #pcbs[active].acc = acc
                    #pcbs[active].state = "ready"
                    #acc = 3  # acc para escalonar
                    #syscall = 1

                for pcb in pcbs:
                    if pcb.state == "blocked":
                        pcb.block_time -= 1
                        if pcb.block_time <= 0:
                            pcb.state = "ready"
                    pcb.deadline -= 1
                    if pcb.deadline <= 0:
                        # deadline estourou, mata o processo
                        print(f"Processo {pcb.name} estourou deadline, matando processo")
                        pcbs.remove(pcb)

                pc += 1
                time += 1


# ESCALONADOR - implementa EDF
# ESCALONADOR (tempo_atual)

    # 1-> reordenar a fila de prontos
        # pega todos os processos ready
        # ordena pelo deadline absoluto (menor primeiro)

    # 2-> verificar se precisa preemptar
        # pega o processo que ta rodando atualmente (running)
        # se o deadline do primeiro da fila < processo rodando
            # salva contexto do atual
            # muda estado do primeiro da fila para running
        # se nao tiver ngn rodando
            # pega o primeiro da fila e muda pra running

    # 3-> a cada nova ativacao periodica do processo
        # quando o processo termina seu periodo (ci esgotado ou SYSCALL0)
            # recalcula deadline absoluto (new_deadline = tempo_atual + periodo)
            # reseta pc para 0
            # reseta acc para 0
            # muda estado para ready
            # reinsere na fila de prontos

    # 4-> verificar perda de deadline
        # para cada processo na fila
            # se tempo atual > deadline do processo
            # imprime que o processo X perdeu deadline no instante Y

"""def escalonar():"""

# INTERFACE - entrada e saida
# INTERFACE
    # meter no freestyle fodase

def interface(channel): # ta errado, tem que receber a cada coisada
    while True:
        prog = input("prog_name period ci:")
        channel.put(prog)



if __name__ == '__main__':
    channel = queue.Queue()

    interface = threading.Thread(target=interface, args=(channel,))
    interface.start()

    pcb = parser("prog2.txt", period=10, ci=5, arrival_time=0)

    print("=== INSTRUCOES ===")
    for i, instr in enumerate(pcb.instructions):
        print(f"{i}: {instr}")

    print("\n=== DATA ===")
    print(pcb.data)


