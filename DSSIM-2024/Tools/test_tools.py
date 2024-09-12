###  # -*- coding: UTF-8 -*-

def preenche_com_zero():
    return

def teste_cria_resposta_encodada(msg):
    resposta = msg.encode('utf-8')

    return resposta


def func100acknowledgment(funcao, flag):
    """ Funcao resposta para o MC às funções 03, 04, 05, 06, 07, 08, 09, 10 e 11. Se todos os dados
    foram recebidos e o DSSim conseguiu executar a sua respectiva função, retorna flag = 1
    se não, flag = 0."""
    msg_retornada = [chr(0)] * 5

    msg_retornada[0] = chr(100)
    msg_retornada[1] = chr(5) # Possui 5 BYTES!!!
    msg_retornada[2] = chr(0)
    msg_retornada[3] = chr(funcao)
    msg_retornada[4] = chr(flag)

    return msg_retornada