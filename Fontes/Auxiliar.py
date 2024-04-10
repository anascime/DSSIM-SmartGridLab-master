###  # -*- coding: iso-8859-15 -*-

"""
Unidade com funções auxiliares.
"""

__author__ = 'CelsoRocha' and 'Paulo Radatz'
import struct


def escreve_lista(nome, lista):
    arquivo_saida = open(nome + ".txt", "w")
    for x in lista:
        arquivo_saida.write(str(x) + "\n")

    return 1


def escreve_lista_par(nome, lista):
    arquivo_saida = open(nome + ".txt", "w")
    i = 0
    while i < len(lista):
        arquivo_saida.write(str(lista[i]) + "\t" + str(lista[i+1]) + "\n")
        i = i + 2
    return 1


def monta_inteiro_from_bytes(string):
    """ Função que recebe uma string de bytes e retorna um inteiro correspondente."""
    if type(string) is list:
        string = "".join(string)  # concatena e converte para string
    if len(string) < 8:
        tamanho = len(string)
        while tamanho < 9:
            string = string + "\x00"
            tamanho = len(string) + 1

    return struct.unpack('<Q', string)[0]


def monta_byte_to_signed_int(string):
    if 0 <= int(string) <= 127:
        return int(string)
    else:
        return int(string) - 256


def monta_float_from_bytes(string):
    """ Função que recebe uma string de bytes e retorna um ponto flutuante correspondente"""
    if len(string) < 4:
        tamanho = len(string)
        while tamanho < 5:
            string = string + "\x00"
            tamanho = len(string) + 1
    return struct.unpack('<f', string)[0]

class Conexao:
    DSSIM_CON, MC_CON = range(2)


class Tipo_Conexao:
    ENV, REC = range(2)