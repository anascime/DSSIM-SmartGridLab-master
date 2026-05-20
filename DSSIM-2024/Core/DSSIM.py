###  # -*- coding: UTF-8 -*-

"""

Classe responsável por executar a comunicação do aplicativo em Python com o DSSim.
Ela contém métodos que tornam a comunicação com o DSSim mais legível.
Novos métodos devem ser implementado na medida em que mais informações da simulação
no DSSim são necessárias.

"""

__author__ = 'CelsoRocha' and 'Paulo Radatz'

from decimal import ROUND_UP
import socket
# import pandas as pd
import ctypes
from statistics import variance
import time
import datetime
import pandas as pd

with pd.option_context('display.max_rows', 10, 'display.max_columns', 5):
    pass
from App.Fontes.Auxiliar import *


class DSSim:

    fault_dictionary = {0: [".1.2.3", ".0.0.0", 3], 1: [".2", ".3", 1], 2: [".1", ".0", 1], 3: [".1", "0", 1],
                        4: [".2.3", ".0.0", 2]}
    # 0: Falta Trifásica (abc)
    # 1: Falta Dupla-Fase (bc)
    # 2: Falta Fase-Terra (at)
    # 3: Falta Fase-Terra com Impedência de Aterramento (at)
    # 4: Falta Dupla-Fase-Terra (bct)

    def __init__(self, TCP_IP, TCP_PORT, BUFFER_SIZE, Form):
        """Cria um novo objeto DSSIM"""

        self.TCP_IP = TCP_IP                                    # IP do Servidor criado pelo DSSIM
        self.TCP_PORT = TCP_PORT                                # Porta onde o servidor se encontra
        self.BUFFER_SIZE = BUFFER_SIZE
        self.form = Form

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria o socket
        self.frame_guids = None                                     # Frame que armazena o nome de todos os elementos da rede
        self.frame_buses = None                                     # Frame que armazena o nome de todas as barras da rede

        # Inicializa algumas variáveis importantes para controle da simulação no OpenDSS-G
        self.is_first_simulation = True                          # Flag que indica se alguma simulação já foi feita
        self.initial_time_step = None                            # Passo de Tempo Inicial da Simulação no OpenDSS-G
        self.current_time = [0]*3                                # Armazena o último instante de tempo
        self.time_step = None                                    # Armazena o passo de tempo de simulação definido no Módulo Central

    #--------------------------------------------------------------------# #
    # ─── Métodos Do Tipo Get ──────────────────────────────────────────────
    #--------------------------------------------------------------------# #

    def get_simulation_time(self, unidade):
        """ Método que retorna o tempo da simulação
        A unidade pode ser 's', 'm', 'h' ou 'd'  """

        if unidade == 's' or unidade == 'm' or unidade == 'h':
            message = "01;"
        elif unidade == 'd':
            message = "02;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, f"{message}\n\n")
        # self.s.send(message.encode())
        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")

        tamanho = int(data[:8], 16) + 8

        if unidade == 's':
            return float(data[8:tamanho])
        elif unidade == 'm':
            return float(data[8:tamanho])/60.0
        elif unidade == 'h':
            return float(data[8:tamanho])/3600.0
        elif unidade == 'd':
            return float(data[8:tamanho])

    def get_all_nodes_voltages(self, unidade):
        """Método que retorna lista de floats (tensão em todos os nós do circuito)

        Opções unidade:
            "pu": retorna uma lista com a magnitude da tensão em todos os nós em pu
            "kV": retorna uma lista com a magnitude e a fase da tensão em todos os nós em kV, no formato retangular
        """

        if unidade == 'pu':
            message = "03;"

        elif unidade == 'kV':
            message = "04;"    # Não entendi o que está acontecendo aqui

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, f"{message}\n\n")
        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        # print(data)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")

        tamanho = int(data[:8], 16) + 8

        lista = data[8:tamanho].split(b"\t")        # Separação utilizada é um tab
        lista = [float(x) for x in lista]   # Converte para Float

        return lista

    def get_last_event(self):
        """Método que retorna bytes com o último evento realizado no DSSim"""

        # Opções conhecidas até o momento:
        #   "Switch": quando o estado de alguma chave é alterado na interface
        #   "Fault": quando uma falta é aplicada na interface
        #   "Clear Fault": quando o usuário selciona o botão "Clear faults" no DSSim

        message = "35;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")

        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def get_bus_voltages(self, bus_name):
        """Executa comandos no ODSS e retorna lista de floats (tensões)

        Método que recebe o nome de uma barra e retorna as tensões nodais Van, Vbn, Vcn e Vnt
        """

        self.send_dss_command("set bus=" + bus_name)
        voltages = self.send_dss_command("voltages")
        # print(voltages)
        voltages = voltages.replace(b" ", b"")  # remove os espaços em branco do bytes
        voltages = voltages[:-1]  # deleta o último caractere, uma vírgula extra
        voltages = voltages.split(b",")
        voltages = [float(x) for x in voltages]  # Converte para Float

        return voltages

    def get_elem_voltages(self, element_name, terminal):
        """Executa comandos no ODSS e retorna lista de floats (tensões)

        Método que recebe o nome de um elemento e retorna as tensões nodais nos seus terminais
        """
        self.send_dss_command("select " + element_name + " " + "terminal = " + str(terminal))
        voltages = self.send_dss_command("voltages")
        # print(voltages)
        voltages = voltages.replace(b" ", b"")  # remove os espaços em branco do bytes
        voltages = voltages[:-1]  # deleta o último caractere, uma vírgula extra
        voltages = voltages.split(b",")
        voltages = [float(x) for x in voltages]  # Converte para Float

        # Sempre temos que retornar 4 valores de tensão de fase para o Módulo Central.
        while len(voltages) < 9:
            voltages.append(float(0.0))  # Enviar zero nas outras fases

        return voltages


    def get_elem_currents(self, element_name):
        """Executa comandos no ODSS e retorna lista de floats (correntes)

        Método que recebe o nome completo de um PDE ou PCE do OpenDSS e
        retorna as correntes que entram em cada um dos seus nós, dos dois terminais
        """

        tipoequip = element_name.split(".")[0]
        if tipoequip == "SwtControl":
             element_name = (self.send_dss_command("? " + element_name + ".SwitchedObj")).decode()


        self.send_dss_command("select " + element_name)
        currents = self.send_dss_command("currents")
        currents = currents.replace(b" ", b"")  # remove os espaços em branco do bytes
        currents = currents[:-1]  # deleta o último caractere, uma vírgula extra
        currents = currents.split(b",")
        currents = [float(x) for x in currents]  # Converte para Float

        # Sempre temos que retornar 4 valores de corrente de fase para o Módulo Central.
        while len(currents) < 9:
            currents.append(float(0.0))  # Enviar zero nas outras fases

        return currents

    def get_switch_state(self, switch_name):
        """Método que recebe o nome de um switch e retorna int (0 ou 1: estado da chave)"""

        message = "19;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")

        tamanho = int(data[:8], 16) + 8
        lista = data[8:tamanho].decode()
        # print(lista)
        lista = lista[:-1].split()  # deleta última linha, separa as duas linhas restantes e separa por tabulação
        lista_2 = []
        for i in lista:
            if i != "0" and i != "1":
                i = i.split(".", 1)[1]
            lista_2.append(i)



        # lista = [i.split(".", 1) for i in lista]
        print(lista)
        print(lista_2)
        # print(str(lista))

        if switch_name in lista_2:
            index = float(lista_2.index(switch_name))
            x = int(index - 1)
            # x = int(index - len(lista_2)/2)

            return lista_2[x]
        else:
            return None

    def get_switch_lock(self, switch_control_name):
        """Método que recebe o nome de um switchcontrol e verifica se ele está travado ou não."""

        lock = self.send_dss_command("? swtcontrol." + switch_control_name + ".lock").decode() # Yes or No
        if lock == "No":
            return 0
        elif lock == "Yes":
            return 1

    def get_total_powers(self, element_name, terminal):
        """Executa comandos no ODSS e retorna 4 floats

        Método que recebe o nome de um element no OpenDSS e retorna a potência ativa e
        reativa total do elemento
        """
        # Se o elemento possuir n fases, a potência total será P1+P2+...+Pn. O mesmo vale para Q.
        # terminal pode ser: 1 , 2 ou None. Se None, o resultado é uma tupla com (P1,Q1,P2,Q2)
        self.send_dss_command("select " + element_name)
        powers = self.send_dss_command("powers")
        # print(powers)
        powers = powers.replace(b" ", b"")  # remove os espaços em branco do bytes
        powers = powers[:-1]  # deleta o último caractere, uma vírgula extra
        powers = powers.split(b",")
        powers = [float(x) for x in powers]  # Converte para Float

        classe_elemento = element_name.split(".")[0]

        if classe_elemento.lower() == ("load" or "capacitor" or "reactor"):
            n_phases = len(powers) / 2
            terminal = 1  # força leitura da potência do único terminal que tem

            print('len(powers): ', len(powers))
            print("n_phases = len(powers) / 2")
            print(f'n_phases = {n_phases}')
        else:
            # n_phases = len(powers) / 4  #?????
            n_phases = len(powers) / 2

            print('len(powers): ', len(powers))
            print("n_phases = len(powers) / 2")
            print(f'n_phases = {n_phases}')

        p_total_1 = 0
        q_total_1 = 0
        p_total_2 = 0
        q_total_2 = 0

        for i in range(round(n_phases)):  #? o que fazer com valor quebrado de n_phases?
            p_total_1 = powers[2 * i] + p_total_1
            q_total_1 = powers[2 * i + 1] + q_total_1

            # if classe_elemento.lower() != ("load" or "capacitor" or "reactor"):
            #     p_total_2 = powers[int(2 * i + n_phases * 2)] + p_total_2
            #     q_total_2 = powers[int(2 * i + 1 + n_phases * 2)] + q_total_2

        if terminal == 1:
            return p_total_1, q_total_1

        elif terminal == 2:
            return p_total_2, q_total_2

        elif terminal is None:
            return p_total_1, q_total_1, p_total_2, q_total_2

    def get_phase_powers(self, element_name, terminal, phase):
        """Executa comandos no ODSS e retorna tupla ou None

        Método que recebe o nome de um elemento no OpenDSS, o terminal e
        um nó e retorna a potência ativa e reativa que entram nesse nó
        """

        self.send_dss_command("select " + element_name)
        powers = self.send_dss_command("powers")
        # print(powers)
        powers = powers.replace(b" ", b"")  # remove os espaços em branco do bytes
        powers = powers[:-1]  # deleta o último caractere, uma vírgula extra
        powers = powers.split(b",")
        powers = [float(x) for x in powers]  # Converte para Float

        # n_phases = len(powers)/4  #?????
        n_phases = len(powers)/2

        if phase > n_phases:
            ctypes.windll.user32.MessageBoxW(0, "O elemento " + '"{}"'.format(element_name) + " possui somente " + str(n_phases) +
            " fases. Fase " + str(phase) + " solicitada.", "Conexão DSSimPC-v2.0", 0)
            return None
        else:
            powers_tupla = powers[6*(terminal-1) + 2*(phase-1)], powers[6*(terminal-1) + 2*(phase-1) + 1]   # P, Q
            return powers_tupla

    def get_transformer_tap(self, transformer_name, winding):
        """Método que recebe o nome de um transformador e um enrolamento e
        retorna o tap atual desse enrolamento em pu e em passos
        """

        taps_array = self.send_dss_command("? " + transformer_name + ".taps")
        taps_array = taps_array[1:-3]  # deleta [ ....  , ]
        taps_array = taps_array.split(b",")
        taps_array = [float(x) for x in taps_array]

        if winding > len(taps_array):
            ctypes.windll.user32.MessageBoxW(0, "O transformador " + '"{}"'.format(transformer_name) + " possui somente " + str(len(taps_array)) +
                                             " enrolamentos. Tap do enrolamento " + str(winding) + " solicitado.", "Conexão DSSimPC-v2.0", 0)
            return None
        else:

            # Convertendo para passos
            maxtap = float(self.send_dss_command("? " + transformer_name + ".maxtap"))
            mintap = float(self.send_dss_command("? " + transformer_name + ".mintap"))
            num_taps = float(self.send_dss_command("? " + transformer_name + ".numtaps"))

            step_pu = (maxtap - mintap) / num_taps

            step = (taps_array[winding-1] - 1.0) / step_pu + (num_taps / 2 + 1)

        return taps_array[winding-1], int(round(step))   # int(-1.0) estava retornando 0 (int) ao invés de -1 (int)

    def get_capacitor_state(self, capacitor_name):
        """Método que recebe o nome de um capacitor e retorna o seu estado"""

        state = self.send_dss_command("? " + capacitor_name + ".states")
        state = state[2]
        return int(state)

    def get_capacitor_kvar(self, capacitor_name):
        """Método que recebe o nome de um capacitor e retorna o valor de sua potência reativa"""

        kvar = self.send_dss_command("? " + capacitor_name + ".kvar")
        kvar = kvar[1:-1]
        return float(kvar)

    def get_num_phases(self, element_name):
        """Método que recebe o nome de um elemento e retorna a quantidade de fases do mesmo"""

        phases = self.send_dss_command("? " + element_name + ".phases")
        return int(phases)

    #--------------------------------------------------------------------# #
    # ─── Métodos Do Tipo Set ──────────────────────────────────────────────
    #--------------------------------------------------------------------# #

    def set_switch_state(self, nome, status):
        """Método que abre/fecha um switch"""

        # identifica o tamanho da mensagem
        tamanho = len(nome) + 2  #: + 1 pelo sinal de igualdade e + 1 pelo status
        tamanho_hex = "%04x" % tamanho
        message = "18;" + tamanho_hex + nome + "=" + str(status) + ";"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")

        msgenv = message.encode()
        self.s.send(message.encode())

        time.sleep(0.1)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")

        tamanho = int(data[:8], 16) + 8
        return (data[8:tamanho]).decode()

    def set_new_bus_fault(self, nome_barra, tipo, resistencia):
        """Método que aplica uma falta em uma dada barra com uma dada resistência de falta.

        O tipo de falta é dado de acordo com o dicionário DSSim.fault_dictionary.
        """

        if resistencia is None:
            resistencia = 0.0001  # valor default do OpenDSS

        resposta = self.send_dss_command("new fault." + nome_barra + " phases = " + str(DSSim.fault_dictionary[tipo][2]) + " bus1= " +
                                         nome_barra + DSSim.fault_dictionary[tipo][0] + " bus2=" +
                                         nome_barra + DSSim.fault_dictionary[tipo][1] + " r = " + resistencia)
        return resposta

    def set_new_line_fault(self, nome_linha, distancia_pct, tipo, resistencia):
        """Método que aplica uma falta no meio de um trecho de linha."""

        # 1º: Armazena dados necessários da linha
        length_original = float(self.send_dss_command("? " + nome_linha + ".length"))
        bus1_original_completo = self.send_dss_command("? " + nome_linha + ".bus1")
        bus1_original_nome = bus1_original_completo.split(b".", 1)[0]
        bus1_original_phases_string = bus1_original_completo.split(b".", 1)[1]
        bus2_original_completo = self.send_dss_command("? " + nome_linha + ".bus2")

        # 2º: Cria duas novas linhas em série cujo comprimento total é igual ao comprimento da linha original
        self.send_dss_command("new " + nome_linha + "_1 like=" + nome_linha.split(".", 1)[1] + " bus1=" + bus1_original_completo + " bus2="
                              + bus1_original_nome + "_aux." + bus1_original_phases_string + " length=" + str(length_original*distancia_pct))
        self.send_dss_command("new " + nome_linha + "_2 like=" + nome_linha.split(".", 1)[1] + " bus1=" + bus1_original_nome + "_aux." + bus1_original_phases_string
                              + " length=" + str(length_original * (1-distancia_pct)))

        # 3º: Desativa linha original
        self.send_dss_command(nome_linha + ".enabled=False")

        # 4º: Aplica a falta na barra auxiliar
        resposta = self.set_new_bus_fault(bus1_original_nome + b"_aux", tipo, resistencia)

        return resposta

    def set_transformer_tap(self, transformer_name, winding, tap):
        """Método que recebe o nome de um transformador, um enrolamento e um tap e seta o valor do tap."""

        num_windings = int(self.send_dss_command("? " + transformer_name + ".windings"))

        if winding > num_windings:
            ctypes.windll.user32.MessageBoxW(0, "O transformador " + '"{}"'.format(transformer_name) + " possui somente " + str(num_windings) +
                                             " enrolamentos. Tap do enrolamento " + str(winding) + " solicitado.", "Conexão DSSimPC-v2.0", 0)
            return None

        self.send_dss_command(transformer_name + ".wdg=" + str(winding) + " tap=" + str(tap))

    def set_capacitor_kvar(self, nome_capacitor, kvar):

        self.send_dss_command(nome_capacitor + ".kvar=" + str(kvar))

    def set_capacitor_state(self, nome_capacitor, state):

        states = self.send_dss_command("? Capacitor.Cap.states")
        print("antes: ", states)

        self.send_dss_command(nome_capacitor + ".states=" + str(state))
        # self.send_dss_command("CapControl.cap.states=" + str(state))

        states = self.send_dss_command("? Capacitor.Cap.states")
        print(f"depois: {states}")

    def set_load_powers(self, nome_carga, p, q):

        if (p is not None) and (q is not None):
            resposta_p = self.send_dss_command(nome_carga + ".kW=" + str(p))
            resposta_q = self.send_dss_command(nome_carga + ".kvar=" + str(q))
            return resposta_p, resposta_q
        elif (p is not None) and (q is None):
            resposta_p = self.send_dss_command(nome_carga + ".kW=" + str(p))
            return resposta_p
        elif (p is None) and (q is not None):
            resposta_q = self.send_dss_command(nome_carga + ".kvar=" + str(q))
            return resposta_q

    #--------------------------------------------------------------------# #
    # ─── Métodos De Interface Com O Mc ────────────────────────────────────
    #--------------------------------------------------------------------# #

    def retorna_id(self, codigo_equipamento_sinap, tipo_equipamento):
        """Método que recebe o código de um equipamento do Sinap e retorna o seu ID"""
        if self.frame_guids is not None:
            if tipo_equipamento != "1":  #> não é Barra
                # print(self.frame_guids.tail(31))
                # id = int(self.frame_guids.loc[(self.frame_guids["Codigo Sinap"] == codigo_equipamento_sinap.lower()), ["Id Sinap"]].values[0][0])
                cod_sin = codigo_equipamento_sinap.lower()
                df = self.frame_guids.loc[(self.frame_guids["Codigo Sinap"] == cod_sin), ["Id Sinap"]]
                id = int(df.values[0][0])
            else:  #> é barra
                # id = int(self.frame_buses.loc[(self.frame_buses["Codigo Sinap"] == codigo_equipamento_sinap.lower()), ["Id Sinap"]].values[0][0])
                cod_sin = codigo_equipamento_sinap.lower()
                df = self.frame_buses.loc[(self.frame_buses["Codigo Sinap"] == cod_sin), ["Id Sinap"]]
                id = int(df.values[0][0])
            return id
        else:
            print("Frame com nomes não armazenado!")

    def get_nome_opendss(self, id, tipo=None):
        """recebe ID e retorna nome completo do equipamento

        Método que recebe um ID de um equipamento do Sinap e retorna o
        nome completo (incluindo a sua classe) do equipamento no OpenDSS
        """
        id_equipamento = int(id)
        if tipo is None:
            # print(self.frame_guids)
            # df_tot = self.frame_guids.loc[(self.frame_guids["Id Sinap"] == id_equipamento)]
            df = self.frame_guids.loc[(self.frame_guids["Id Sinap"] == id_equipamento), ["Nome Completo"]]

            valor = df.values[0][0]

            nome_opendss = valor
            # nome_opendss = self.frame_guids.loc[(self.frame_guids["Id Sinap"] == id_equipamento), ["Nome Completo"]].values[0][0]
        else:  # Caso seja Barra
            # print(self.frame_buses)
            # df_tot = self.frame_buses.loc[(self.frame_guids["Id Sinap"] == id_equipamento)]
            df = self.frame_buses.loc[(self.frame_guids["Id Sinap"] == id_equipamento), ["Nome Completo"]]

            valor = df.values[0][0]

            nome_opendss = valor
            # nome_opendss = self.frame_buses.loc[(self.frame_buses["Id Sinap"] == id_equipamento), ["Nome Completo"]].values[0][0]
        return nome_opendss

    def get_frame_csv_final(self):
        self.frame_guids = pd.read_csv(self.data_path + "/" + "UUIDS_final.csv", engine='python')

    def get_last_simulation_type(self):    # Testa!!
        """ Método que identifica se o último tipo de simulação realizado pelo DSSim é do tipo Fluxo ou Curto.
        A lógica será a seguinte: se houver um elemento fault na rede, será do tipo Curto. Caso contrário, tipo Fluxo.

        Para identificar se há uma falta na rede utilizando comandos do OpenDSS, vamos utilizar o comando
        Export GUIDS. Se um elemento da classe "Fault" for identificado e se a sua propriedade "enabled" for "true",
        o resultado será "Curto", caso contrário, será "Fluxo"."""

        # self.armazena_nomes_elementos()
        self.get_frame_csv_final()
        try:

            nome_falta = self.frame_guids.loc[(self.frame_guids["Tipo Elemento"] == "Fault"), ["Nome OpenDSS"]]["Nome OpenDSS"].tolist()
            if len(nome_falta) == 0:
                # print("Fluxo")
                return "Fluxo"
            else:
                for i in range(len(nome_falta)):
                    if self.send_dss_command("? fault." + nome_falta[i] + ".enabled") == 'true':
                        # print("Curto")
                        return "Curto"
                    else:
                        # print("Fluxo, falta disabled")
                        return "Fluxo"
        except:  # Se não encontrar nenhum elemento com a classe
            # print("Fluxo")
            return "Fluxo"

    def varia_tap(self, transformer_name, tap):
        """ Método que recebe o nome de um trafo e uma variacao de tap e varia o tap do respectivo trafo"""

        # O tap no OpenDSS é especificado em pu. Por isso, precisamos converter para pu.
        # Convertendo para passos
        maxtap = float(self.send_dss_command("? " + transformer_name + ".maxtap"))
        mintap = float(self.send_dss_command("? " + transformer_name + ".mintap"))
        num_taps = float(self.send_dss_command("? " + transformer_name + ".numtaps"))
        tap_atual = self.send_dss_command("? " + transformer_name + ".tap")


        step_pu = (maxtap - mintap) / num_taps

        self.send_dss_command(transformer_name + ".wdg=1")  # Ativa o primeiro enrolamento
        kv1 = self.send_dss_command("? " + transformer_name + ".kv")

        self.send_dss_command(transformer_name + ".wdg=2")  # Ativa o segundo enrolamento
        kv2 = self.send_dss_command("? " + transformer_name + ".kv")

        # De acordo com o protocolo, o tap a ser variado deve ser o de enrolamento com maior tensão nominal
        if kv1 > kv2:
            wdg = 1
        else:
            wdg = 2

        self.send_dss_command(transformer_name + ".wdg=" + str(wdg))
        novo_tap = mintap + (tap - 1) * step_pu

        # Verifica se tap está nos extremos (mínimo ou máximo)
        if novo_tap > maxtap or novo_tap < mintap:
            return "OK"

        # Seta novo tap
        self.send_dss_command(transformer_name + ".tap=" + str(novo_tap))

        return "OK"

    #--------------------------------------------------------------------# #
    # ─── Métodos Auxiliares ───────────────────────────────────────────────
    #--------------------------------------------------------------------# #

    def send_dss_command(self, comando):
        """Método que executa um comando na linguagem de programação do OpenDSS"""

        # identifica o tamanho da mensagem
        tamanho = len(comando)
        tamanho_hex = "%04x" % tamanho  # converte "tamanho" para hexadecimal com 4 dígitos (por algum motivo, só funciona quando tem 4 dígitos. Se colocar com 8, não funciona.

        message = "25;" + tamanho_hex + comando + ";"
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")

        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")
        tamanho = int(data[:8], 16) + 8

        data_r = data[8:tamanho]

        return data_r

    def refresh_gui(self, tipo):
        """Método que atualiza a GUI do DSSim"""
        # Entender o porque de nem sempre a GUI atualizar. Parece que falta colocar algum delay

        if tipo == "overloads":
            message = "36;"
        elif tipo == "voltages":
            message = "37;"
        elif tipo == "powers":
            message = "38"
        elif tipo == "isolation":
            message = "41;"
        else:
            message = "41;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.send(message.encode())
        time.sleep(0.1)

        # data = self.s.recv(self.BUFFER_SIZE)
        # if self.form is not None:
        #     self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")
        # tamanho = int(data[:8], 16) + 8

        return
        # return data[8:tamanho]

    def step_in(self):
        """Método que avança um passo de tempo na simulação do DSSim"""

        message = "23;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")
        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def end_simulation(self):
        """Método que força o fim da simulação. Usar ao final da execução de vários step_in."""

        message = "24;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.send(message.encode())

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + b"\n\n")

        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def close(self):
        """Método que fecha a conexão com o servidor TCP"""
        self.s.close()

    def clear_fault(self, nome_barra=None, nome_linha=None):
        """Retira falta e retorna o circuito à condição inicial

        Método que retira uma falta e retorna o circuito à condição inicial de
        acordo com o tipo de falta (em Barra ou em Trecho).
        Declarar somente um dos dois.

        Se nenhum argumento for passado, devemos identificar todas as faltas na
        rede e eliminá-las, retornando a rede para o seu estado inicial.
        """

        if (nome_barra is not None) and (nome_linha is None):  # Falta em Barra
            resposta = self.send_dss_command("fault." + nome_barra + ".enabled=False")

        elif (nome_barra is None) and (nome_linha is not None):  # Falta em Trecho
            self.send_dss_command(nome_linha + "_1.enabled=False")  # desativa primeira linha
            self.send_dss_command(nome_linha + "_2.enabled=False")  # desativa segunda linha

            # desativa falta
            barra_falta = self.send_dss_command(b"? " + nome_linha + b".bus1") + b"_aux"
            self.send_dss_command(b"fault." + barra_falta + b".enabled=False")

            # reativa linha original
            resposta = self.send_dss_command(nome_linha + ".enabled=True")

        else:

            # Primeiro, devemos identificar todas as faltas no sistema:
            self.armazena_nomes_elementos()

            nome_faltas = self.frame_guids.loc[(self.frame_guids["Tipo Elemento"] == "Fault"), ["Nome OpenDSS"]]["Nome OpenDSS"].tolist()
            for i in range(len(nome_faltas)):
                if self.send_dss_command("? fault." + nome_faltas[i] + ".enabled") == 'true':
                    self.send_dss_command("fault." + nome_faltas[i] + ".enabled=false")

            resposta = "OK"

        return resposta

    def connect(self):

        if self.s.connect_ex((self.TCP_IP, self.TCP_PORT)) == 0:  # Conecta com o servidor
            print("Comunicação com OpenDSS-G estabelecida com sucesso!")
            return True
        else:
            ctypes.windll.user32.MessageBoxW(0, "Conexão TCP não estabelecida! Verifique os dados da conexão com o "
                                                "servidor!", "Conexão DSSimPC-v2.0", 0)
            return False
        # self.s.close()   # é necessário abrir e fechar a conexão a todo instante ?

    def armazena_path(self):
        """Método que armazena o caminho dos dados do DSSim.

        Será utilizado posteriormente quando formos ler os
        arquivos gerados por comandos "export"
        """
        self.data_path = self.send_dss_command("get datapath").decode()
        # print(self.data_path)

    def armazena_nomes_elementos(self):
        """Método que exporta as GUIDs de cada um dos elementos da rede.

        Usaremos este método para armazenar os nomes de todos os
        elementos em um dataframe somente uma vez
        """

        self.send_dss_command("export uuids")  #* substituição guids → uuids
        # self.send_dss_command("export guids")     # Verificar pq não está retornando o endereço do arquivo exportado

        casename = self.send_dss_command("get casename").decode() #> casename = circuit
        nomes = ["Completo"]
        self.frame_guids = pd.read_csv(self.data_path + "/" + casename + "_EXP_UUIDS.CSV", engine='python', names=nomes)

        self.frame_guids["Nome Completo"] = self.frame_guids["Completo"].str.split(' ').str.get(0)
        self.frame_guids["Tipo Elemento"] = self.frame_guids["Nome Completo"].str.split('.').str.get(0)
        self.frame_guids["Nome OpenDSS"] = self.frame_guids["Nome Completo"].str.split('.').str.get(1)
        self.frame_guids["Codigo Sinap"] = self.frame_guids["Nome OpenDSS"]
        self.frame_guids["Id Sinap"] = self.frame_guids.index

        #! print tabela
        # print('self.frame_guids:\n', self.frame_guids.to_markdown())
        print(self.frame_guids.head().to_markdown())
        self.frame_guids.drop("Completo", axis=1, inplace=True)

        cria_csv_id(self.frame_guids, self.data_path)

        # output_path = 'C:/DSSIM-SmartGridLab-master/resultados'
        # self.frame_guids.to_csv(output_path)

    def armazena_nomes_barras(self):
        """Exporta arquivos coordenadas

        Método que exporta o arquivo de Coordenadas das Barras de cada um dos elementos da rede. Usaremos este método para
        armazenar os nomes de todas as barras em um data frame somente uma vez
        """

        self.send_dss_command("export buscoords")  # Verificar pq não está retornando o endereço do arquivo exportado
        casename = self.send_dss_command("get casename").decode() #> casename = circuit
        nomes = ["Nome Completo", "X", "Y"]
        self.frame_buses = pd.read_csv(self.data_path + "/" + casename + "_EXP_BUSCOORDS.CSV", engine='python', names=nomes, usecols=["Nome Completo"])

        self.frame_buses["Codigo Sinap"] = self.frame_buses["Nome Completo"].str.split('_ID').str.get(0)
        self.frame_buses["Id Sinap"] = self.frame_buses["Nome Completo"].str.split('_ID').str.get(1)

        # print(self.frame_buses.head())

    def check_sim_needed(self, hora, minuto, segundo):
        """checa necessidade de novo passo de simulação no ODSS-G

        Esse método faz uma checagem se é preciso simular um novo passo de
        simulação no OpenDSS-G ou não.
        É preciso simular se o tempo especificado é diferente do último simulado.
        Caso contrário, checar se houve alguma alteração na rede que exija uma
        atualização do fluxo de potência.
        """

        # tempo_atual_sec = float(self.get_simulation_time('s'))
        # tempo_atual = str(datetime.timedelta(seconds=tempo_atual_sec))  # datetime
        # self.current_time[0] = float(tempo_atual.split(":")[0])
        # self.current_time[1] = float(tempo_atual.split(":")[1])
        # self.current_time[2] = float(tempo_atual.split(":")[2])
        tempo_atual_sec = self.get_simulation_time('s')  #> float

        # if tempo_atual_sec < 0:

        #     tempo_atual_sec = 66600

        #! timedelta espera int
        tempo_atual = str(datetime.timedelta(seconds=tempo_atual_sec))  # datetime

        # Se o tempo for negativo, ajustamos a string
        if 'day' in tempo_atual:
            tempo_atual = tempo_atual.split(", ")[-1]  # Pega apenas a parte 'hh:mm:ss'

        #! current_time é uma lista de int
        self.current_time[0] = float(tempo_atual.split(":")[0])
        self.current_time[1] = float(tempo_atual.split(":")[1])
        self.current_time[2] = float(tempo_atual.split(":")[2])

        specified_time = float(hora)*3600.0 + float(minuto)*60.0 + float(segundo)

        print("Tempo Atual: " + tempo_atual + "       Tempo Especificado: " + hora + ":" + minuto + ":" + segundo)

        if self.time_step is None and tempo_atual_sec != specified_time:  # Na primeira simulação de todas
            # print("Simular - Fluxo Inicial")
            return True
        elif self.time_step is not None and (tempo_atual_sec - self.time_step) != specified_time:
            # print("Simular - Fluxo ao longo do processo")
            return True
        else:
            # print("Não Simular!")
            return False

    def solve_time(self, hora, minuto, segundo):
        """Método que comanda a simulação de um novo fluxo de potência no OpenDSS-G."""

        try:
            tempo_hora = float(hora) + float(minuto) / 60.0 + float(segundo) / 3600.0

            if self.is_first_simulation:

                self.initial_time_step = 0.1
                # necessário definir o modo de simulação e passo de tempo
                self.send_dss_command("set mode=daily")
                self.send_dss_command("set controlmode=static")
                self.send_dss_command("set number=1")

                self.send_dss_command("set stepsize=" + str(self.initial_time_step))  # na primeira solução, um stepsize bem baixo só para o relógio do OpenDSS-G não avançar muito.
                self.send_dss_command("set hour=" + str(tempo_hora))  # seta o tempo para o horário definido no inócio da simulação.
                self.is_first_simulation = False
            else:
                if self.time_step is None:  # se ainda não foi definido
                    self.time_step = (float(hora)-self.current_time[0])*3600.0 + (float(minuto)-self.current_time[1])*60.0 + (float(segundo) - self.current_time[2]) \
                                    + self.initial_time_step  # Passo de tempo do Módulo Central em segundos
                    self.send_dss_command("set stepsize=" + str(self.time_step))
                    self.send_dss_command("set hour=" + str(hora))  # seta o tempo para o horário recebido
                    self.send_dss_command("set sec=" + str(float(minuto)*60.0 + float(segundo)))

                    # Uma vez definido, não precisamos alterar o time_step (pois todos os eventos cadastrados no Módulo Central acontecem em instantes de tempo
                    # múltiplos do passo de tempo

                else:
                    # Checar se corresponde a uma nova simulação. Isto é, se o tempo especificado é menor que o atual.
                    tempo_seg = float(hora) * 3600.0 + float(minuto) * 60.0 + float(segundo)
                    # tempo_atual_sec = float(self.get_simulation_time('s'))
                    tempo_atual_sec = self.get_simulation_time('s')
                    if tempo_seg < (tempo_atual_sec - self.time_step):
                        self.send_dss_command("set hour=" + str(hora))  # seta o tempo para o horário recebido
                        self.send_dss_command("set sec=" + str(float(minuto) * 60.0 + float(segundo)))

            self.step_in()

            # self.send_dss_command("Solve")

        except Exception as e:
            print(f'Erro ({e}).')
            raise e
