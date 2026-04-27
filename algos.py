# EXCLUIR DEPOIS, ARQUIVO NOVO SO PQ FIQUEI UM COMMIT ATRAS E SOU VAGABA


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

# ============================= ; ===========================

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

# ============================= ; ===========================

# INTERFACE
    # meter no freestyle fodase

