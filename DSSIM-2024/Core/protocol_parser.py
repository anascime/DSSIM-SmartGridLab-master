# -*- coding: UTF-8 -*-
import datetime
import logging
import math
import os
import threading
import time
import struct
import sys
from typing import List
import pandas as pd
from numpy import true_divide
from concurrent.futures import ThreadPoolExecutor

#from network import identified_nodes
# import thread
# import Core.MC as coreMC
# import Core.DSSIM as DSSIMmas essixi
import App.Fontes.Auxiliar as aux
qls = aux.quebra_linha_simbolo
from Tools.test_tools import *
import Core.DSSIM as DSSIM
from Tools.error_messages import ErrorMessages
from Models.Transformer import Transformer
import logging
import logging.config
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config['logging'])

logger = logging.getLogger('server')
equipment_logger = logging.getLogger('server.parser')

EQUIPMENT_TYPE_LABELS = {
    "1": "barra",
    "2": "trecho",
    "3": "chave",
    "4": "transformador",
    "5": "regulador",
    "6": "capacitor_serie",
    "7": "capacitor",
    "8": "gerador",
    "9": "suprimento",
    "10": "carga",
    "11": "filtro",
    "12": "reator",
}


def equipamento_rotulo(tipo_equipamento):
    return EQUIPMENT_TYPE_LABELS.get(str(tipo_equipamento), f"tipo_{tipo_equipamento}")


def _pack_float_value(value: float) -> str:
    return struct.pack('<f', float(value))[0:4].decode('latin-1')


def _append_float_values(equipamento: list, values: list) -> None:
    for value in values:
        equipamento.append(_pack_float_value(value))

TCP_IP = '127.0.0.1'
TCP_PORT = 6345
BUFFER_SIZE_DSSIM = 8192  # Qual valor utilizar aqui?

dssim_obj = DSSIM.DSSim(TCP_IP, TCP_PORT, BUFFER_SIZE_DSSIM, None)    #> teste
dssim_obj.connect()
dssim_obj.armazena_path()
dssim_obj.armazena_nomes_elementos()


# Configurações globais (Constantes em MAIÚSCULO)
HOST = ''
PORT = 1024
BUFFER_SIZE = 1024
MAX_WORKERS = 50  # Limite máximo de clientes simultâneos
trafo_tap_alterado = [] # type: List[Transformer]  # Lista de objetos Transformer com estado persistido
tensoes_alteradas = {}  # Dicionário para armazenar as tensões alteradas por transformador

def process_data(msg):
    raise NotImplementedError("Função de processamento de dados ainda não implementada.")


def decodifica_mensagem(conn, data):
    raise NotImplementedError("Função de decodificação da mensagem ainda não implementada.")


def reconstroi_msg(data):
    raise NotImplementedError("Função de reconstrução da mensagem ainda não implementada.")
