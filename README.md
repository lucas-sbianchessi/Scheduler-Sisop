# Scheaduler EDF

Quando roda o program (python3 main.py) a interface grafica dele permite escolhar um ou mais programas para rodar e cada um deles pode se escolher arrival(tempo em que o programa sera carregado), ci(tempo de execução do programa) e periodo(de quanto em quanto tempo deve se repetir o programa), que cada ciclo é uma intrução e uma unidade de tempo.

A parte abaixo é para servir sumario do programa apresentado na main.py

# PROCESS CONTROL BLOCK
  contem informacoees que cada processo necessita


# PARSER - separar code de data - carrega e inicializa programas

  prapara o programa para a execucao separando data das intrucoes e inicializa o pcb dos programas

# EXECUCAO
simula o processador e sistema operacional

## 1-> ==== ATUALIZA BLOQUEADOS
diminui o tempo restante de bloquedo dos processos e verifica se podem sair do estado de bloqueado

## 2-> ==== VERIFICA ARRIVAL TIME
verifica se tem que carregar um processo de acordo com o arrival time estabelecido

## 3-> ==== TRATA SYSCALL
como definido no trabalho(0 acaba o processo, 1 imprime acc, 2 le um valor)

## 4-> ==== CHAMA ESCALONADOR
roda o escalonador EDF e atualiza o processo ativo(active)

## 5-> ==== EXECUTA INSTRUCOES
simula o processamento de uma unica instrucao, dado o pc

## 6-> ==== VERIFICA CI E REAGENDA
soma uma ao pc e diminui um do ci do processo ativo

## 7-> ==== VERIFICA DEADLINE
ve se algum dos processos em ready tem mais para executar do que deadline (ci > deadline), se sim bloqueia ate o proximo periodo e imprime

# ESCALONADOR - implementa EDF

# INTERFACE - entrada e saida / bloatware
