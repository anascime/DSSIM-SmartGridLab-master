###  # -*- coding: UTF-8 -*-

"""
Unidade com funções auxiliares.
"""

__author__ = 'CelsoRocha' and 'Paulo Radatz'
import struct
import pandas
import os

def quebra_linha_simbolo(simbolo, caractere_linha="═"):
    try:
        # Obtém a largura atual do terminal
        largura = os.get_terminal_size().columns
    except OSError:
        largura = 80 # Fallback padrão

    # Garante espaço para o símbolo com espaçamento
    centro = f"  {simbolo}  "
    l_char = caractere_linha
    # Calcula o tamanho de cada lado da linha
    # Se a linha contiver espaço (como a de pontos), o cálculo muda ligeiramente
    vagas_lado = (largura - len(centro)) // 2

    if len(l_char) > 1: # Caso do "· "
        repeticoes = vagas_lado // len(l_char)
        lado = (l_char * repeticoes).strip()
    else:
        lado = l_char * vagas_lado

    linha = f"{lado}{centro}{lado}"
    print(linha.center(largura))

    # # Ajusta em 1 caractere se a largura for ímpar
    # if len(linha) < largura:
    #     linha += caractere_linha

    # print(linha)

# Exemplos de uso:
# quebra_linha_simbolo("❖", "═")
# quebra_linha_simbolo("✦", "─")
# quebra_linha_simbolo("⭐", "=")
# quebra_linha_simbolo("⭐", "〰")
# quebra_linha_simbolo("SUCCESS", "━")


def cria_csv_id(df, path):
    """ Cria csv dos equipamentos e seus ids
    """

    df.to_csv(path + "/UUIDS_final.csv")
    print("Arquivo UUIDS_final.csv criado com sucesso!")

def escreve_lista(nome, lista):
    with open(nome + ".txt", "w") as f:
        for x in lista:
            f.write(str(x) + "\n")
    return 1


def escreve_lista_par(nome, lista):
    with open(nome + ".csv", "w") as f:
        i = 0
        while i < len(lista):
            f.write(str(lista[i]) + ";" + str(lista[i+1]) + "\n")
            i = i + 2
    return 1


def monta_byte_to_signed_int(string):
    if 0 <= int(string) <= 127:
        return int(string)
    else:
        return int(string) - 256


# ──────────────────────────────────────────────────────────────────────────────
# ─── Funções Interpretes De Bytes ─────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def monta_inteiro_from_bytes(string):
    """ Função que recebe uma string de bytes e retorna um inteiro correspondente."""
    if type(string) is list:
        string = "".join(string)  # concatena e converte para string
    if len(string) < 8:
        tamanho = len(string)
        while tamanho < 9:
            string = string + "\x00"
            tamanho = len(string) + 1
    # stringb = string.encode('latin-1')
    stringb = string.encode('latin')
    # stringb = string.encode()
    # tx = b'\x00\x12\x04\x00\x00\x00\x00\x00'
    return struct.unpack('<Q', stringb)[0]


def monta_float_from_bytes(string):
    """Função que recebe uma string de bytes e retorna um ponto flutuante correspondente"""
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