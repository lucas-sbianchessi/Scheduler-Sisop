Progs = ["prog1.txt"]
pcbs = []
validInstrs = ["ADD", "SUB", "MULT", "DIV", "LOAD", "STORE", "BRANY", "BRPOS", "BRZERO", "SYSCALL"] #pra veificacao no carregarProgs

class PCB:
    def __init__(self, count, hash):
        self.count = count
        self.pc = 0
        self.data = hash


# Carrega e inicializa programas
def carregarProgs():
    for prog in Progs:
        with open(prog, "r") as f:
            for linha in f:
                count += 1
        pcbs.append(PCB(count))

# Execucao em geral do trabalho 
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




if __name__ == '__main__':

    carregarProgs()
    executar()


