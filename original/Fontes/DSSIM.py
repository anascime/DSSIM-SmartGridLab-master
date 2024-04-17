###  # -*- coding: iso-8859-15 -*-

"""

Classe respons�vel por executar a comunica��o do aplicativo em Python com o DSSim.
Ela cont�m m�todos que tornam a comunica��o com o DSSim mais leg�vel.
Novos m�todos devem ser implementado na medida em que mais informa��es da simula��o
no DSSim s�o necess�rias.

"""

__author__ = 'CelsoRocha' and 'Paulo Radatz'

import socket
import pandas as pd
import ctypes
import time
import datetime

from Auxiliar import *


class DSSim:

    fault_dictionary = {0: [".1.2.3", ".0.0.0", 3], 1: [".2", ".3", 1], 2: [".1", ".0", 1], 3: [".1", "0", 1],
                        4: [".2.3", ".0.0", 2]}
    # 0: Falta Trif�sica (abc)
    # 1: Falta Dupla-Fase (bc)
    # 2: Falta Fase-Terra (at)
    # 3: Falta Fase-Terra com Imped�ncia de Aterramento (at)
    # 4: Falta Dupla-Fase-Terra (bct)

    def __init__(self, TCP_IP, TCP_PORT, BUFFER_SIZE, Form):
        """ Cria um novo objeto DSSIM """

        self.TCP_IP = TCP_IP                                    # IP do Servidor criado pelo DSSIM
        self.TCP_PORT = TCP_PORT                                # Porta onde o servidor se encontra
        self.BUFFER_SIZE = BUFFER_SIZE
        self.form = Form

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria o socket
        self.frame_guids = None                                     # Frame que armazena o nome de todos os elementos da rede
        self.frame_buses = None                                     # Frame que armazena o nome de todas as barras da rede

        # Inicializa algumas vari�veis importantes para controle da simula��o no OpenDSS-G
        self.is_first_simulation = True                          # Flag que indica se alguma simula��o j� foi feita
        self.initial_time_step = None                            # Passo de Tempo Inicial da Simula��o no OpenDSS-G
        self.current_time = [0]*3                                # Armazena o �ltimo instante de tempo
        self.time_step = None                                    # Armazena o passo de tempo de simula��o definido no M�dulo Central

    # #--------------------------------------------------------------------# #
    #                        M�todos do Tipo "Get"
    # #--------------------------------------------------------------------# #

    def get_simulation_time(self, unidade):
        """ M�todo que retorna o tempo da simula��o
        A unidade pode ser 's', 'm', 'h' ou 'd'  """

        if unidade == 's' or unidade == 'm' or unidade == 'h':
            message = "01;"
        elif unidade == 'd':
            message = "02;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")

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
        """ M�todo que retorna a tens�o em todas os n�s do circuito """
        # Op��es:
        #   "pu": retorna uma lista com a magnitude da tens�o em todos os n�s em pu
        #   "kV": retorna uma lista com a magnitude e a fase da tens�o em todos os n�s em kV, no formato retangular

        if unidade == 'pu':
            message = "03;"

        elif unidade == 'kV':
            message = "04;"    # N�o entendi o que est� acontecendo aqui

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        # print data
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")

        tamanho = int(data[:8], 16) + 8

        lista = data[8:tamanho].split("\t")        # Separa��o utilizada � um tab
        lista = [float(x) for x in lista]   # Converte para Float

        return lista

    def get_last_event(self):
        """ M�todo que retorna o �ltimo evento realizado no DSSim """

        # Op��es conhecidas at� o momento:
        #   "Switch": quando o estado de alguma chave � alterado na interface
        #   "Fault": quando uma falta � aplicada na interface
        #   "Clear Fault": quando o usu�rio selciona o bot�o "Clear faults" no DSSim

        message = "35;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")

        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def get_bus_voltages(self, bus_name):
        """ M�todo que recebe o nome de uma barra e retorna as tens�es nodais Van, Vbn, Vcn e Vnt"""

        self.send_dss_command("set bus=" + bus_name)
        voltages = self.send_dss_command("voltages")
        # print voltages
        voltages = voltages.replace(" ", "")  # remove os espa�os em branco
        voltages = voltages[:-1]  # deleta o �ltimo caractere, uma v�rgula extra
        voltages = voltages.split(",")
        voltages = [float(x) for x in voltages]  # Converte para Float

        return voltages

    def get_elem_voltages(self, element_name, terminal):
        """ M�todo que recebe o nome de um elemento e retorna as tens�es nodais nos seus terminais"""
        self.send_dss_command("select " + element_name + " " + "terminal = " + str(terminal))
        voltages = self.send_dss_command("voltages")
        # print voltages
        voltages = voltages.replace(" ", "")  # remove os espa�os em branco
        voltages = voltages[:-1]  # deleta o �ltimo caractere, uma v�rgula extra
        voltages = voltages.split(",")
        voltages = [float(x) for x in voltages]  # Converte para Float

        # Sempre temos que retornar 4 valores de tens�o de fase para o M�dulo Central.
        while len(voltages) < 9:
            voltages.append(float(0.0))  # Enviar zero nas outras fases

        return voltages

    def get_elem_currents(self, element_name):
        """ M�todo que recebe o nome completo de um PDE ou PCE do OpenDSS e retorna as correntes que entram em cada um
        dos seus n�s, dos dois terminais"""

        self.send_dss_command("select " + element_name)
        currents = self.send_dss_command("currents")
        # print currents
        currents = currents.replace(" ", "")  # remove os espa�os em branco
        currents = currents[:-1]  # deleta o �ltimo caractere, uma v�rgula extra
        currents = currents.split(",")
        currents = [float(x) for x in currents]  # Converte para Float

        # Sempre temos que retornar 4 valores de corrente de fase para o M�dulo Central.
        while len(currents) < 9:
            currents.append(float(0.0))  # Enviar zero nas outras fases

        return currents

    def get_switch_state(self, switch_name):
        """ M�todo que recebe o nome de um switch e retorna o seu estado """

        message = "19;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")

        tamanho = int(data[:8], 16) + 8
        lista = data[8:tamanho]
        # print lista
        lista = lista[:-1].split()  # deleta �ltima linha, separa as duas linhas restantes e separa por tabula��o
        print lista
        if switch_name in lista:
            index = lista.index(switch_name)
            return lista[index - len(lista)/2]
        else:
            return None

    def get_switch_lock(self, switch_control_name):
        """ M�todo que recebe o nome de um switchcontrol e verifica se ele est� travado ou n�o."""

        lock = self.send_dss_command("? swtcontrol." + switch_control_name + ".lock") # Yes or No
        if lock == "No":
            return 0
        elif lock == "Yes":
            return 1

    def get_total_powers(self, element_name, terminal):
        """ M�todo que recebe o nome de um element no OpenDSS e retorna a pot�ncia ativa e reativa total do elemento """
        # Se o elemento possuir n fases, a pot�ncia total ser� P1+P2+...+Pn. O mesmo vale para Q.
        # terminal pode ser: 1 , 2 ou None. Se None, o resultado � uma tupla com (P1,Q1,P2,Q2)
        self.send_dss_command("select " + element_name)
        powers = self.send_dss_command("powers")
        # print powers
        powers = powers.replace(" ", "")  # remove os espa�os em branco
        powers = powers[:-1]  # deleta o �ltimo caractere, uma v�rgula extra
        powers = powers.split(",")
        powers = [float(x) for x in powers]  # Converte para Float

        classe_elemento = element_name.split(".")[0]

        if classe_elemento.lower() == ("load" or "capacitor" or "reactor"):
            n_phases = len(powers)/2
            terminal = 1  # for�a leitura da pot�cia do �nico terminal que tem
        else:
            n_phases = len(powers) / 4

        p_total_1 = 0
        q_total_1 = 0
        p_total_2 = 0
        q_total_2 = 0

        for i in range(n_phases):
            p_total_1 = powers[2 * i] + p_total_1
            q_total_1 = powers[2 * i + 1] + q_total_1

            if classe_elemento.lower() != ("load" or "capacitor" or "reactor"):
                p_total_2 = powers[2 * i + n_phases * 2] + p_total_2
                q_total_2 = powers[2 * i + 1 + n_phases * 2] + q_total_2

        if terminal == 1:
            return p_total_1, q_total_1

        elif terminal == 2:
            return p_total_2, q_total_2

        elif terminal is None:
            return p_total_1, q_total_1, p_total_2, q_total_2

    def get_phase_powers(self, element_name, terminal, phase):
        """ M�todo que recebe o nome de um elemento no OpenDSS, o terminal e um n� e retorna a pot�ncia ativa e reativa
        que entram nesse n� """

        self.send_dss_command("select " + element_name)
        powers = self.send_dss_command("powers")
        # print powers
        powers = powers.replace(" ", "")  # remove os espa�os em branco
        powers = powers[:-1]  # deleta o �ltimo caractere, uma v�rgula extra
        powers = powers.split(",")
        powers = [float(x) for x in powers]  # Converte para Float

        n_phases = len(powers)/4

        if phase > n_phases:
            ctypes.windll.user32.MessageBoxW(0, u"O elemento " + '"{}"'.format(element_name) + u" possui somente " + str(n_phases) +
            u" fases. Fase " + str(phase) + u" solicitada.", u"Conex�o DSSimPC-v2.0", 0)
            return None
        else:
            return powers[6*(terminal-1) + 2*(phase-1)], powers[6*(terminal-1) + 2*(phase-1) + 1]   # P, Q

    def get_transformer_tap(self, transformer_name, winding):
        """ M�todo que recebe o nome de um transformador e um enrolamento e retorna o tap atual desse enrolamento em pu e em passos """

        taps_array = self.send_dss_command("? " + transformer_name + ".taps")
        taps_array = taps_array[1:-3]  # deleta [ ....  , ]
        taps_array = taps_array.split(",")
        taps_array = [float(x) for x in taps_array]

        if winding > len(taps_array):
            ctypes.windll.user32.MessageBoxW(0, u"O transformador " + '"{}"'.format(transformer_name) + u" possui somente " + str(len(taps_array)) +
                                             u" enrolamentos. Tap do enrolamento " + str(winding) + u" solicitado.", u"Conex�o DSSimPC-v2.0", 0)
            return None
        else:

            # Convertendo para passos
            maxtap = float(self.send_dss_command("? " + transformer_name + ".maxtap"))
            mintap = float(self.send_dss_command("? " + transformer_name + ".mintap"))
            num_taps = float(self.send_dss_command("? " + transformer_name + ".numtaps"))

            step_pu = (maxtap - mintap) / num_taps

            step = (taps_array[winding-1] - 1.0) / step_pu

        return taps_array[winding-1], int(round(step))   # int(-1.0) estava retornando 0 (int) ao inv�s de -1 (int)

    def get_capacitor_state(self, capacitor_name):
        """ M�todo que recebe o nome de um capacitor e retorna o seu estado """

        state = self.send_dss_command("? " + capacitor_name + ".states")
        state = state[2]
        return int(state)

    def get_capacitor_kvar(self, capacitor_name):
        """ M�todo que recebe o nome de um capacitor e retorna o valor de sua pot�ncia reativa """

        kvar = self.send_dss_command("? " + capacitor_name + ".kvar")
        kvar = kvar[1:-1]
        return float(kvar)

    def get_num_phases(self, element_name):
        """ M�todo que recebe o nome de um elemento e retorna a quantidade de fases do mesmo """

        phases = self.send_dss_command("? " + element_name + ".phases")
        return int(phases)

    # #--------------------------------------------------------------------# #
    #                        M�todos do Tipo "Set"
    # #--------------------------------------------------------------------# #

    def set_switch_state(self, nome, status):
        """ M�todo que abre/fecha um switch """

        # identifica o tamanho da mensagem
        tamanho = len(nome) + 2  # + 1 pelo sinal de igualdade e + 1 pelo status
        tamanho_hex = "%04x" % tamanho

        message = "18;" + tamanho_hex + nome + "=" + str(status) + ";"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        time.sleep(0.1)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")

        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def set_new_bus_fault(self, nome_barra, tipo, resistencia):
        """ M�todo que aplica uma falta em uma dada barra com uma dada resist�ncia de falta.
        O tipo de falta � dado de acordo com o dicion�rio DSSim.fault_dictionary."""

        if resistencia is None:
            resistencia = 0.0001  # valor default do OpenDSS

        resposta = self.send_dss_command("new fault." + nome_barra + " phases = " + str(DSSim.fault_dictionary[tipo][2]) + " bus1= " +
                                         nome_barra + DSSim.fault_dictionary[tipo][0] + " bus2=" +
                                         nome_barra + DSSim.fault_dictionary[tipo][1] + " r = " + resistencia)
        return resposta

    def set_new_line_fault(self, nome_linha, distancia_pct, tipo, resistencia):
        """ M�todo que aplica uma falta no meio de um trecho de linha."""

        # 1�: Armazena dados necess�rios da linha
        length_original = float(self.send_dss_command("? " + nome_linha + ".length"))
        bus1_original_completo = self.send_dss_command("? " + nome_linha + ".bus1")
        bus1_original_nome = bus1_original_completo.split(".", 1)[0]
        bus1_original_phases_string = bus1_original_completo.split(".", 1)[1]
        bus2_original_completo = self.send_dss_command("? " + nome_linha + ".bus2")

        # 2�: Cria duas novas linhas em s�rie cujo comprimento total � igual ao comprimento da linha original
        self.send_dss_command("new " + nome_linha + "_1 like=" + nome_linha.split(".", 1)[1] + " bus1=" + bus1_original_completo + " bus2="
                              + bus1_original_nome + "_aux." + bus1_original_phases_string + " length=" + str(length_original*distancia_pct))
        self.send_dss_command("new " + nome_linha + "_2 like=" + nome_linha.split(".", 1)[1] + " bus1=" + bus1_original_nome + "_aux." + bus1_original_phases_string
                              + " length=" + str(length_original * (1-distancia_pct)))

        # 3�: Desativa linha original
        self.send_dss_command(nome_linha + ".enabled=False")

        # 4�: Aplica a falta na barra auxiliar
        resposta = self.set_new_bus_fault(bus1_original_nome + "_aux", tipo, resistencia)

        return resposta

    def set_transformer_tap(self, transformer_name, winding, tap):
        """ M�todo que recebe o nome de um transformador, um enrolamento e um tap e seta o valor do tap. """

        num_windings = int(self.send_dss_command("? " + transformer_name + ".windings"))

        if winding > num_windings:
            ctypes.windll.user32.MessageBoxW(0, u"O transformador " + '"{}"'.format(transformer_name) + u" possui somente " + str(num_windings) +
                                             u" enrolamentos. Tap do enrolamento " + str(winding) + u" solicitado.", u"Conex�o DSSimPC-v2.0", 0)
            return None

        self.send_dss_command(transformer_name + ".wdg=" + str(winding) + " tap=" + str(tap))

    def set_capacitor_kvar(self, nome_capacitor, kvar):

        self.send_dss_command(nome_capacitor + ".kvar=" + str(kvar))

    def set_capacitor_state(self, nome_capacitor, state):
        self.send_dss_command(nome_capacitor + ".states=" + str(state))

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

    # #--------------------------------------------------------------------# #
    #                   M�todos de Interface com o MC
    # #--------------------------------------------------------------------# #

    def retorna_id(self, codigo_equipamento_sinap, tipo_equipamento):
        """ M�todo que recebe o c�digo de um equipamento do Sinap e retorna o seu ID"""
        if self.frame_guids is not None:
            if tipo_equipamento is not "1":  # Se n�o for Barra
                id = int(self.frame_guids.loc[(self.frame_guids["Codigo Sinap"] == codigo_equipamento_sinap.lower()), ["Id Sinap"]].values[0][0])
            else:
                id = int(self.frame_buses.loc[(self.frame_buses["Codigo Sinap"] == codigo_equipamento_sinap.lower()), ["Id Sinap"]].values[0][0])
            return id
        else:
            print "Frame com nomes n�o armazenado!"

    def get_nome_opendss(self, id_equipamento, tipo=None):
        """ M�todo que recebe um ID de um equipamento do Sinap e retorna o nome completo (incluindo a sua classe) do equipamento no OpenDSS"""
        if tipo is None:
            nome_opendss = self.frame_guids.loc[(self.frame_guids["Id Sinap"] == id_equipamento), ["Nome Completo"]].values[0][0]
        else:  # Caso seja Barra
            nome_opendss = self.frame_buses.loc[(self.frame_buses["Id Sinap"] == id_equipamento), ["Nome Completo"]].values[0][0]
        return nome_opendss

    def get_last_simulation_type(self):    # Testa!!
        """ M�todo que identifica se o �ltimo tipo de simula��o realizado pelo DSSim � do tipo Fluxo ou Curto.
        A l�gica ser� a seguinte: se houver um elemento fault na rede, ser� do tipo Curto. Caso contr�rio, tipo Fluxo.

        Para identificar se h� uma falta na rede utilizando comandos do OpenDSS, vamos utilizar o comando
        Export GUIDS. Se um elemento da classe "Fault" for identificado e se a sua propriedade "enabled" for "true",
        o resultado ser� "Curto", caso contr�rio, ser� "Fluxo"."""

        self.armazena_nomes_elementos()
        try:

            nome_falta = self.frame_guids.loc[(self.frame_guids["Tipo Elemento"] == "Fault"), ["Nome OpenDSS"]]["Nome OpenDSS"].tolist()
            if len(nome_falta) == 0:
                # print "Fluxo"
                return "Fluxo"
            else:
                for i in range(len(nome_falta)):
                    if self.send_dss_command("? fault." + nome_falta[i] + ".enabled") == 'true':
                        # print "Curto"
                        return "Curto"
                    else:
                        # print "Fluxo, falta disabled"
                        return "Fluxo"
        except:  # Se n�o encontrar nenhum elemento com a classe
            # print "Fluxo"
            return "Fluxo"

    def varia_tap(self, transformer_name, variacao_tap):
        """ M�todo que recebe o nome de um trafo e uma variacao de tap e varia o tap do respectivo trafo"""

        # O tap no OpenDSS � especificado em pu. Por isso, precisamos converter para pu.
        # Convertendo para passos
        maxtap = float(self.send_dss_command("? " + transformer_name + ".maxtap"))
        mintap = float(self.send_dss_command("? " + transformer_name + ".mintap"))
        num_taps = float(self.send_dss_command("? " + transformer_name + ".numtaps"))

        step_pu = (maxtap - mintap) / num_taps

        self.send_dss_command(transformer_name + ".wdg=1")  # Ativa o primeiro enrolamento
        kv1 = self.send_dss_command("? " + transformer_name + ".kv")

        self.send_dss_command(transformer_name + ".wdg=2")  # Ativa o segundo enrolamento
        kv2 = self.send_dss_command("? " + transformer_name + ".kv")

        # De acordo com o protocolo, o tap a ser variado deve ser o de enrolamento com maior tens�o nominal
        if kv1 > kv2:
            wdg = 1
        else:
            wdg = 2

        self.send_dss_command(transformer_name + ".wdg=" + str(wdg))
        tap_atual = self.send_dss_command("? " + transformer_name + ".tap")

        # Calcula novo tap em pu
        novo_tap = float(tap_atual) + variacao_tap*step_pu

        # Seta novo tap
        self.send_dss_command(transformer_name + ".tap=" + str(novo_tap))

        return "OK"

    # #--------------------------------------------------------------------# #
    #                        M�todos Auxiliares
    # #--------------------------------------------------------------------# #

    def send_dss_command(self, comando):
        """ M�todo que executa um comando na linguagem de programa��o do OpenDSS """

        # identifica o tamanho da mensagem
        tamanho = len(comando)
        tamanho_hex = "%04x" % tamanho  # converte "tamanho" para hexadecimal com 4 d�gitos (por algum motivo, s� funciona quando tem 4 d�gitos. Se colocar com 8, n�o funciona.

        message = "25;" + tamanho_hex + comando + ";"
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")
        tamanho = int(data[:8], 16) + 8

        return data[8:tamanho]

    def refresh_gui(self, tipo):
        """ M�todo que atualiza a GUI do DSSim """
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
        self.s.sendall(message)
        time.sleep(0.1)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")
        tamanho = int(data[:8], 16) + 8

        return data[8:tamanho]

    def step_in(self):
        """ M�todo que avan�a um passo de tempo na simula��o do DSSim """

        message = "23;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")
        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def end_simulation(self):
        """ M�todo que for�a o fim da simula��o. Usar ao final da execu��o de v�rios step_in. """

        message = "24;"

        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.ENV, message + "\n\n")
        self.s.sendall(message)

        data = self.s.recv(self.BUFFER_SIZE)
        if self.form is not None:
            self.form.escreve_mensagem(Conexao.DSSIM_CON, Tipo_Conexao.REC, data + "\n\n")

        tamanho = int(data[:8], 16) + 8
        return data[8:tamanho]

    def close(self):
        """ M�todo que fecha a conex�o com o servidor TCP """
        self.s.close()

    def clear_fault(self, nome_barra=None, nome_linha=None):
        """ M�todo que retira uma falta e retorna o circuito � condi��o inicial de acordo com o tipo de falta (em Barra
        ou em Trecho). Declarar somente um dos dois.
        Se nenhum argumento � passado, devemos identificar todas as faltas na rede e elimin�-las, retornando a rede para o seu estado inicial."""

        if (nome_barra is not None) and (nome_linha is None):  # Falta em Barra
            resposta = self.send_dss_command("fault." + nome_barra + ".enabled=False")

        elif (nome_barra is None) and (nome_linha is not None):  # Falta em Trecho
            self.send_dss_command(nome_linha + "_1.enabled=False")  # desativa primeira linha
            self.send_dss_command(nome_linha + "_2.enabled=False")  # desativa segunda linha

            # desativa falta
            barra_falta = self.send_dss_command("? " + nome_linha + ".bus1") + "_aux"
            self.send_dss_command("fault." + barra_falta + ".enabled=False")

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
            print u"Comunica��o Estabelecida com sucesso!"
            return True
        else:
            ctypes.windll.user32.MessageBoxW(0, u"Conex�o TCP n�o estabelecida! Verifique os dados da conex�o com o "
                                                u"servidor!", u"Conex�o DSSimPC-v2.0", 0)
            return False
        # self.s.close()   # � necess�rio abrir e fechar a conex�o a todo instante ?

    def armazena_path(self):
        """ M�todo que armazena o caminho dos dados do DSSim. Ser� utilizado posteriormente quando formos ler os
        arquivos gerados por comandos "export" """
        self.data_path = self.send_dss_command("get datapath")
        print self.data_path

    def armazena_nomes_elementos(self):
        """ M�todo que exporta as GUIDs de cada um dos elementos da rede. Usaremos este m�todo para
         armazenar os nomes de todos os elementos em um dataframe somente uma vez"""
        self.send_dss_command("export guids")     # Verificar pq n�o est� retornando o endere�o do arquivo exportado
        casename = self.send_dss_command("get casename")
        nomes = ["Completo"]
        self.frame_guids = pd.read_csv(self.data_path + "/" + casename + "_EXP_GUIDS.CSV", engine='python', names=nomes)

        self.frame_guids["Nome Completo"] = self.frame_guids["Completo"].str.split(' ').str.get(0)
        self.frame_guids["Tipo Elemento"] = self.frame_guids["Nome Completo"].str.split('.').str.get(0)
        self.frame_guids["Nome OpenDSS"] = self.frame_guids["Nome Completo"].str.split('.').str.get(1)
        self.frame_guids["Codigo Sinap"] = self.frame_guids["Nome OpenDSS"].str.split('_id').str.get(0)
        self.frame_guids["Id Sinap"] = self.frame_guids["Nome OpenDSS"].str.split('_id').str.get(1)

        self.frame_guids.drop("Completo", axis=1, inplace=True)

        # print self.frame_guids.head()

    def armazena_nomes_barras(self):
        """ M�todo que exporta o arquivo de Coordenadas das Barras de cada um dos elementos da rede. Usaremos este m�todo para
         armazenar os nomes de todas as barras em um data frame somente uma vez"""

        self.send_dss_command("export buscoords")  # Verificar pq n�o est� retornando o endere�o do arquivo exportado
        casename = self.send_dss_command("get casename")
        nomes = ["Nome Completo", "X", "Y"]
        self.frame_buses = pd.read_csv(self.data_path + "/" + casename + "_EXP_BUSCOORDS.CSV", engine='python', names=nomes, usecols=["Nome Completo"])

        self.frame_buses["Codigo Sinap"] = self.frame_buses["Nome Completo"].str.split('_ID').str.get(0)
        self.frame_buses["Id Sinap"] = self.frame_buses["Nome Completo"].str.split('_ID').str.get(1)

        # print self.frame_buses.head()

    def check_sim_needed(self, hora, minuto, segundo):
        """ Esse m�todo faz uma checagem se � preciso simular um novo passo de simula��o no OpenDSS-G ou n�o.
        � preciso simular se o tempo especificado � diferente do �ltimo simulado. Caso contr�rio, checar se houve
        alguma altera��o na rede que exija uma atualiza��o do fluxo de pot�ncia."""

        tempo_atual_sec = float(self.get_simulation_time('s'))
        tempo_atual = str(datetime.timedelta(seconds=tempo_atual_sec))  # datetime
        self.current_time[0] = float(tempo_atual.split(":")[0])
        self.current_time[1] = float(tempo_atual.split(":")[1])
        self.current_time[2] = float(tempo_atual.split(":")[2])

        specified_time = float(hora)*3600.0 + float(minuto)*60.0 + float(segundo)

        # print "Tempo Atual: " + tempo_atual + "       Tempo Especificado: " + hora + ":" + minuto + ":" + segundo

        if self.time_step is None and tempo_atual_sec != specified_time:  # Na primeira simula��o de todas
            # print u"Simular - Fluxo Inicial"
            return True
        elif self.time_step is not None and (tempo_atual_sec - self.time_step) != specified_time:
            # print u"Simular - Fluxo ao longo do processo"
            return True
        else:
            # print u"N�o Simular!"
            return False

    def solve_time(self, hora, minuto, segundo):
        """ M�todo que comanda a simula��o de um novo fluxo de pot�ncia no OpenDSS-G."""

        tempo_hora = float(hora) + float(minuto) / 60.0 + float(segundo) / 3600.0

        if self.is_first_simulation:

            self.initial_time_step = 0.1
            # necess�rio definir o modo de simula��o e passo de tempo
            self.send_dss_command("set mode=daily")
            self.send_dss_command("set controlmode=static")
            self.send_dss_command("set number=1")

            self.send_dss_command("set stepsize=" + str(self.initial_time_step))  # na primeira solu��o, um stepsize bem baixo s� para o rel�gio do OpenDSS-G n�o avan�ar muito.
            self.send_dss_command("set hour=" + str(tempo_hora))  # seta o tempo para o hor�rio definido no in�cio da simula��o.
            self.is_first_simulation = False
        else:
            if self.time_step is None:  # se ainda n�o foi definido
                self.time_step = (float(hora)-self.current_time[0])*3600.0 + (float(minuto)-self.current_time[1])*60.0 + (float(segundo) - self.current_time[2]) \
                                 + self.initial_time_step  # Passo de tempo do M�dulo Central em segundos
                self.send_dss_command("set stepsize=" + str(self.time_step))
                self.send_dss_command("set hour=" + str(hora))  # seta o tempo para o hor�rio recebido
                self.send_dss_command("set sec=" + str(float(minuto)*60.0 + float(segundo)))

                # Uma vez definido, n�o precisamos alterar o time_step (pois todos os eventos cadastrados no M�dulo Central acontecem em instantes de tempo
                # m�ltiplos do passo de tempo

            else:
                # Checar se corresponde a uma nova simula��o. Isto �, se o tempo especificado � menor que o atual.
                tempo_seg = float(hora) * 3600.0 + float(minuto) * 60.0 + float(segundo)
                tempo_atual_sec = float(self.get_simulation_time('s'))
                if tempo_seg < (tempo_atual_sec - self.time_step):
                    self.send_dss_command("set hour=" + str(hora))  # seta o tempo para o hor�rio recebido
                    self.send_dss_command("set sec=" + str(float(minuto) * 60.0 + float(segundo)))

        self.step_in()

        # self.send_dss_command("Solve")
