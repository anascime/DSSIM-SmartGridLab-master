# -*- coding: UTF-8 -*-
import datetime
import logging
import math
import os
import threading
import time
import socket
import struct
import sys
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
import logging
import logging.config
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config['logging'])

logger = logging.getLogger('server')
equipment_logger = logging.getLogger('server.equipment')

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

def process_data(msg):
        """Processa mensagens entre MC e DSSim e retorna string

        Método responsável por processar a mensagem recebida pelo cliente MC,
        chamando a respectiva função na comunicação com o servidor DSSim e
        enviando a devida mensagem de volta ao cliente MC
        """

        # tamanho = len(data)
        # funcao = ord(data[0])
        # O comprimento de "data" é exatamente o comprimento da mensagem. No print(data,)
        # parece que a mensagem é bem menor, mas isso é porque vários "chars" enviados
        # pelo C++ são nulos, o que vira um char "", que na hora do print, não aparece.

        logger.debug("mensagem bruta MC: %s", msg)
        message = reconstroi_msg(msg)
        # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.REC, message + "\n\n")
        logger.info("mensagem MC: %s", message)

        msg_dividida = message.split(";")
        funcao = msg_dividida[0]
        logger.debug("função=%s", funcao)

        # dssim_obj = 2    #> dssim_obj=None para teste
        #! verificar se esses "is not", funcionam e/ou fazem sentido
        if dssim_obj is not None:  # Verifica se existe conexão com o DSSim
            if funcao == "99":  # Retorna ID do equipamento por meio de código
                codigo_equipamento = msg_dividida[-2]
                tipo_equipamento = msg_dividida[-3]
                logger.debug("func=99 tipo=%s codigo=%s", tipo_equipamento, codigo_equipamento)

                id_equipamento = dssim_obj.retorna_id(codigo_equipamento, tipo_equipamento)  # int
                logger.info("func=99 id=%s tipo=%s codigo=%s", id_equipamento, tipo_equipamento, codigo_equipamento)

                qtde_bytes = 43   # Usando o mesmo valor definido no C++ builder quando a função 99 é enviada para o Simulador.
                msg_retornada = [chr(0)]*qtde_bytes
                now = datetime.datetime.now()

                msg_retornada[0] = chr(int(funcao))
                msg_retornada[1] = chr(qtde_bytes)
                msg_retornada[2] = chr(0)
                msg_retornada[3] = chr(now.hour)  # verificar se a hora do sistema atual ou a hora recebida na mensagem
                msg_retornada[4] = chr(now.minute)
                msg_retornada[5] = chr(now.second)
                msg_retornada[6] = chr(int(tipo_equipamento))
                # print('msg_retornada: ', msg_retornada)

                # Id do equipamento Convertendo o valor do ID para 4 bytes segundo o formato Little Endian
                msg_retornada[7] = chr(struct.pack('<Q', id_equipamento)[0])
                msg_retornada[8] = chr(struct.pack('<Q', id_equipamento)[1])
                msg_retornada[9] = chr(struct.pack('<Q', id_equipamento)[2])
                msg_retornada[10] = chr(struct.pack('<Q', id_equipamento)[3])

                # Código do Equipamento
                for i in range(11, 11 + len(codigo_equipamento)):
                    msg_retornada[i] = codigo_equipamento[i-11]

                # Mensagem Display
                msg = funcao + ";" + str(qtde_bytes) + ";" + str(now.hour) + ";" + str(now.minute) + ";" + str(now.second) + ";" + tipo_equipamento + ";" + str(id_equipamento) + ";" + codigo_equipamento + ";"
                # print('msg: ', msg)
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                str_retorno = "".join(str(x) for x in msg_retornada)
                logger.debug("func=99 qt_bytes=%s id=%s", qtde_bytes, id_equipamento)

                # return "".join(str(x) for x in msg_retornada)
                return str_retorno

            elif funcao == "1":  # MC solicita registros de equipamentos. Devemos retornar a função 02 do protocolo.

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                if dssim_obj.check_sim_needed(hora, minuto, segundo):
                    # Simula
                    dssim_obj.solve_time(hora, minuto, segundo)

                #! Teste de pegar tensões
                # fnames = "out/names_nodes"
                # os.makedirs(os.path.dirname(fnames), exist_ok=True)
                c = dssim_obj.get_all_name_nodes()
                # aux.escreve_lista(fnames, c)

                # arquivo = "out/voltages_pu"
                # os.makedirs(os.path.dirname(arquivo), exist_ok=True)
                b = dssim_obj.get_all_nodes_voltages('pu')
                # aux.escreve_lista(arquivo, b)
                data = pd.DataFrame({'Bus': c, 'Voltage': b})
                data[['Bus', 'Node']] = data['Bus'].str.split('.', expand=True)
                data.insert(0, 'Number', 0)
                data = data[['Number', 'Bus', 'Node', 'Voltage']]
                #TODO 1 arquivo por timestamp de todas as barras
                data.to_csv("out/nodes_voltages_pu.csv", index=False)

                #todo 1 arq por simulação - barras monitoradas: timestamp; barra; nó; tensao_pu;
                # b = dssim_obj.get_all_nodes_voltages('pu')
                # aux.escreve_lista_par(arquivo2, b)

                count = 0
                lista_equipamentos = []  # lista de tuplas
                for i in range(len(msg_dividida)-1):  # -1 porque tem um espaço a mais que vem por causa do split(";")
                    if i == (5 + count*2):
                        tipo_equipamento = msg_dividida[i]
                        id_equipamento = msg_dividida[i+1]

                        logger.debug(
                            "func=1 request hora=%s:%s:%s equipamento=%s id=%s",
                            hora,
                            minuto,
                            segundo,
                            equipamento_rotulo(tipo_equipamento),
                            id_equipamento,
                        )

                        count = count + 1
                        lista_equipamentos.append((tipo_equipamento, id_equipamento))

                # Retornar a função 02:
                    # Trata-se de uma resposta para a função 1, na qual são enviados todos os registros pertinentes aos
                    # equipamentos solicitados, na ordem de solicitação e referidos ao horário definido na solicitação.
                    # Cada informação de grandeza é dada por 8 bytes, sendo 4 bytes para o módulo e 4 bytes para a fase (em graus).

                    # Os registros de grandezas enviados pela função 2 estão relacionados à simulação corrente do Sinap, ou seja,
                    # fluxo de carga ou curto-circuito.

                dic_tipo_registros = {"1": 32, "2": 32, "3": 136, "4": 129, "5": 129, "6": 48, "7": 37, "8": 66, "9": 72, "10": 72, "12": 68}

                # OBS: Registro do equipamento tipo Chave: Não estamos considerando, os 4 bytes de "Id da Barra de Referência" porque
                # o Módulo Central que eu estou utilizando não recebe ele. Nem sabemos que parâmetro é esse também (Por isso 132)
                # ATUALIZAÇÃO 24/04/2018: A versão "ModuloCentralXE7_Rev2_Sinap20170725" do Módulo Central espera na leitura da função
                # 2 esses 4 bytes. Vamos assumir como sendo a barra 1 da chave (Agora, 136 bytes)

                qtde_bytes = 7  # Começa sempre com 7 bytes fixos.
                for i in range(len(lista_equipamentos)):
                    qtde_bytes = qtde_bytes + 5 + dic_tipo_registros[lista_equipamentos[i][0]]

                # msg_retornada = [chr(0)] * qtde_bytes
                msg_retornada = [chr(0)] * 7  # 7 primeiros bytes, depois vamos concatenar
                # msg_retornada = []  # resolver problema aqui, na hora de montar a msg
                msg_retornada[0] = chr(2)
                msg_retornada[1] = chr(struct.pack('<Q', qtde_bytes)[0])
                msg_retornada[2] = chr(struct.pack('<Q', qtde_bytes)[1])
                msg_retornada[3] = chr(int(hora))
                msg_retornada[4] = chr(int(minuto))
                msg_retornada[5] = chr(int(segundo))

                tipo_calculo = dssim_obj.get_last_simulation_type()
                if tipo_calculo == "Fluxo":
                    msg_retornada[6] = chr(0)  # Fluxo. O que mandar aqui exatamente? # mandar o último tipo de simulação enviado pelo dssim.
                else:  # "Curto"
                    msg_retornada[6] = chr(1)

                lista_equipamentos_todos = []

                for i in range(len(lista_equipamentos)):
                    tipo_equipamento = lista_equipamentos[i][0]
                    id_equipamento = lista_equipamentos[i][1]

                    equipamento = []

                    # if i == 1:
                    #     logger.debug("processando tamanho do lote equipamento (batch size)=%s", len(lista_equipamentos))

                    equipamento.append(chr(int(tipo_equipamento)))  # Tipo
                    id_equip_bytes = struct.pack('<Q', int(id_equipamento))[0:4]  # Id
                    equipamento.append(id_equip_bytes.decode("latin-1"))

                    if tipo_equipamento == "1":  # Barra
                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento, "barra")
                        voltages = dssim_obj.get_bus_voltages(nome_opendss)  # salva array com registros
                        logger.debug("func=1 barra id=%s nome=%s tensões=%s", id_equipamento, nome_opendss, voltages)

                        va = voltages[0]
                        va_angle = voltages[1]
                        vb = voltages[2]
                        vb_angle = voltages[3]
                        vc = voltages[4]
                        vc_angle = voltages[5]
                        vn = voltages[6]
                        vn_angle = voltages[7]

                        equipamento.append(struct.pack('<f', va)[0:4])        # Módulo Fase A
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # Ângulo Fase
                        equipamento.append(struct.pack('<f', vb)[0:4])        # Módulo Fase B
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # Ângulo Fase B
                        equipamento.append(struct.pack('<f', vc)[0:4])        # Módulo Fase C
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # Ângulo Fase C
                        equipamento.append(struct.pack('<f', vn)[0:4])        # Módulo Neutro
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # Ângulo Neutro

                    elif tipo_equipamento == "2":  # Trecho

                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        currents = dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros
                        logger.debug("func=1 trecho id=%s nome=%s correntes=%s", id_equipamento, nome_opendss, currents)

                        ia = currents[0]
                        ia_angle = currents[1]
                        ib = currents[2]
                        ib_angle = currents[3]
                        ic = currents[4]
                        ic_angle = currents[5]
                        in_ = currents[6]  # in_
                        in_angle = currents[7]

                        equipamento.append(struct.pack('<f', ia)[0:4])  # Módulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # Ângulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # Módulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # Ângulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # Módulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # Ângulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # Módulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # Ângulo Neutro

                    elif tipo_equipamento == "3":  # Chave

                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        # currents = dssim_obj.get_elem_currents(nome_opendss, 1)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros
                        voltages_1 = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        voltages_2 = dssim_obj.get_elem_voltages(nome_opendss, 2)  # salva array com registros
                        powers_total = dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros
                        power_phase_a = dssim_obj.get_phase_powers(nome_opendss, 1, 1)  #* Cuidado aqui, precisamos verificar as fases disponíveis antes...
                        power_phase_b = dssim_obj.get_phase_powers(nome_opendss, 1, 2)
                        power_phase_c = dssim_obj.get_phase_powers(nome_opendss, 1, 3)
                        logger.debug(
                            "func=1 chave id=%s nome=%s correntes=%s tensões_1=%s tensões_2=%s potência_total=%s potências_fases=%s/%s/%s",
                            id_equipamento,
                            nome_opendss,
                            currents,
                            voltages_1,
                            voltages_2,
                            powers_total,
                            power_phase_a,
                            power_phase_b,
                            power_phase_c,
                        )

                        va1 = struct.pack('<f', voltages_1[0])[0:4]
                        va1_angle = struct.pack('<f', voltages_1[1])[0:4]
                        vb1 = struct.pack('<f', voltages_1[2])[0:4]
                        vb1_angle = struct.pack('<f', voltages_1[3])[0:4]
                        vc1 = struct.pack('<f', voltages_1[4])[0:4]
                        vc1_angle = struct.pack('<f', voltages_1[5])[0:4]
                        vn1 = struct.pack('<f', voltages_1[6])[0:4]
                        vn1_angle = struct.pack('<f', voltages_1[7])[0:4]

                        equipamento.append(va1.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(va1_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(vb1.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(vb1_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc1.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(vc1_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn1.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(vn1_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        va2 = (struct.pack('<f', voltages_2[0])[0:4])
                        va2_angle = (struct.pack('<f', voltages_2[1])[0:4])
                        vb2 = (struct.pack('<f', voltages_2[2])[0:4])
                        vb2_angle = (struct.pack('<f', voltages_2[3])[0:4])
                        vc2 = (struct.pack('<f', voltages_2[4])[0:4])
                        vc2_angle = (struct.pack('<f', voltages_2[5])[0:4])
                        vn2 = (struct.pack('<f', voltages_2[6])[0:4])
                        vn2_angle = (struct.pack('<f', voltages_2[7])[0:4])

                        equipamento.append(va2.decode('latin-1'))  # Módulo Fase A - Terminal 2
                        equipamento.append(va2_angle.decode('latin-1'))  # Ângulo Fase - Terminal 2
                        equipamento.append(vb2.decode('latin-1'))  # Módulo Fase B - Terminal 2
                        equipamento.append(vb2_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 2
                        equipamento.append(vc2.decode('latin-1'))  # Módulo Fase C - Terminal 2
                        equipamento.append(vc2_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 2
                        equipamento.append(vn2.decode('latin-1'))  # Módulo Neutro - Terminal 2
                        equipamento.append(vn2_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 2

                        ia = currents[0]
                        ia_angle = currents[1]
                        ib = currents[2]
                        ib_angle = currents[3]
                        ic = currents[4]
                        ic_angle = currents[5]
                        in_ = currents[6]  # in_
                        in_angle = currents[7]

                        equipamento.append((struct.pack('<f', ia)[0:4]).decode('latin-1'))  # Módulo Fase A
                        equipamento.append((struct.pack('<f', ia_angle)[0:4]).decode('latin-1'))  # Ângulo Fase
                        equipamento.append((struct.pack('<f', ib)[0:4]).decode('latin-1'))  # Módulo Fase B
                        equipamento.append((struct.pack('<f', ib_angle)[0:4]).decode('latin-1'))  # Ângulo Fase B
                        equipamento.append((struct.pack('<f', ic)[0:4]).decode('latin-1'))  # Módulo Fase C
                        equipamento.append((struct.pack('<f', ic_angle)[0:4]).decode('latin-1'))  # Ângulo Fase C
                        equipamento.append((struct.pack('<f', in_)[0:4]).decode('latin-1'))  # Módulo Neutro
                        equipamento.append((struct.pack('<f', in_angle)[0:4]).decode('latin-1'))  # Ângulo Neutro

                        switch_state = chr(int(dssim_obj.get_switch_state(nome_opendss.split(".")[1])))   # switch state não tá funcionando para a última chave
                        equipamento.append(switch_state)
                        cbr = chr(int(0))
                        equipamento.append(cbr)
                        cbtl = chr(int(0))
                        equipamento.append(cbtl)
                        lockout = chr(int(dssim_obj.get_switch_lock(nome_opendss.split(".")[1]))) #! checaaaar
                        equipamento.append(lockout)

                        # Em qual terminal?
                        p_3f = float(0) # powers_total[0]/1000.0  # converter                       de kW para MW
                        q_3f = float(0) # powers_total[1]/1000.0
                        p_a = float(0) # power_phase_a[0]/1000.0
                        q_a = float(0) # power_phase_a[1]/1000.0
                        p_b = float(0) # power_phase_b[0]/1000.0
                        q_b = float(0) # power_phase_b[1]/1000.0
                        p_c = float(0) # power_phase_c[0]/1000.0
                        q_c = float(0) # power_phase_c[1]/1000.0

                        equipamento.append((struct.pack('<f', p_3f)[0:4]).decode())  # Módulo Fase A
                        equipamento.append((struct.pack('<f', q_3f)[0:4]).decode())  # Ângulo Fase
                        equipamento.append((struct.pack('<f', p_a)[0:4]).decode())  # Módulo Fase B
                        equipamento.append((struct.pack('<f', q_a)[0:4]).decode())  # Ângulo Fase B
                        equipamento.append((struct.pack('<f', p_b)[0:4]).decode())  # Módulo Fase C
                        equipamento.append((struct.pack('<f', q_b)[0:4]).decode())  # Ângulo Fase C
                        equipamento.append((struct.pack('<f', p_c)[0:4]).decode())  # Módulo Neutro
                        equipamento.append((struct.pack('<f', q_c)[0:4]).decode())  # Ângulo Neutro

                        #! Id da barra de referência (assumi como sendo a barra 1 da chave) Convertendo o valor do ID para 4 bytes segundo o formato Little Endian
                        swtobj = dssim_obj.send_dss_command("? " + nome_opendss + ".SwitchedObj")
                        # barra_ref_nome = dssim_obj.send_dss_command("? " + swtobj.decode() + ".bus1")

                        # id_barra_ref = int(barra_ref_nome.split(b"_id")[1].split(b".")[0])
                        id_barra_ref = int(dssim_obj.send_dss_command("? " + swtobj.decode() + ".bus1"))
                        id_barra_ref_Q = struct.pack('<Q', id_barra_ref)[0:4]

                        equipamento.append(id_barra_ref_Q.decode('latin-1'))
                        # equipamento.append(struct.pack('<Q', id_barra_ref)[0])
                        # equipamento.append(struct.pack('<Q', id_barra_ref)[1])
                        # equipamento.append(struct.pack('<Q', id_barra_ref)[2])
                        # equipamento.append(struct.pack('<Q', id_barra_ref)[3])

                    elif tipo_equipamento == "4" or tipo_equipamento == "5":  # Transformador ou Regulador de Tensão
                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        tipo_rotulo = equipamento_rotulo(tipo_equipamento)

                        if nome_opendss.split('.')[0].lower() != "transformer":
                            raise ValueError(f"\nid: {id_equipamento}\n\
                                             Equipamento {nome_opendss} não é um Transformer ou RegControl")

                        voltages_1 = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        voltages_2 = dssim_obj.get_elem_voltages(nome_opendss, 2)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros

                        try:
                            tap1, step1 = dssim_obj.get_transformer_tap(nome_opendss, 1)
                            tap2, step2 = dssim_obj.get_transformer_tap(nome_opendss, 2)
                            pass
                        except ValueError as e:
                            raise e

                        logger.info(f"{nome_opendss} - Va={voltages_1[0]} ∠{voltages_1[1]}, Vb={voltages_1[2]} ∠{voltages_1[3]}, Vc={voltages_1[4]} ∠{voltages_1[5]}, tap1 = {tap1}, step1 = {step1}, tap2 = {tap2}, step2 = {step2}")
                        logger.info(f"{nome_opendss} - Va={round(voltages_1[0] * math.sqrt(3), 2)} ∠{voltages_1[1]}, Vb={round(voltages_1[2] * math.sqrt(3), 2)} ∠{voltages_1[3]}, Vc={round(voltages_1[4] * math.sqrt(3), 2)} ∠{voltages_1[5]}")
                        equipment_logger.info(f"{nome_opendss} - Va = {voltages_1[0]} {voltages_1[1]}, Vb = {voltages_1[2]} {voltages_1[3]}, Vc = {voltages_1[4]} {voltages_1[5]}, tap1 = {tap1}, step1 = {step1}, tap2 = {tap2}, step2 = {step2}")
                        equipment_logger.info(f"{nome_opendss} - Va = {round(voltages_1[0] * math.sqrt(3), 2)}, Vb = {round(voltages_1[2] * math.sqrt(3), 2)} Vc = {round(voltages_1[4] * math.sqrt(3), 2)}")
                        # equipment_logger.debug(
                        #     "func=1 equipamento=%s id=%s nome=%s tap1=%s step1=%s tap2=%s step2=%s voltages_t1=%s voltages_t2=%s currents=%s",
                        #     tipo_rotulo,
                        #     id_equipamento,
                        #     nome_opendss,
                        #     tap1,
                        #     step1,
                        #     tap2,
                        #     step2,
                        #     voltages_1,
                        #     voltages_2,
                        #     currents,
                        # )

                        va1 = struct.pack('<f', voltages_1[0])[0:4]
                        va1_angle = struct.pack('<f', voltages_1[1])[0:4]
                        vb1 = struct.pack('<f', voltages_1[2])[0:4]
                        vb1_angle = struct.pack('<f', voltages_1[3])[0:4]
                        vc1 = struct.pack('<f', voltages_1[4])[0:4]
                        vc1_angle = struct.pack('<f', voltages_1[5])[0:4]
                        vn1 = struct.pack('<f', 0)[0:4]
                        vn1_angle = struct.pack('<f', 0)[0:4]
                        # vn1 = struct.pack('<f', voltages_1[6])[0:4]
                        # vn1_angle = struct.pack('<f', voltages_1[7])[0:4]

                        va2 = struct.pack('<f', voltages_2[0])[0:4]
                        va2_angle = struct.pack('<f', voltages_2[1])[0:4]
                        vb2 = struct.pack('<f', voltages_2[2])[0:4]
                        vb2_angle = struct.pack('<f', voltages_2[3])[0:4]
                        vc2 = struct.pack('<f', voltages_2[4])[0:4]
                        vc2_angle = struct.pack('<f', voltages_2[5])[0:4]
                        vn2 = struct.pack('<f', 0)[0:4]
                        vn2_angle = struct.pack('<f', 0)[0:4]
                        # vn2 = struct.pack('<f', voltages_2[6])[0:4]
                        # vn2_angle = struct.pack('<f', voltages_2[7])[0:4]

                        equipamento.append(va1.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(va1_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(vb1.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(vb1_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc1.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(vc1_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn1.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(vn1_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        equipamento.append(va2.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(va2_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(vb2.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(vb2_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc2.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(vc2_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn2.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(vn2_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        if len(currents) == 9:
                            ia1 = struct.pack('<f', currents[0])[0:4]
                            ia1_angle = struct.pack('<f', currents[1])[0:4]
                            ib1 = struct.pack('<f', 0)[0:4]
                            ib1_angle = struct.pack('<f', 0)[0:4]
                            ic1 = struct.pack('<f', 0)[0:4]
                            ic1_angle = struct.pack('<f', 0)[0:4]
                            in1_ = struct.pack('<f', 0)[0:4]
                            in1_angle = struct.pack('<f', 0)[0:4]
                            # in1_ = struct.pack('<f', currents[6])[0:4]
                            # in1_angle = struct.pack('<f', currents[7])[0:4]

                            ia2 = struct.pack('<f', currents[0])[0:4]
                            ia2_angle = struct.pack('<f', currents[1])[0:4]
                            ib2 = struct.pack('<f', 0)[0:4]
                            ib2_angle = struct.pack('<f', 0)[0:4]
                            ic2 = struct.pack('<f', 0)[0:4]
                            ic2_angle = struct.pack('<f', 0)[0:4]
                            in2_ = struct.pack('<f', 0)[0:4]
                            in2_angle = struct.pack('<f', 0)[0:4]
                        else:
                            ia1 = struct.pack('<f', currents[0])[0:4]
                            ia1_angle = struct.pack('<f', currents[1])[0:4]
                            ib1 = struct.pack('<f', currents[2])[0:4]
                            ib1_angle = struct.pack('<f', currents[3])[0:4]
                            ic1 = struct.pack('<f', currents[4])[0:4]
                            ic1_angle = struct.pack('<f', currents[5])[0:4]
                            in1_ = struct.pack('<f', 0)[0:4]
                            in1_angle = struct.pack('<f', 0)[0:4]
                            # in1_ = struct.pack('<f', currents[6])[0:4]
                            # in1_angle = struct.pack('<f', currents[7])[0:4]

                            ia2 = struct.pack('<f', currents[8])[0:4]
                            ia2_angle = struct.pack('<f', currents[9])[0:4]
                            ib2 = struct.pack('<f', currents[10])[0:4]
                            ib2_angle = struct.pack('<f', currents[11])[0:4]
                            ic2 = struct.pack('<f', currents[12])[0:4]
                            ic2_angle = struct.pack('<f', currents[13])[0:4]
                            in2_ = struct.pack('<f', 0)[0:4]
                            in2_angle = struct.pack('<f', 0)[0:4]
                            # in2_ = struct.pack('<f', currents[14])[0:4]
                            # in2_angle = struct.pack('<f', currents[15])[0:4]

                        equipamento.append(ia1.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(ia1_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(ib1.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(ib1_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(ic1.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(ic1_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(in1_.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(in1_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        equipamento.append(ia2.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(ia2_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(ib2.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(ib2_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(ic2.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(ic2_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(in2_.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(in2_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        # tap1, step1 = dssim_obj.get_transformer_tap(nome_opendss, 1)
                        # tap2, step2 = dssim_obj.get_transformer_tap(nome_opendss, 2)

                        if step2 != 0:
                            step = struct.pack('<h', step2)[0]
                        elif tap1 != 0:
                            step = struct.pack('<h', step1)[0]
                        else:
                            step = struct.pack('<h', 0)[0]

                        equipamento.append(chr(step))  # Passo do tap. Converter para signed int

                    elif tipo_equipamento == "6":  # Capacitor Série
                        form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda não implementado!" + "\n\n")
                        logger.warning("func=1 equip=capacitor_serie id=%s ainda nao implementado", id_equipamento)
                        return None

                    elif tipo_equipamento == "7":  # Capacitor

                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros

                        va = struct.pack('<f', voltages[0])[0:4]
                        va_angle = struct.pack('<f', voltages[1])[0:4]
                        vb = struct.pack('<f', voltages[2])[0:4]
                        vb_angle = struct.pack('<f', voltages[3])[0:4]
                        vc = struct.pack('<f', voltages[4])[0:4]
                        vc_angle = struct.pack('<f', voltages[5])[0:4]
                        vn = struct.pack('<f', 0)[0:4]
                        vn_angle = struct.pack('<f', 0)[0:4]
                        # vn = struct.pack('<f', voltages[6])[0:4]
                        # vn_angle = struct.pack('<f', voltages[7])[0:4]

                        equipamento.append(va.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(va_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(vb.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(vb_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(vc_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(vn_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        kvar_value = dssim_obj.get_capacitor_kvar(nome_opendss)
                        kvar = struct.pack('<f', kvar_value)[0:4]
                        equipamento.append(kvar.decode('latin-1'))  # Potência Reativa kvar


                        estado = dssim_obj.get_capacitor_state(nome_opendss)  # Estado do capacitor
                        equipment_logger.debug("func=1 equip=capacitor id=%s nome=%s tensões=%s kvar=%s estado=%s", id_equipamento, nome_opendss, voltages, kvar_value, estado)
                        equipamento.append(chr(estado))

                    elif tipo_equipamento == "8":  # Gerador
                        # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda não implementado!" + "\n\n")
                        logger.warning("func=1 equip=gerador id=%s ainda nao implementado", id_equipamento)
                        return None

                    elif tipo_equipamento == "9" or tipo_equipamento == "10":  # Suprimento ou Carga

                        if tipo_equipamento == "9":
                            nome_opendss = "Vsource.source"  # nome default do elemento circuito do OpenDSS
                        else:
                            nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)

                        voltages = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)
                        powers_total = dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros


                        # #! Emulador de carga 2.0 soma
                        # em_carga = True
                        # if em_carga:
                        #     for i, val in enumerate(voltages):
                        #         print('voltages[i]: ', voltages[i])
                        #         if i == 1:
                        #             voltages[i]=val+2.0
                        #         if i == 2:
                        #             voltages[i]=val+2.0
                        #         print('voltages[i]: ', voltages[i])

                        va = struct.pack('<f', voltages[0])[0:4]
                        va_angle = struct.pack('<f', voltages[1])[0:4]
                        vb = struct.pack('<f', voltages[2])[0:4]
                        vb_angle = struct.pack('<f', voltages[3])[0:4]
                        vc = struct.pack('<f', voltages[4])[0:4]
                        vc_angle = struct.pack('<f', voltages[5])[0:4]
                        vn = struct.pack('<f', 0)[0:4]
                        vn_angle = struct.pack('<f', 0)[0:4]
                        # vn = struct.pack('<f', voltages[6])[0:4]
                        # vn_angle = struct.pack('<f', voltages[7])[0:4]

                        equipamento.append(va.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(va_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(vb.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(vb_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(vc_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(vn_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        ia = struct.pack('<f', currents[0])[0:4]
                        ib = struct.pack('<f', currents[2])[0:4]
                        ic = struct.pack('<f', currents[4])[0:4]
                        # ia = currents[0]
                        # ib = currents[2]
                        # ic = currents[4]

                        if tipo_equipamento == "9":  # Suprimento
                            if 0 <= currents[1] <= 180:  # deixar sempre entre 0 e 180
                                ia_angle = struct.pack('<f', currents[1] - 180)[0:4]
                                # ia_angle = currents[1] - 180
                            else:
                                ia_angle = struct.pack('<f', currents[1] + 180)[0:4]
                                # ia_angle = currents[1] + 180
                            if 0 <= currents[3] <= 180:  # deixar sempre entre 0 e 180
                                ib_angle = struct.pack('<f', currents[3] - 180)[0:4]
                                # ib_angle = currents[3] - 180
                            else:
                                ib_angle = struct.pack('<f', currents[3] + 180)[0:4]
                                # ib_angle = currents[3] + 180
                            if 0 <= currents[5] <= 180:  # deixar sempre entre 0 e 180
                                ic_angle = struct.pack('<f', currents[5] - 180)[0:4]
                                # ic_angle = currents[5] - 180
                            else:
                                ic_angle = struct.pack('<f', currents[5] + 180)[0:4]
                                # ic_angle = currents[5] + 180

                        else:  # Carga
                            ia_angle = struct.pack('<f', currents[1])[0:4]
                            ib_angle = struct.pack('<f', currents[3])[0:4]
                            ic_angle = struct.pack('<f', currents[5])[0:4]
                            # ia_angle = currents[1]
                            # ib_angle = currents[3]
                            # ic_angle = currents[5]

                        in_ = struct.pack('<f', 0)[0:4]
                        in_angle = struct.pack('<f', 0)[0:4]
                        # in_ = struct.pack('<f', currents[6])[0:4]
                        # in_angle = struct.pack('<f', currents[7])[0:4]
                        # in_ = 0
                        # in_angle = 0

                        equipamento.append(ia.decode('latin-1'))  # Módulo Fase A
                        equipamento.append(ia_angle.decode('latin-1'))  # Ângulo Fase
                        equipamento.append(ib.decode('latin-1'))  # Módulo Fase B
                        equipamento.append(ib_angle.decode('latin-1'))  # Ângulo Fase B
                        equipamento.append(ic.decode('latin-1'))  # Módulo Fase C
                        equipamento.append(ic_angle.decode('latin-1'))  # Ângulo Fase C
                        equipamento.append(in_.decode('latin-1'))  # Módulo Neutro
                        equipamento.append(in_angle.decode('latin-1'))  # Ângulo Neutro

                        # equipamento.append(struct.pack('<f', ia)[0:4])  # Módulo Fase A
                        # equipamento.append(struct.pack('<f', ia_angle)[0:4])  # Ângulo Fase
                        # equipamento.append(struct.pack('<f', ib)[0:4])  # Módulo Fase B
                        # equipamento.append(struct.pack('<f', ib_angle)[0:4])  # Ângulo Fase B
                        # equipamento.append(struct.pack('<f', ic)[0:4])  # Módulo Fase C
                        # equipamento.append(struct.pack('<f', ic_angle)[0:4])  # Ângulo Fase C
                        # equipamento.append(struct.pack('<f', in_)[0:4])  # Módulo Neutro
                        # equipamento.append(struct.pack('<f', in_angle)[0:4])  # Ângulo Neutro

                        if tipo_equipamento == "9":  # Suprimento
                            p_3f = powers_total[0] * -1/1000.0
                            q_3f = powers_total[1] * -1/1000.0
                        else:  # Carga
                            p_3f = powers_total[0]/1000.0
                            q_3f = powers_total[1]/1000.0

                        equipment_logger.debug(
                            "func=1 equip=%s id=%s nome=%s tensoes=%s correntes=%s p_q=(%s, %s)",
                            equipamento_rotulo(tipo_equipamento),
                            id_equipamento,
                            nome_opendss,
                            voltages,
                            currents,
                            p_3f,
                            q_3f,
                        )

                        equipamento.append((struct.pack('<f', p_3f)[0:4]).decode('latin-1'))  # Potência Ativa Trifásica, sentido saindo do suprimento
                        equipamento.append((struct.pack('<f', q_3f)[0:4]).decode('latin-1'))  # Potência Reativa Trifásica, sentido saindo do suprimento
                        # equipamento.append(struct.pack('<f', p_3f)[0:4])  # Potência Ativa Trifásica, sentido saindo do suprimento
                        # equipamento.append(struct.pack('<f', q_3f)[0:4])  # Potência Reativa Trifásica, sentido saindo do suprimento

                    elif tipo_equipamento == "11":  # Filtro
                        form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda não implementado!" + "\n\n")
                        logger.warning("func=1 equip=filtro id=%s ainda nao implementado", id_equipamento)
                        return None
                    elif tipo_equipamento == "12":  # Reator

                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)
                        powers_total = dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros

                        va = struct.pack('<f', voltages[0])[0:4]
                        va_angle = struct.pack('<f', voltages[1])[0:4]
                        vb = struct.pack('<f', voltages[2])[0:4]
                        vb_angle = struct.pack('<f', voltages[3])[0:4]
                        vc = struct.pack('<f', voltages[4])[0:4]
                        vc_angle = struct.pack('<f', voltages[5])[0:4]
                        vn = struct.pack('<f', 0)[0:4]
                        vn_angle = struct.pack('<f', 0)[0:4]
                        # vn = struct.pack('<f', voltages[6])[0:4]
                        # vn_angle = struct.pack('<f', voltages[7])[0:4]

                        equipamento.append(va.decode('latin-1'))  # Módulo Fase A - Terminal 1
                        equipamento.append(va_angle.decode('latin-1'))  # Ângulo Fase - Terminal 1
                        equipamento.append(vb.decode('latin-1'))  # Módulo Fase B - Terminal 1
                        equipamento.append(vb_angle.decode('latin-1'))  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc.decode('latin-1'))  # Módulo Fase C - Terminal 1
                        equipamento.append(vc_angle.decode('latin-1'))  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn.decode('latin-1'))  # Módulo Neutro - Terminal 1
                        equipamento.append(vn_angle.decode('latin-1'))  # Ângulo Neutro - Terminal 1

                        ia = currents[0]
                        ia_angle = currents[1]
                        ib = currents[2]
                        ib_angle = currents[3]
                        ic = currents[4]
                        ic_angle = currents[5]
                        # in1_ = currents[6]  # in_
                        # in1_angle = currents[7]
                        in_ = 0
                        in_angle = 0

                        equipamento.append(struct.pack('<f', ia)[0:4])  # Módulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # Ângulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # Módulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # Ângulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # Módulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # Ângulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # Módulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # Ângulo Neutro

                        q_3f = powers_total[1]/1000.0

                        equipamento.append(struct.pack('<f', q_3f)[0:4])  # Potência Reativa Trifásica, sentido saindo do suprimento
                        logger.debug(
                            "func=1 equip=reator id=%s nome=%s tensoes=%s correntes=%s q_3f=%s",
                            id_equipamento,
                            nome_opendss,
                            voltages,
                            currents,
                            q_3f,
                        )

                    else:
                        # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro não identificado. Tipo de Equipamento " + tipo_equipamento + " não identificado!" + "\n\n")
                        return None

                    lista_equipamentos_todos = lista_equipamentos_todos + equipamento  # Concatena lista

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(qtde_bytes) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";" + str(ord(msg_retornada[5])) + ";" + tipo_calculo + ";"   # Não mostraremos os registros dos equipamentos pq a msg pode
                # ser muito extensa
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                msg_retornada = msg_retornada + lista_equipamentos_todos
                resposta = "".join(str(x) for x in msg_retornada)
                return resposta

                # resposta2 = "".join(x for x in msg_retornada)
                # resp_encode = resposta.encode()  #> bytes
                # resp_b = f"b'{resposta}'"  #> string
                # resp_def = teste_cria_resposta_encodada(resposta)
                # resp_encode = resposta  #> bytes
                # resp_ascii = resposta.encode('ascii', 'ignore')
                # resp_bytes = bytes(resposta)

            elif funcao == "3":  # Alteração de Estado de Chave
                print('funcao: ', funcao)

                # return

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]
                id_equipamento = msg_dividida[6]
                comando = int(msg_dividida[7])

                nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)  #> deixa o nome completo "swtcontrol."
                # nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)[5:]  #* retira o "Line." do nome Completo do elemento Line que é um switch

                estado_atual = int(dssim_obj.get_switch_state(nome_opendss.split(".")[1])) # type: ignore

                if comando != estado_atual:  # se o novo estado é diferente do atual
                    resposta = dssim_obj.set_switch_state(nome_opendss, comando)

                    if resposta == 'OK':  # Significa que foi executada com sucesso pelo OpenDSS-G. Verificar o que ocorre se a chave já estivesse aberta

                        msg_retornada = func100acknowledgment(int(funcao), 1)

                        # dssim_obj.update_flow_needed = True  # força solução do fluxo novamente porque houve mudança no estado da chave
                        if dssim_obj.check_sim_needed(hora, minuto, segundo):
                            # Simula
                            dssim_obj.solve_time(hora, minuto, segundo)
                            # Atualiza Grafico com novo estado das chaves
                            time.sleep(0.5)
                            dssim_obj.refresh_gui("isolation")
                            # dssim_obj.refresh_gui("powers")

                    else:
                        msg_retornada = func100acknowledgment(int(funcao), 0)
                else:  # caso contrário, não é necessário fazer nada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            # elif funcao == "4":  # Simulação de Falta

            #     qtde_bytes_rcv = msg_dividida[1]
            #     hora = msg_dividida[2]
            #     minuto = msg_dividida[3]
            #     segundo = msg_dividida[4]

            #     tipo_equipamento = msg_dividida[5]
            #     id_equipamento = msg_dividida[6]
            #     tipo_curto = msg_dividida[7]
            #     valor_percentual_distancia = msg_dividida[8]
            #     resistencia = msg_dividida[9]  # resistência de falta
            #     indicacao_calculo = msg_dividida[10]

            #     if tipo_equipamento == "1":  # Falta em Barra

            #         nome_barra_opendss = dssim_obj.get_nome_opendss(id_equipamento, "barra")
            #         resposta = dssim_obj.set_new_bus_fault(nome_barra_opendss, int(tipo_curto), resistencia)

            #     else:  # Falta em Trecho

            #         nome_trecho_opendss = dssim_obj.get_nome_opendss(id_equipamento)
            #         resposta = dssim_obj.set_new_line_fault(nome_trecho_opendss, float(valor_percentual_distancia), int(tipo_curto), resistencia)

            #     if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
            #         msg_retornada = func100acknowledgment(int(funcao), 1)
            #     else:
            #         msg_retornada = func100acknowledgment(int(funcao), 0)

            #     # Mensagem Display
            #     msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

            #     return "".join(str(x) for x in msg_retornada)

            # elif funcao == "5":  # Elimina Falta

            #     qtde_bytes_rcv = msg_dividida[1]
            #     hora = msg_dividida[2]
            #     minuto = msg_dividida[3]
            #     segundo = msg_dividida[4]

            #     resposta = dssim_obj.clear_fault()

            #     if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
            #         msg_retornada = func100acknowledgment(int(funcao), 1)
            #     else:
            #         msg_retornada = func100acknowledgment(int(funcao), 0)

            #     # Mensagem Display
            #     msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

            #     return "".join(str(x) for x in msg_retornada)

            elif funcao == "6" or funcao == "7":  # Alteração de Tap de Transformador

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                tap = int(msg_dividida[7])

                # if tap > 1:
                #     variacao_tap = 1
                # else:
                #     variacao_tap = tap

                logger.debug('tap MC: %s', tap)
                equipment_logger.info("func=%s equip=%s id=%s tap=%s", funcao, equipamento_rotulo(tipo_equipamento), id_equipamento, tap)


                nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                resposta = dssim_obj.varia_tap(nome_opendss, tap)
                equipment_logger.info("func=%s transformador id=%s nome=%s tap=%s resposta=%s", funcao, id_equipamento, nome_opendss, tap, resposta)

                if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            # elif funcao == "8":  # Alteração no valor de Reativo em BC

            #     qtde_bytes_rcv = msg_dividida[1]
            #     hora = msg_dividida[2]
            #     minuto = msg_dividida[3]
            #     segundo = msg_dividida[4]

            #     tipo_equipamento = msg_dividida[5]
            #     id_equipamento = msg_dividida[6]
            #     novo_kvar = msg_dividida[7]

            #     nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
            #     resposta = dssim_obj.set_capacitor_kvar(nome_opendss, novo_kvar)

            #     if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
            #         msg_retornada = func100acknowledgment(int(funcao), 1)
            #     else:
            #         msg_retornada = func100acknowledgment(int(funcao), 0)

            #     # Mensagem Display
            #     msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

            #     return "".join(str(x) for x in msg_retornada)

            # elif funcao == "10":  # Alteração no valor de Carga

            #     qtde_bytes_rcv = msg_dividida[1]
            #     hora = msg_dividida[2]
            #     minuto = msg_dividida[3]
            #     segundo = msg_dividida[4]

            #     tipo_equipamento = msg_dividida[5]
            #     id_equipamento = msg_dividida[6]
            #     novo_kw = msg_dividida[7]
            #     novo_kvar = msg_dividida[8]

            #     nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
            #     resposta = dssim_obj.set_load_powers(nome_opendss, novo_kw, novo_kvar)

            #     if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
            #         msg_retornada = func100acknowledgment(int(funcao), 1)
            #     else:
            #         msg_retornada = func100acknowledgment(int(funcao), 0)

            #     # Mensagem Display
            #     msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

            #     return "".join(str(x) for x in msg_retornada)

            elif funcao == "11":  # Alteração do Estado de BC

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                novo_estado = msg_dividida[7]

                nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                resposta = dssim_obj.set_capacitor_state(nome_opendss, int(novo_estado))
                logger.info("func=11 capacitor id=%s nome=%s estado=%s resposta=%s", id_equipamento, nome_opendss, novo_estado, resposta)

                if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            else:
                print(u"Função " + funcao + u" não reconhecida")
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Nada enviado!" + "\n\n")
                return None

        return "nao existe objeto dssim"

def decodifica_mensagem(conn, data):
    """ Método que recebe a str com a mensagem que vem no Buffer e decodifica cada pacote de mensagem.
    Foi necessário criar essa função, pois como o envio e recebimento de mensagens é assíncrono, pode ser
    que em uma determinada leitura do conteúdo do buffer venha mais de um pacote de mensagem."""


    application_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(application_path, "in", "config_smartRT.yml")

    inicio = time.time()

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)["data_SmartRT"]

    list_a, list_b, list_c = aux.build_tasks_from_config(config)


    mensagem = [struct.pack('<Q', 0)[0]]*16384    #< igual a ['\x00']
    copia_mensagem = [struct.pack('<Q', 0)[0]]*16384


    decodificar_dados_recebidos = True
    tamanho_mensagem = 0
    data_len = len(data)
    # print('data: ', data)

    # Atualiza a mensagem recebida (caso incompleta anteriormente)
    for i in range(data_len):
        mensagem[i + tamanho_mensagem] = data[i]
    tamanho_mensagem = tamanho_mensagem + data_len

    while decodificar_dados_recebidos:
        # decodificar_dados_recebidos = False
        quantidade_bytes = ord(mensagem[1]) + 256 * ord(mensagem[2])
        # print('quantidade_bytes: ', quantidade_bytes)

        if quantidade_bytes <= tamanho_mensagem:

            # if resposta is not None:
            if ord(data[0]) == 3:
                print("oi")

            # print('mensagem: ', mensagem)
            # print('mensagem[0:quantidade_bytes]: ', mensagem[0:quantidade_bytes])

            # ─── Chama Process Data ───────────────────────────────
            resposta = process_data(mensagem[0:quantidade_bytes])  # só envia o conteúdo de um único pacote

            if resposta is not None:
                resposta_len = len(resposta)
                # for i in range(resposta_len):
                #     msg_resposta[i + tamanho_mensagem] = resposta[i]
                # print('data: ', data)
                # print('resposta: ', resposta)

                #~ prints de MONITORAMENTO: tamanho da mensagem
                # print('\nutf-8')
                # print('\nlen_data: ', data_len)
                # print('data_encode:\t\t', data.encode())
                # print('resposta_encode:\t', resposta.encode())
                # print(f'len_resposta: {resposta_len}\n')

                # print('\nlatin-1')
                # print('len_data: ', data_len)
                # print('data_encode:\t\t', data.encode('latin-1'))
                # print('resposta_encode:\t', resposta.encode('latin-1'))
                # print(f'len_resposta: {resposta_len}\n')

                # conn.sendall(resposta)
                try:
                    # print(resposta)
                    # print("\nlatin-1:\t", resposta.encode('latin-1'))
                    # print("\nutf-8:\t\t", resposta.encode('utf-8'))
                    resp = resposta.encode('latin-1')
                    conn.send(resp)
                    pass
                except ConnectionAbortedError:
                    print(f'Erro de conexão (ConnectionAbortedError).')
                else:
                    pass

            # Verifica se a decodificação dos dados recebidos deve prosseguir
            if quantidade_bytes < tamanho_mensagem:
                for i in range(tamanho_mensagem):
                    copia_mensagem[i] = mensagem[i]

                for i in range(tamanho_mensagem - quantidade_bytes):
                    mensagem[i] = copia_mensagem[i + quantidade_bytes]

                tamanho_mensagem = tamanho_mensagem - quantidade_bytes

            else:
                tamanho_mensagem = 0
                decodificar_dados_recebidos = False

        else:  # Mensagem recebida está incompleta
            decodificar_dados_recebidos = False

        qls("✦", "─")


def reconstroi_msg(data):
    """Função que reconstrói uma mensagem recebida do Módulo Central"""

    funcao = int(ord(data[0]))
    mensagem = ""

    if funcao == 99:  # Retorna ID do Equipamento por meio de Código

        # Essa função não vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem o equipamento:
        # Byte 7: Número do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) = 0
        # Byte 9: Id do Equipamento (Byte 2) = 0
        # Byte 10: Id do Equipamento (Byte 3) = 0
        # Byte 11: Id do Equipamento (Byte 4) = 0
        # Byte 12 a N: Código do Equipamento

        for i in range(len(data)):
            if ord(data[i]) == 0:  # não adicionar espaços em branco que vem na mensagem...
                continue
            if i <= 10:
                mensagem = mensagem + str(ord(data[i])) + ";"
            else:  # i > 10:
                mensagem = mensagem + data[i]
            # dado uma string de comprimento unitário, a função ord retorna o valor do byte quando o argumento
        # é uma string de 8-bit
        mensagem = mensagem + ";"
        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 1:  # Solicitação de Registros

        # Essa função não vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 5 Bytes que descrevem o equipamento para cada equipamento:

        # Equipamento 1:
        # Byte 7: Número do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1)
        # Byte 9: Id do Equipamento (Byte 2)
        # Byte 10: Id do Equipamento (Byte 3)
        # Byte 11: Id do Equipamento (Byte 4)

        # Equipamento 2:
        # Byte 12: Número do Tipo do Equipamento
        # Byte 13: Id do Equipamento (Byte 1)
        # Byte 14: Id do Equipamento (Byte 2)
        # Byte 15: Id do Equipamento (Byte 3)
        # Byte 16: Id do Equipamento (Byte 4)

        # E assim vai..

        count = 0
        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == (7 + 5*count + 1) or i == (7 + 5*count + 2) or i == (7 + 5*count + 3):  # não adicionar espaços em branco que vem na mensagem...
                continue
            if i == (7 + 5*count):  # 7, 12, 17,...
                mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[(7 + 5*count): (7 + 5*count + 4)])) + ';'

            else:
                if i == (11 + 5*count):
                    count = count + 1    # Se i == 11, é porque já passou para o segundo equipamento, portanto, incrementar count
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 3:  # Alteração de Estado em Chaves

        # Essa função já vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem a chave selecionada:

        # Byte 7: Número do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1)
        # Byte 9: Id do Equipamento (Byte 2)
        # Byte 10: Id do Equipamento (Byte 3)
        # Byte 11: Id do Equipamento (Byte 4)
        # Byte 12: Novo estado da chave

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10:  # não adicionar espaços em branco que vem na mensagem...
                continue
            elif i == 7:
                mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[7:11])) + ';'

            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 4:  # Simulação de Falta

        # Essa função já vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 7 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Informações do Equipamento:

        # Byte 7: Número do Tipo do Equipamento (1 ou 2)
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # Informações do Curto em si

        # Byte 12: Tipo de Curto-Circuito (Valor de 0 a 4 conforme tabela de curtos)
        # Byte 13: Valor % referente a distância entre a barra 1 o defeito / tamanho do trecho (Byte 1) - Float
        # Byte 14: Valor % referente a distância entre a barra 1 o defeito / tamanho do trecho (Byte 2) - Float
        # Byte 15: Valor % referente a distância entre a barra 1 o defeito / tamanho do trecho (Byte 3) - Float
        # Byte 16: Valor % referente a distância entre a barra 1 o defeito / tamanho do trecho (Byte 4) - Float
        # Byte 17: Valor da impedância de defeito em Ohms. (Byte 1) - Float
        # Byte 18: Valor da impedância de defeito em Ohms. (Byte 2) - Float
        # Byte 19: Valor da impedância de defeito em Ohms. (Byte 3) - Float
        # Byte 20: Valor da impedância de defeito em Ohms. (Byte 4) - Float
        # Byte 21: Indicação de cálculo de curto-circuito com (1) ou sem pré-falta (0).

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10 or i == 13 or i == 14 or i == 15 or i == 17 or i == 18 or i == 19:  # não adicionar espaços em branco que vem na mensagem...
                continue
            elif i == 7:
                mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[7:11])) + ';'
            elif i == 12:  # Distância
                mensagem = mensagem + str(aux.monta_float_from_bytes(data[12:16])) + ';'
            elif i == 16:  # Impedância
                mensagem = mensagem + str(aux.monta_float_from_bytes(data[16:20])) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 5:  # Elimina Falta

        # Essa função já vem com a quantidade de bytes fechada.

        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        for i in range(len(data)):
            if ord(data[i]) == 0 and i == 2:  # não adicionar espaços em branco que vem na mensagem...
                continue
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 6:  # Alteração no Tap de Transformador
        """Essa função já vem com a quantidade de bytes fechada.

            Essa mensagem possui sempre 7 bytes iniciais
            Byte 1: Função
            Byte 2: Quantidade de Bytes - byte 1
            Byte 3: Quantidade de Bytes - byte 2 = 0
            Byte 4: Hora
            Byte 5: Minuto
            Byte 6: Segundo

            Mais 5 Bytes que descrevem o transformador selecionado:

            Byte 7: Número do Tipo do Equipamento
            Byte 8: Id do Equipamento (Byte 1) - Inteiro
            Byte 9: Id do Equipamento (Byte 2) - Inteiro
            Byte 10: Id do Equipamento (Byte 3) - Inteiro
            Byte 11: Id do Equipamento (Byte 4) - Inteiro

            E 1 Byte com a variação do tap
            Byte 12: Variação (Byte) - Inteiro sem sinal. Precisamos converter de NotSignedToSigned
        """

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10:  # não adicionar espaços em branco que vem na mensagem...
                continue
            if i == 7:
                mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[7:11])) + ';'
            elif i == 11:
                mensagem = mensagem + str(aux.monta_byte_to_signed_int(str(ord(data[i])))) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 7:  # Alteração no Tap de Regulador de Tensão
        """Essa função já vem com a quantidade de bytes fechada.

            Essa mensagem possui sempre 7 bytes iniciais
            Byte 1: Função
            Byte 2: Quantidade de Bytes - byte 1
            Byte 3: Quantidade de Bytes - byte 2 = 0
            Byte 4: Hora
            Byte 5: Minuto
            Byte 6: Segundo

            Mais 5 Bytes que descrevem o transformador selecionado:

            Byte 7: Número do Tipo do Equipamento
            Byte 8: Id do Equipamento (Byte 1) - Inteiro
            Byte 9: Id do Equipamento (Byte 2) - Inteiro
            Byte 10: Id do Equipamento (Byte 3) - Inteiro
            Byte 11: Id do Equipamento (Byte 4) - Inteiro

            E 1 Byte com a variação do tap
            Byte 12: Variação (Byte) - Inteiro sem sinal. Precisamos converter de NotSignedToSigned
        """

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10:  # não adicionar espaços em branco que vem na mensagem...
                continue
            if i == 7:
                mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[7:11])) + ';'
            elif i == 11:
                mensagem = mensagem + str(aux.monta_byte_to_signed_int(str(ord(data[i])))) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 8 or funcao == 11:  # Funções 8 e 11 possuem a mesma estrutura (Alteração no valor de reativo BC e Alteração em estado de BC, respectivamente)

        # Essa função já vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem a chave selecionada:

        # Byte 7: Número do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # Byte 12: Nova Potência Reativa (Byte 1)  - Float Função 8 ; # Byte 12: Novo Estado do BC (Byte 1)  - Int Função 8 ;
        # Byte 13: Nova Potência Reativa (Byte 2)  - Float Função 8 ; # Byte 13: Nova Estado do BC (Byte 2)  - Int Função 8 ;
        # Byte 14: Nova Potência Reativa (Byte 3)  - Float Função 8 ; # Byte 14: Nova Estado do BC (Byte 3)  - Int Função 8 ;
        # Byte 15: Nova Potência Reativa (Byte 4)  - Float Função 8 ; # Byte 15: Nova Estado do BC (Byte 4)  - Int Função 8 ;

        count = 0
        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == (7 + 4*count + 1) or i == (7 + 4*count + 2) or i == (7 + 4*count + 3):  # não adicionar espaços em branco que vem na mensagem...
                if i == (10 + 4*count):
                    count = count + 1    # Se i == 11, é porque já passou para o segundo equipamento, portanto, incrementar count
                continue
            if i == (7 + 4*count):  # 7, 12, 17,...
                if count == 0 or (count == 1 and funcao == 11):
                    mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
                elif count == 1:
                    mensagem = mensagem + str(aux.monta_float_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    elif funcao == 9:  # Alteração no valor de suprimento
        return "funcao 9 ainda não implementada"

    elif funcao == 10:  # Alteração no valor de carga

        # Essa função já vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem a chave selecionada:

        # Byte 7: Número do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # Byte 12: Nova Potência Ativa (Byte 1)  - Float
        # Byte 13: Nova Potência Ativa (Byte 2)  - Float
        # Byte 14: Nova Potência Ativa (Byte 3)  - Float
        # Byte 15: Nova Potência Ativa (Byte 4)  - Float

        # Byte 16: Nova Potência Reativa (Byte 1)  - Float
        # Byte 17: Nova Potência Reativa (Byte 2)  - Float
        # Byte 18: Nova Potência Reativa (Byte 3)  - Float
        # Byte 19: Nova Potência Reativa (Byte 4)  - Float

        count = 0
        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == (7 + 4 * count + 1) or i == (7 + 4 * count + 2) or i == (7 + 4 * count + 3):  # não adicionar espaços em branco que vem na mensagem...
                if i == (10 + 4 * count):
                    count = count + 1  # Se i == 11, é porque já passou para o segundo equipamento, portanto, incrementar count
                continue
            if i == (7 + 4 * count):  # 7, 12, 17,...
                if count == 0:
                    mensagem = mensagem + str(aux.monta_inteiro_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
                else:
                    mensagem = mensagem + str(aux.monta_float_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print("msg reconstruida, " + mensagem)
        return str(mensagem)

    else:
        return u"Função não identificada, mensagem não pôde ser reconstruída!"

def handle_client(client_socket: socket.socket, client_address: tuple) -> None:
    """Gerencia a comunicação com um cliente específico."""
    logging.info(f"Conexão estabelecida com {client_address}")

    # O 'with' garante o fechamento do socket do cliente ao terminar
    with client_socket:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    logging.info(f"Cliente {client_address} desconectou voluntariamente.")
                    break

                rcvd_data = data.decode('latin-1')
                decodifica_mensagem(client_socket, rcvd_data)

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