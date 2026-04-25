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
        self.instructions = instructions #lista de instrucoes parseadas de .code
        self.data = data #dic. de vars dda memoria do processo
        self.pc = 0 #idx da proxima instrucao a executar
        self.acc = 0 #valor atual do acumulador

        #ESCALONAMENTO -> o que o EDF vai usar para tomar decisoes
        self.state ="ready" #estado do processo -> running/ready/blocked
        self.period = period #periodo da tarefa -> intervalo entre ativacoes
        self.ci = ci #tempo de computacao maxima
        self.arrival_time = arrival_time #instate que tarefa chega ao sistema
        self.deadline = arrival_time + period #deadline absoluto
        self.block_time = 0 #contador regressivo -> usar no SYSCALL


# PARSER - separar code de data - carrega e inicializa programas
def parser(file_name, period, ci, arrival_time):
    instructions = [] #lista de instrucoes
    data = {} #vars do processo
    labels = {} #para onde labels apontam (loop -> idx3)
    mode = None #secao atual do arquivo

    # 1 -> separar modes, add labels e data
    # le o arquivo linha  linha separando codigo de dado, tira comentarios
    lines_code_raw = [] #guarda linhas raw antes de resolver labels
    with open(file_name, "r") as f:
        for line in f:
            # remove comentarios e linhas vazias
            line = line.split("#")[0].strip()
            if not line: continue

            # mode define qual secao o parser ta agr
            if line == ".code": mode = "code"
            elif line == ".endcode": mode = None
            elif line == ".data": mode = "data"
            elif line == ".enddata": mode = None
            #guarda linha de codigo
            elif mode == "code": lines_code_raw.append(line)

            # tudo que cai em data vira entrada no dic.
            # memoria privada, prog1 nao conflita com prog2
            # data prog1 fica -> {"a": 10}
            # data prog2 fica -> {"a": 0, "b": 1, "controle": 0, "aux": 0}
            elif mode == "data":
                part = line.split()
                data[part[0]] = int(part[1])


    # 2 -> mapear labels para os indices
    # percorre codigo identificando labels e registrando a que indx aponta
    # instrucoes de salto vao referenciar essas labels pelo nome
    # prog2 deve ficar -> {"loop": 0, "fim": 6}
    idx =0
    no_label_lines = [] #linhas sem labels
    for line in lines_code_raw:
        #percorre linhas do code procurando por qql coisa com :
        # quando acha add no dic. labels em qual idx. o label aponta
        if ":" in line:
            part = line.split(":")
            labels[part[0].strip()] = idx #registra indx da label
            rest = part[1].strip()
            if not rest: continue  #label sozinha, sem mais instrucoes
            line = rest  #continua com a instrucao que tava depois do :
        no_label_lines.append(line) # labels somem da lista de instrucoes, so existem no dic. labels
        idx += 1

    # 3 -> monta lista final trocando os nomes de label por indx
    # deixa pronto para o executor rodar sem ter que fazer mta coisa
    jumps = {"BRANY", "BRPOS", "BRZERO", "BRNEG"}
    for line in no_label_lines:
        part = line.split()
        opcode = part[0].upper()
        if opcode in jumps:
            part[1] = labels[part[1]] #BRANY loop vira [BRANY, 0]
        instructions.append(part)
        #cada instrucao deve ficar como uma lista ["LOAD", "a"], ["SUB", "#1"], ["BRZERO", 6]

    return PCB(file_name, instructions, data, period, ci, arrival_time)



# EXECUCAO - Execucao em geral do trabalho
def executar():
    acc = 0
    pc = 0
    active = 0 # TODO rename, qual pcbs[active] esta rodando
    while len(pcbs) > 0:

        if active == -1: # roda so em 0 (conferir teoria)
            # antes 0 termina 1 printa e 2 le
            # TODO roda a logica do escalonamento

        else:
            # carrega instrucao
            with open(Progs[active], "r") as f:
                instructions = f.readlines()

            # TODO cipa abaixo joga em uma funcao
            while active != -1: #tem jeito melhor
                instr = instructions[pcbs[active].pc].split() # TODO n sei como ele ta splitando as ,
                if instr[0] == "ADD":
                    acc += int(instr[1])
                elif instr[0] == "SUB":
                    acc -= int(instr[1])
                elif instr[0] == "MULT":
                    acc *= int(instr[1])
                elif instr[0] == "DIV":
                    acc /= int(instr[1])
                elif instr[0] == "LOAD":
                    acc = int(instr[1])
                elif instr[0] == "STORE":
                    # TODO fazer um hash e inicializar um hash de dados no pcb
                    # TODO -------------------------------------------------
                    # ta tudo errado pq ele tem q pegar no hash de dados o lugar
                elif instr[0] == "BRANY":
                    pcbs[active].pc = int(instr[1])
                elif instr[0] == "BRPOS":
                    if acc > 0:
                        pcbs[active].pc = int(instr[1])
                elif instr[0] == "BRZERO":
                    if acc == 0:
                        pcbs[active].pc = int(instr[1])
                elif instr[0] == "SYSCALL":
                    active = -1
                # da pra sonhar em meter um negocinho mais bonito


# GERENCIAMENTO - gerenciador de processos

# ESCALONADOR - implementa EDF

# INTERFACE - entrada e saida



if __name__ == '__main__':

    carregarProgs()
    executar()


