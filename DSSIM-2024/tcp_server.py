# -*- coding: UTF-8 -*-
import datetime
import logging
import os
import time
import socket
from concurrent.futures import ThreadPoolExecutor

import App.Fontes.Auxiliar as aux
qls = aux.quebra_linha_simbolo
from Tools.test_tools import *
import Core.protocol_parser as parser
from Tools.error_messages import ErrorMessages
import logging
import logging.config
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config['logging'])

logger = logging.getLogger('server')
equipment_logger = logging.getLogger('server.handler')


# Configurações globais (Constantes em MAIÚSCULO)
HOST = ''
PORT = 1024
BUFFER_SIZE = 1024
MAX_WORKERS = 50  # Limite máximo de clientes simultâneos

def handle_client(client_socket: socket.socket, client_address: tuple) -> None:
    """Gerencia a comunicação com um cliente específico."""
    logging.info(f"Conexão estabelecida com {client_address}")
    global mudou_tap
    mudou_tap = False
    print('mudou_tap: ', mudou_tap)
    # O 'with' garante o fechamento do socket do cliente ao terminar
    with client_socket:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    logging.info(f"Cliente {client_address} desconectou voluntariamente.")
                    break

                rcvd_data = data.decode('latin-1')
                parser.decodifica_mensagem(client_socket, rcvd_data)

            except ConnectionAbortedError:
                logging.warning(f"Conexão abortada pelo cliente {client_address}.")
                break
            except Exception as e:
                logging.error(f"Erro inesperado no cliente {client_address}: {e}")
                break

def start_server() -> None:
    """Inicializa e roda o servidor TCP."""
    # O 'with' principal garante que a porta será liberada se o servidor cair
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            logging.info(f"Servidor rodando e aguardando conexões na porta {PORT}...")

            # Gerenciador de fila de threads (Pool)
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                while True:
                    client_socket, client_address = server_socket.accept()
                    # Passa o cliente para o pool processar assim que houver vaga
                    executor.submit(handle_client, client_socket, client_address)

        except KeyboardInterrupt:
            logging.info("Servidor interrompido via teclado (Ctrl+C). Desligando...")
        except Exception as e:
            logging.critical(f"Erro crítico no loop do servidor: {e}")

if __name__ == '__main__':
    start_server()