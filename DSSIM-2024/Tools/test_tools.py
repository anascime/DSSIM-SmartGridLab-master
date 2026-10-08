###  # -*- coding: UTF-8 -*-
import struct

def preenche_com_zero():
    return

def teste_cria_resposta_encodada(msg):
    resposta = msg.encode('utf-8')

    return resposta

def set_taps():

    r = input("Alterar valores dos taps do trafo? (s/n)\n--> ")

    return r

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

def getbarra(barra=None):# -> bytes | Any:
    if barra is None:
        barra = bytes(input('Digite a barra: '), 'utf-8')
    return barra

def trataBarra(barra: bytes):# -> bytes | Any:
    try:
        barra = barra.split(b'.')[0]
    except AttributeError:
        pass

    try:
        barra = int(barra)
        barra = struct.pack('<Q', barra)[0:4]
    except ValueError:
        raise ValueError("Valor inválido. A barra não é um número inteiro.")

    try:
        barra = struct.pack('<Q', barra)[0:4]
    except struct.error:
        raise ValueError("Valor inválido. A barra não é um número inteiro.")

    try:
        barra = barra.decode('latin-1')
    except AttributeError:
        pass

    return barra



def main():
    print('Testes de funções do DSSim')

    barra = getbarra()
    print('Barra digitada: ', barra)
    bTratada = trataBarra(barra)
    print('Barra tratada: ', bTratada)

    # print("1 - Teste de função 100 (acknowledgment)")
    # print("2 - Teste de função 101 (resposta para o MC)")
    # print("3 - Teste de função 102 (resposta para o MC)")
    # print("4 - Teste de função 103 (resposta para o MC)")
    # print("5 - Teste de função 104 (resposta para o MC)")
    # print("6 - Teste de função 105 (resposta para o MC)")
    # print("7 - Teste de função 106 (resposta para o MC)")
    # print("8 - Teste de função 107 (resposta para o MC)")
    # print("9 - Teste de função 108 (resposta para o MC)")
    # print("10 - Teste de função 109 (resposta para o MC)")
    # print("11 - Teste de função 110 (resposta para o MC)")

if __name__ == "__main__":
    main()