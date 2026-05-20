# -*- coding: iso-8859-15 -*-

"""

Classe respons�vel por executar a comunica��o do aplicativo em Python com o MC.
Ela cont�m m�todos que emulam o servidor do SINAP, que escuta �s solicita��es
do M�dulo Central.

"""

__author__ = 'CelsoRocha' and 'Paulo Radatz'

import socket
import ctypes
import time
import struct
import datetime
from Auxiliar import *


class MC:

    def __init__(self, form, TCP_PORT, TCP_HOST = '', dssim_obj = None):
        """ Cria um novo objeto MC """

        self.TCP_HOST = TCP_HOST  # O que significa o HOST exatamente? Uma string vazia significa que o servidor
        # pode escutar conex�es oriundas de outros computadores na rede tamb�m. "127.0.0.1" significa que
        # o servidor escutar� somente conex�es oriundas da pr�pria m�quina.
        self.TCP_PORT = TCP_PORT  # Porta onde o servidor se encontrar�

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria o socket
        self.dssim_obj = dssim_obj  # refer�ncia para o objeto DSSim
        self.form = form  # refer�ncia para o objeto formul�rio principal

        self.mensagem = [struct.pack('<Q', 0)[0]]*16384    # igual a ['\x00']
        self.copia_mensagem = [struct.pack('<Q', 0)[0]]*16384

    # #--------------------------------------------------------------------# #
    #                        M�todos Principais
    # #--------------------------------------------------------------------# #

    def process_data(self, msg):
        """ M�todo respons�vel por processar a mensagem recebida pelo cliente MC,
         chamando a respectiva fun��o na comunica��o com o servidor DSSim e
         enviando a devida mensagem de volta ao cliente MC."""

        # tamanho = len(data)
        # funcao = ord(data[0])
        # O comprimento de "data" � exatamente o comprimento da mensagem. No print data,
        # parece que a mensagem � bem menor, mas isso � porque v�rios "chars" enviados
        # pelo C++ s�o nulos, o que vira um char "", que na hora do print, n�o aparece.

        message = reconstroi_msg(msg)
        self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.REC, message + "\n\n")

        msg_dividida = message.split(";")
        funcao = msg_dividida[0]

        if self.dssim_obj is not None:  # Verifica se existe conex�o com o DSSim
            if funcao == "99":  # Retorna ID do equipamento por meio de c�digo
                codigo_equipamento = msg_dividida[-2]
                tipo_equipamento = msg_dividida[5]
                id_equipamento = self.dssim_obj.retorna_id(codigo_equipamento, tipo_equipamento)  # int

                qtde_bytes = 43   # Usando o mesmo valor definido no C++ builder quando a fun��o 99 � enviada para o Simulador.
                msg_retornada = [chr(0)]*qtde_bytes
                now = datetime.datetime.now()

                msg_retornada[0] = chr(int(funcao))
                msg_retornada[1] = chr(qtde_bytes)
                msg_retornada[2] = chr(0)
                msg_retornada[3] = chr(now.hour)  # verificar se a hpra do sistema atual ou a hora recebida na mensagem
                msg_retornada[4] = chr(now.minute)
                msg_retornada[5] = chr(now.second)
                msg_retornada[6] = chr(int(tipo_equipamento))

                # Id do equipamento Convertendo o valor do ID para 4 bytes segundo o formato Little Endian
                msg_retornada[7] = struct.pack('<Q', id_equipamento)[0]
                msg_retornada[8] = struct.pack('<Q', id_equipamento)[1]
                msg_retornada[9] = struct.pack('<Q', id_equipamento)[2]
                msg_retornada[10] = struct.pack('<Q', id_equipamento)[3]

                # C�digo do Equipamento
                for i in range(11, 11 + len(codigo_equipamento)):
                    msg_retornada[i] = codigo_equipamento[i-11]

                # Mensagem Display
                msg = funcao + ";" + str(qtde_bytes) + ";" + str(now.hour) + ";" + str(now.minute) + ";" + str(now.second) + ";" + tipo_equipamento + ";" + str(id_equipamento) + ";" + codigo_equipamento + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "1":  # MC solicita registros de equipamentos. Devemos retornar a fun��o 02 do protocolo.

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                if self.dssim_obj.check_sim_needed(hora, minuto, segundo):
                    # Simula
                    self.dssim_obj.solve_time(hora, minuto, segundo)

                count = 0
                lista_equipamentos = []  # lista de tuplas
                for i in range(len(msg_dividida)-1):  # -1 porque tem um espa�o a mais que vem por causa do split(";")
                    if i == (5 + count*2):
                            tipo_equipamento = msg_dividida[i]
                            print tipo_equipamento
                            id_equipamento = msg_dividida[i+1]
                            print id_equipamento
                            count = count + 1
                            lista_equipamentos.append((tipo_equipamento, id_equipamento))

                # Retornar a fun��o 02:
                    # Trata-se de uma resposta para a fun��o 1, na qual s�o enviados todos os registros pertinentes aos
                    # equipamentos solicitados, na ordem de solicita��o e referidos ao hor�rio definido na solicita��o.
                    # Cada informa��o de grandeza � dada por 8 bytes, sendo 4 bytes para o m�dulo e 4 bytes para a fase (em graus).

                    # Os registros de grandezas enviados pela fun��o 2 est�o relacionados � simula��o corrente do Sinap, ou seja,
                    # fluxo de carga ou curto-circuito.

                dic_tipo_registros = {"1": 32, "2": 32, "3": 136, "4": 129, "5": 129, "6": 48, "7": 37, "8": 66, "9": 72, "10": 72, "12": 68}

                # OBS: Registro do equipamento tipo Chave: N�o estamos considerando, os 4 bytes de "Id da Barra de Refer�ncia" porque
                # o M�dulo Central que eu estou utilizando n�o recebe ele. Nem sabemos que par�metro � esse tamb�m (Por isso 132)
                # ATUALIZA��O 24/04/2018: A vers�o "ModuloCentralXE7_Rev2_Sinap20170725" do M�dulo Central espera na leitura da fun��o
                # 2 esses 4 bytes. Vamos assumir como sendo a barra 1 da chave (Agora, 136 bytes)

                qtde_bytes = 7  # Come�a sempre com 7 bytes fixos.
                for i in range(len(lista_equipamentos)):
                    qtde_bytes = qtde_bytes + 5 + dic_tipo_registros[lista_equipamentos[i][0]]

                # msg_retornada = [chr(0)] * qtde_bytes
                msg_retornada = [chr(0)] * 7  # 7 primeiros bytes, depois vamos concatenar
                # msg_retornada = []  # resolver problema aqui, na hora de montar a msg
                msg_retornada[0] = chr(2)
                msg_retornada[1] = struct.pack('<Q', qtde_bytes)[0]
                msg_retornada[2] = struct.pack('<Q', qtde_bytes)[1]
                msg_retornada[3] = chr(int(hora))
                msg_retornada[4] = chr(int(minuto))
                msg_retornada[5] = chr(int(segundo))

                tipo_calculo = self.dssim_obj.get_last_simulation_type()
                if tipo_calculo == "Fluxo":
                    msg_retornada[6] = chr(0)  # Fluxo. O que mandar aqui exatamente? # mandar o �ltimo tipo de simula��o enviado pelo dssim.
                else:  # "Curto"
                    msg_retornada[6] = chr(1)

                lista_equipamentos_todos = []

                for i in range(len(lista_equipamentos)):
                    tipo_equipamento = lista_equipamentos[i][0]
                    id_equipamento = lista_equipamentos[i][1]

                    equipamento = []

                    if i == 1:
                        print "oi"
                    equipamento.append(chr(int(tipo_equipamento)))  # Tipo
                    equipamento.append(struct.pack('<Q', int(id_equipamento))[0:4])  # Id

                    if tipo_equipamento == "1":  # Barra
                        nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento, "barra")
                        voltages = self.dssim_obj.get_bus_voltages(nome_opendss)  # salva array com registros

                        va = voltages[0]
                        va_angle = voltages[1]
                        vb = voltages[2]
                        vb_angle = voltages[3]
                        vc = voltages[4]
                        vc_angle = voltages[5]
                        vn = voltages[6]
                        vn_angle = voltages[7]

                        equipamento.append(struct.pack('<f', va)[0:4])        # M�dulo Fase A
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', vb)[0:4])        # M�dulo Fase B
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', vc)[0:4])        # M�dulo Fase C
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', vn)[0:4])        # M�dulo Neutro
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # �ngulo Neutro

                    elif tipo_equipamento == "2":  # Trecho

                        nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                        currents = self.dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros

                        ia = currents[0]
                        ia_angle = currents[1]
                        ib = currents[2]
                        ib_angle = currents[3]
                        ic = currents[4]
                        ic_angle = currents[5]
                        in_ = currents[6]  # in_
                        in_angle = currents[7]

                        equipamento.append(struct.pack('<f', ia)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # �ngulo Neutro

                    elif tipo_equipamento == "3":  # Chave

                        nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                        currents = self.dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros
                        voltages_1 = self.dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        voltages_2 = self.dssim_obj.get_elem_voltages(nome_opendss, 2)  # salva array com registros
                        powers_total = self.dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros
                        power_phase_a = self.dssim_obj.get_phase_powers(nome_opendss, 1, 1)  #< Cuidado aqui, precisamos verificar as fases dispon�veis antes...
                        power_phase_b = self.dssim_obj.get_phase_powers(nome_opendss, 1, 2)
                        power_phase_c = self.dssim_obj.get_phase_powers(nome_opendss, 1, 3)

                        va1 = voltages_1[0]
                        va1_angle = voltages_1[1]
                        vb1 = voltages_1[2]
                        vb1_angle = voltages_1[3]
                        vc1 = voltages_1[4]
                        vc1_angle = voltages_1[5]
                        vn1 = voltages_1[6]
                        vn1_angle = voltages_1[7]

                        equipamento.append(struct.pack('<f', va1)[0:4])  # M�dulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va1_angle)[0:4])  # �ngulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb1)[0:4])  # M�dulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb1_angle)[0:4])  # �ngulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc1)[0:4])  # M�dulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc1_angle)[0:4])  # �ngulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn1)[0:4])  # M�dulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn1_angle)[0:4])  # �ngulo Neutro - Terminal 1

                        va2 = voltages_2[0]
                        va2_angle = voltages_2[1]
                        vb2 = voltages_2[2]
                        vb2_angle = voltages_2[3]
                        vc2 = voltages_2[4]
                        vc2_angle = voltages_2[5]
                        vn2 = voltages_2[6]
                        vn2_angle = voltages_2[7]

                        equipamento.append(struct.pack('<f', va2)[0:4])  # M�dulo Fase A - Terminal 2
                        equipamento.append(struct.pack('<f', va2_angle)[0:4])  # �ngulo Fase - Terminal 2
                        equipamento.append(struct.pack('<f', vb2)[0:4])  # M�dulo Fase B - Terminal 2
                        equipamento.append(struct.pack('<f', vb2_angle)[0:4])  # �ngulo Fase B - Terminal 2
                        equipamento.append(struct.pack('<f', vc2)[0:4])  # M�dulo Fase C - Terminal 2
                        equipamento.append(struct.pack('<f', vc2_angle)[0:4])  # �ngulo Fase C - Terminal 2
                        equipamento.append(struct.pack('<f', vn2)[0:4])  # M�dulo Neutro - Terminal 2
                        equipamento.append(struct.pack('<f', vn2_angle)[0:4])  # �ngulo Neutro - Terminal 2

                        ia = currents[0]
                        ia_angle = currents[1]
                        ib = currents[2]
                        ib_angle = currents[3]
                        ic = currents[4]
                        ic_angle = currents[5]
                        in_ = currents[6]  # in_
                        in_angle = currents[7]

                        equipamento.append(struct.pack('<f', ia)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # �ngulo Neutro

                        switch_state = chr(int(self.dssim_obj.get_switch_state(nome_opendss.split(".")[1])))   # switch state n�o t� funcionando para a �ltima chave
                        equipamento.append(switch_state)
                        cbr = chr(int(0))
                        equipamento.append(cbr)
                        cbtl = chr(int(0))
                        equipamento.append(cbtl)
                        lockout = chr(int(self.dssim_obj.get_switch_lock(nome_opendss.split(".")[1]))) # checaaaar
                        equipamento.append(lockout)

                        # Em qual terminal?
                        p_3f = powers_total[0]/1000.0  # converter de kW para MW
                        q_3f = powers_total[1]/1000.0
                        p_a = power_phase_a[0]/1000.0
                        q_a = power_phase_a[1]/1000.0
                        p_b = power_phase_b[0]/1000.0
                        q_b = power_phase_b[1]/1000.0
                        p_c = power_phase_c[0]/1000.0
                        q_c = power_phase_c[1]/1000.0

                        equipamento.append(struct.pack('<f', p_3f)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', q_3f)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', p_a)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', q_a)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', p_b)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', q_b)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', p_c)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', q_c)[0:4])  # �ngulo Neutro

                        # Id da barra de refer�ncia (assumi como sendo a barra 1 da chave) Convertendo o valor do ID para 4 bytes segundo o formato Little Endian
                        barra_ref_nome = self.dssim_obj.send_dss_command("? " + nome_opendss + ".bus1")
                        id_barra_ref = int(barra_ref_nome.split("_id")[1].split(".")[0])
                        equipamento.append(struct.pack('<Q', id_barra_ref)[0])
                        equipamento.append(struct.pack('<Q', id_barra_ref)[1])
                        equipamento.append(struct.pack('<Q', id_barra_ref)[2])
                        equipamento.append(struct.pack('<Q', id_barra_ref)[3])

                    elif tipo_equipamento == "4" or tipo_equipamento == "5":  # Transformador ou Regulador de Tens�o

                        nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                        voltages_1 = self.dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        voltages_2 = self.dssim_obj.get_elem_voltages(nome_opendss, 2)  # salva array com registros
                        currents = self.dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros

                        va1 = voltages_1[0]
                        va1_angle = voltages_1[1]
                        vb1 = voltages_1[2]
                        vb1_angle = voltages_1[3]
                        vc1 = voltages_1[4]
                        vc1_angle = voltages_1[5]
                        # vn1 = voltages_1[6]
                        # vn1_angle = voltages_1[7]
                        vn1 = 0
                        vn1_angle = 0

                        equipamento.append(struct.pack('<f', va1)[0:4])  # M�dulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va1_angle)[0:4])  # �ngulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb1)[0:4])  # M�dulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb1_angle)[0:4])  # �ngulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc1)[0:4])  # M�dulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc1_angle)[0:4])  # �ngulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn1)[0:4])  # M�dulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn1_angle)[0:4])  # �ngulo Neutro - Terminal 1

                        va2 = voltages_2[0]
                        va2_angle = voltages_2[1]
                        vb2 = voltages_2[2]
                        vb2_angle = voltages_2[3]
                        vc2 = voltages_2[4]
                        vc2_angle = voltages_2[5]
                        # vn2 = voltages_2[6]
                        # vn2_angle = voltages_2[7]
                        vn2 = 0
                        vn2_angle = 0

                        equipamento.append(struct.pack('<f', va2)[0:4])  # M�dulo Fase A - Terminal 2
                        equipamento.append(struct.pack('<f', va2_angle)[0:4])  # �ngulo Fase - Terminal 2
                        equipamento.append(struct.pack('<f', vb2)[0:4])  # M�dulo Fase B - Terminal 2
                        equipamento.append(struct.pack('<f', vb2_angle)[0:4])  # �ngulo Fase B - Terminal 2
                        equipamento.append(struct.pack('<f', vc2)[0:4])  # M�dulo Fase C - Terminal 2
                        equipamento.append(struct.pack('<f', vc2_angle)[0:4])  # �ngulo Fase C - Terminal 2
                        equipamento.append(struct.pack('<f', vn2)[0:4])  # M�dulo Neutro - Terminal 2
                        equipamento.append(struct.pack('<f', vn2_angle)[0:4])  # �ngulo Neutro - Terminal 2

                        ia1 = currents[0]
                        ia1_angle = currents[1]
                        ib1 = currents[2]
                        ib1_angle = currents[3]
                        ic1 = currents[4]
                        ic1_angle = currents[5]
                        # in1_ = currents[6]  # in_
                        # in1_angle = currents[7]
                        in1_ = 0
                        in1_angle = 0

                        ia2 = currents[8]
                        ia2_angle = currents[9]
                        ib2 = currents[10]
                        ib2_angle = currents[11]
                        ic2 = currents[12]
                        ic2_angle = currents[13]
                        # in2_ = currents[14]  # in_
                        # in2_angle = currents[15]
                        in2_= 0
                        in2_angle = 0

                        equipamento.append(struct.pack('<f', ia1)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', ia1_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', ib1)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', ib1_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', ic1)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', ic1_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', in1_)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', in1_angle)[0:4])  # �ngulo Neutro

                        equipamento.append(struct.pack('<f', ia2)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', ia2_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', ib2)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', ib2_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', ic2)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', ic2_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', in2_)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', in2_angle)[0:4])  # �ngulo Neutro

                        tap1, step1 = self.dssim_obj.get_transformer_tap(nome_opendss, 1)
                        tap2, step2 = self.dssim_obj.get_transformer_tap(nome_opendss, 2)

                        if step2 != 0:
                            step = step2
                        elif tap1 != 0:
                            step = step1
                        else:
                            step = 0

                        equipamento.append(struct.pack('<h', step)[0])  # Passo do tap. Converter para signed int

                    elif tipo_equipamento == "6":  # Capacitor S�rie
                        self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda n�o implementado!" + "\n\n")
                        return None

                    elif tipo_equipamento == "7":  # Capacitor

                        nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = self.dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros

                        va = voltages[0]
                        va_angle = voltages[1]
                        vb = voltages[2]
                        vb_angle = voltages[3]
                        vc = voltages[4]
                        vc_angle = voltages[5]
                        # vn1 = voltages[6]
                        # vn1_angle = voltages[7]
                        vn = 0
                        vn_angle = 0

                        equipamento.append(struct.pack('<f', va)[0:4])  # M�dulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # �ngulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb)[0:4])  # M�dulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # �ngulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc)[0:4])  # M�dulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # �ngulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn)[0:4])  # M�dulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # �ngulo Neutro - Terminal 1


                        kvar = self.dssim_obj.get_capacitor_kvar(nome_opendss)
                        equipamento.append(struct.pack('<f', kvar)[0:4])  # Pot�ncia Reativa kvar

                        estado = self.dssim_obj.get_capacitor_state(nome_opendss)
                        equipamento.append(chr(estado))

                    elif tipo_equipamento == "8":  # Gerador
                        self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda n�o implementado!" + "\n\n")
                        return None

                    elif tipo_equipamento == "9" or tipo_equipamento == "10":  # Suprimento ou Carga

                        if tipo_equipamento == "9":
                            nome_opendss = "Vsource.source"  # nome default do elemento circuito do OpenDSS
                        else:
                            nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = self.dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        currents = self.dssim_obj.get_elem_currents(nome_opendss)
                        powers_total = self.dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros

                        va = voltages[0]
                        va_angle = voltages[1]
                        vb = voltages[2]
                        vb_angle = voltages[3]
                        vc = voltages[4]
                        vc_angle = voltages[5]
                        # vn1 = voltages[6]
                        # vn1_angle = voltages[7]
                        vn = 0
                        vn_angle = 0

                        equipamento.append(struct.pack('<f', va)[0:4])  # M�dulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # �ngulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb)[0:4])  # M�dulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # �ngulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc)[0:4])  # M�dulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # �ngulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn)[0:4])  # M�dulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # �ngulo Neutro - Terminal 1

                        ia = currents[0]
                        ib = currents[2]
                        ic = currents[4]

                        if tipo_equipamento == "9":  # Suprimento
                            if 0 <= currents[1] <= 180:  # deixar sempre entre 0 e 180
                                ia_angle = currents[1] - 180
                            else:
                                ia_angle = currents[1] + 180
                            if 0 <= currents[3] <= 180:  # deixar sempre entre 0 e 180
                                ib_angle = currents[3] - 180
                            else:
                                ib_angle = currents[3] + 180
                            if 0 <= currents[5] <= 180:  # deixar sempre entre 0 e 180
                                ic_angle = currents[5] - 180
                            else:
                                ic_angle = currents[5] + 180

                        else:  # Carga
                            ia_angle = currents[1]
                            ib_angle = currents[3]
                            ic_angle = currents[5]

                        # in1_ = currents[6]  # in_
                        # in1_angle = currents[7]
                        in_ = 0
                        in_angle = 0

                        equipamento.append(struct.pack('<f', ia)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # �ngulo Neutro

                        if tipo_equipamento == "9":  # Suprimento
                            p_3f = powers_total[0] * -1/1000.0
                            q_3f = powers_total[1] * -1/1000.0
                        else:  # Carga
                            p_3f = powers_total[0]/1000.0
                            q_3f = powers_total[1]/1000.0

                        equipamento.append(struct.pack('<f', p_3f)[0:4])  # Pot�ncia Ativa Trif�sica, sentido saindo do suprimento
                        equipamento.append(struct.pack('<f', q_3f)[0:4])  # Pot�ncia Reativa Trif�sica, sentido saindo do suprimento

                    elif tipo_equipamento == "11":  # Filtro
                        self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda n�o implementado!" + "\n\n")
                        return None
                    elif tipo_equipamento == "12":  # Reator

                        nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = self.dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        currents = self.dssim_obj.get_elem_currents(nome_opendss)
                        powers_total = self.dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros

                        va = voltages[0]
                        va_angle = voltages[1]
                        vb = voltages[2]
                        vb_angle = voltages[3]
                        vc = voltages[4]
                        vc_angle = voltages[5]
                        # vn1 = voltages[6]
                        # vn1_angle = voltages[7]
                        vn = 0
                        vn_angle = 0

                        equipamento.append(struct.pack('<f', va)[0:4])  # M�dulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # �ngulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb)[0:4])  # M�dulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # �ngulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc)[0:4])  # M�dulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # �ngulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn)[0:4])  # M�dulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # �ngulo Neutro - Terminal 1

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

                        equipamento.append(struct.pack('<f', ia)[0:4])  # M�dulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # �ngulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # M�dulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # �ngulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # M�dulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # �ngulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # M�dulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # �ngulo Neutro

                        q_3f = powers_total[1]/1000.0

                        equipamento.append(struct.pack('<f', q_3f)[0:4])  # Pot�ncia Reativa Trif�sica, sentido saindo do suprimento

                    else:
                        self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro n�o identificado. Tipo de Equipamento " + tipo_equipamento + " n�o identificado!" + "\n\n")
                        return None

                    lista_equipamentos_todos = lista_equipamentos_todos + equipamento  # Concatena lista

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(qtde_bytes) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";" + str(ord(msg_retornada[5])) + ";" + tipo_calculo + ";"   # N�o mostraremos os registros dos equipamentos pq a msg pode
                # ser muito extensa
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                msg_retornada = msg_retornada + lista_equipamentos_todos
                return "".join(str(x) for x in msg_retornada)

            elif funcao == "3":  # Altera��o de Estado de Chave

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]
                id_equipamento = msg_dividida[6]
                comando = int(msg_dividida[7])

                nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)[5:]  # retira o "Line." do nome Completo do elemento Line que � um switch
                estado_atual = int(self.dssim_obj.get_switch_state(nome_opendss))

                if comando != estado_atual:  # se o novo estado � diferente do atual
                    resposta = self.dssim_obj.set_switch_state(nome_opendss, comando)
                    if resposta == 'OK':  # Significa que foi executada com sucesso pelo OpenDSS-G. Verificar o que ocorre se a chave j� estivesse aberta
                        msg_retornada = func100acknowledgment(int(funcao), 1)

                        # self.dssim_obj.update_flow_needed = True  # for�a solu��o do fluxo novamente porque houve mudan�a no estado da chave
                        if self.dssim_obj.check_sim_needed(hora, minuto, segundo):
                            # Simula
                            self.dssim_obj.solve_time(hora, minuto, segundo)
                            # Atualiza Grafico com novo estado das chaves
                            time.sleep(0.5)
                            self.dssim_obj.refresh_gui("isolation")
                            # self.dssim_obj.refresh_gui("powers")

                    else:
                        msg_retornada = func100acknowledgment(int(funcao), 0)
                else:  # caso contr�rio, n�o � necess�rio fazer nada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "4":  # Simula��o de Falta

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                tipo_curto = msg_dividida[7]
                valor_percentual_distancia = msg_dividida[8]
                resistencia = msg_dividida[9]  # resist�ncia de falta
                indicacao_calculo = msg_dividida[10]

                if tipo_equipamento == "1":  # Falta em Barra

                    nome_barra_opendss = self.dssim_obj.get_nome_opendss(id_equipamento, "barra")
                    resposta = self.dssim_obj.set_new_bus_fault(nome_barra_opendss, int(tipo_curto), resistencia)

                else:  # Falta em Trecho

                    nome_trecho_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                    resposta = self.dssim_obj.set_new_line_fault(nome_trecho_opendss, float(valor_percentual_distancia), int(tipo_curto), resistencia)

                if resposta == 'OK':  # 0 � o valor retornado pelo DSSim quando essa fun��o � executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "5":  # Elimina Falta

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                resposta = self.dssim_obj.clear_fault()

                if resposta == 'OK':  # 0 � o valor retornado pelo DSSim quando essa fun��o � executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "6":  # Altera��o de Tap de Transformador

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                variacao_tap = int(msg_dividida[7])

                nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                resposta = self.dssim_obj.varia_tap(nome_opendss, variacao_tap)

                if resposta == 'OK':  # 0 � o valor retornado pelo DSSim quando essa fun��o � executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "8":  # Altera��o no valor de Reativo em BC

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                novo_kvar = msg_dividida[7]

                nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                resposta = self.dssim_obj.set_capacitor_kvar(nome_opendss, novo_kvar)

                if resposta == 'OK':  # 0 � o valor retornado pelo DSSim quando essa fun��o � executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "10":  # Altera��o no valor de Carga

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                novo_kw = msg_dividida[7]
                novo_kvar = msg_dividida[8]

                nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                resposta = self.dssim_obj.set_load_powers(nome_opendss, novo_kw, novo_kvar)

                if resposta == 'OK':  # 0 � o valor retornado pelo DSSim quando essa fun��o � executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            elif funcao == "11":  # Altera��o do Estado de BC

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]

                tipo_equipamento = msg_dividida[5]
                id_equipamento = msg_dividida[6]
                novo_estado = msg_dividida[7]

                nome_opendss = self.dssim_obj.get_nome_opendss(id_equipamento)
                resposta = self.dssim_obj.set_capacitor_state(nome_opendss, int(novo_estado))

                if resposta == 'OK':  # 0 � o valor retornado pelo DSSim quando essa fun��o � executada.
                    msg_retornada = func100acknowledgment(int(funcao), 1)
                else:
                    msg_retornada = func100acknowledgment(int(funcao), 0)

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                return "".join(str(x) for x in msg_retornada)

            else:
                print u"Fun��o " + funcao + u" n�o reconhecida"
                self.form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Nada enviado!" + "\n\n")
                return None

        return "nao existe objeto dssim"

    def decodifica_mensagem(self, data):
        """ M�todo que recebe a str com a mensagem que vem no Buffer e decodifica cada pacote de mensagem.
        Foi necess�rio criar essa fun��o, pois como o envio e recebimento de mensagens � ass�ncrono, pode ser
        que em uma determinada leitura do conte�do do buffer venha mais de um pacote de mensagem."""

        decodificar_dados_recebidos = True
        tamanho_mensagem = 0
        data_len = len(data)

        # Atualiza a mensagem recebida (caso incompleta anteriormente)
        for i in range(data_len):
            self.mensagem[i + tamanho_mensagem] = data[i]
        tamanho_mensagem = tamanho_mensagem + data_len

        while decodificar_dados_recebidos:
            # decodificar_dados_recebidos = False
            quantidade_bytes = ord(self.mensagem[1]) + 256 * ord(self.mensagem[2])

            if quantidade_bytes <= tamanho_mensagem:

                # if resposta is not None:
                if ord(data[0]) == 3:
                    print "oi"
                resposta = self.process_data(self.mensagem[0:quantidade_bytes])  # s� envia o conte�do de um �nico pacote
                if resposta is not None:
                    self.conn.sendall(resposta)

                # Verifica se a decodifica��o dos dados recebidos deve prosseguir
                if quantidade_bytes < tamanho_mensagem:
                    for i in range(tamanho_mensagem):
                        self.copia_mensagem[i] = self.mensagem[i]

                    for i in range(tamanho_mensagem - quantidade_bytes):
                        self.mensagem[i] = self.copia_mensagem[i + quantidade_bytes]

                    tamanho_mensagem = tamanho_mensagem - quantidade_bytes

                else:
                    tamanho_mensagem = 0
                    decodificar_dados_recebidos = False

            else:  # Mensagem recebida est� incompleta
                decodificar_dados_recebidos = False

    # #--------------------------------------------------------------------# #
    #                        M�todos Auxiliares
    # #--------------------------------------------------------------------# #

    def cria_servidor(self):
        """Cria o servidor  na porta especificada"""

        try:
            self.s.bind((self.TCP_HOST, self.TCP_PORT))  # linkando o servidor com algum endere�o e porta
            print u"Servidor para comunica��o com o MC criado com sucesso!"
            return True
        except socket.error, msg:
            ctypes.windll.user32.MessageBoxW(0, u"Link com a porta especificada para o servidor n�o criado! C�dido do erro " + str(msg[0]) + u"Mensagem: "
                                             + str(msg[1]), u"Conex�o com o M�dulo Central", 0)
            return False

    def modo_escuta(self):
        """Coloca o servidor no modo de escuta. Al�m disso, deixa o servidor esperando por uma conex�o."""
        self.s.listen(10)  # Verificar se o n�mero de conex�es poss�veis pode afetar o funcionamento do nosso software
        self.conn, self.add = self.s.accept()
        print "Conectado a " + self.add[0] + ":" + str(self.add[1])

        data = None
        while True:
            data = self.conn.recv(16384)  # Tamanho do Buffer settado para o mesmo que o da comunica��o com o DSSim
            # print data
            # print type(data)
            # if not data:
                #  break
            if data is not None:
                self.decodifica_mensagem(data)
                # resposta = self.process_data(data)
            # if resposta is not None:
            #     self.conn.sendall(resposta)

        self.conn.close()  # Verificar como arrumar essa quest�o do t�rmino da comunica��o.
        self.s.close()
        return 0


def reconstroi_msg(data):
    """ Fun��o que reconstr�i uma mensagem recebida do M�dulo Central"""

    funcao = int(ord(data[0]))
    mensagem = ""

    if funcao == 99:  # Retorna ID do Equipamento por meio de C�digo

        # Essa fun��o n�o vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem o equipamento:
        # Byte 7: N�mero do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) = 0
        # Byte 9: Id do Equipamento (Byte 2) = 0
        # Byte 10: Id do Equipamento (Byte 3) = 0
        # Byte 11: Id do Equipamento (Byte 4) = 0
        # Byte 12 a N: C�digo do Equipamento

        for i in range(len(data)):
            if ord(data[i]) == 0:  # n�o adicionar espa�os em branco que vem na mensagem...
                continue
            if i <= 10:
                mensagem = mensagem + str(ord(data[i])) + ";"
            else:  # i > 10:
                mensagem = mensagem + data[i]
            # dado uma string de comprimento unit�rio, a fun��o ord retorna o valor do byte quando o argumento
        # � uma string de 8-bit
        mensagem = mensagem + ";"
        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 1:  # Solicita��o de Registros

        # Essa fun��o n�o vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 5 Bytes que descrevem o equipamento para cada equipamento:

        # Equipamento 1:
        # Byte 7: N�mero do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1)
        # Byte 9: Id do Equipamento (Byte 2)
        # Byte 10: Id do Equipamento (Byte 3)
        # Byte 11: Id do Equipamento (Byte 4)

        # Equipamento 2:
        # Byte 12: N�mero do Tipo do Equipamento
        # Byte 13: Id do Equipamento (Byte 1)
        # Byte 14: Id do Equipamento (Byte 2)
        # Byte 15: Id do Equipamento (Byte 3)
        # Byte 16: Id do Equipamento (Byte 4)

        # E assim vai..

        count = 0
        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == (7 + 5*count + 1) or i == (7 + 5*count + 2) or i == (7 + 5*count + 3):  # n�o adicionar espa�os em branco que vem na mensagem...
                continue
            if i == (7 + 5*count):  # 7, 12, 17,...
                mensagem = mensagem + str(monta_inteiro_from_bytes(data[(7 + 5*count): (7 + 5*count + 4)])) + ';'

            else:
                if i == (11 + 5*count):
                    count = count + 1    # Se i == 11, � porque j� passou para o segundo equipamento, portanto, incrementar count
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 3:  # Altera��o de Estado em Chaves

        # Essa fun��o j� vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem a chave selecionada:

        # Byte 7: N�mero do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1)
        # Byte 9: Id do Equipamento (Byte 2)
        # Byte 10: Id do Equipamento (Byte 3)
        # Byte 11: Id do Equipamento (Byte 4)
        # Byte 12: Novo estado da chave

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10:  # n�o adicionar espa�os em branco que vem na mensagem...
                continue
            elif i == 7:
                mensagem = mensagem + str(monta_inteiro_from_bytes(data[7:11])) + ';'

            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 4:  # Simula��o de Falta

        # Essa fun��o j� vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 7 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Informa��es do Equipamento:

        # Byte 7: N�mero do Tipo do Equipamento (1 ou 2)
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # Informa��es do Curto em si

        # Byte 12: Tipo de Curto-Circuito (Valor de 0 a 4 conforme tabela de curtos)
        # Byte 13: Valor % referente a dist�ncia entre a barra 1 o defeito / tamanho do trecho (Byte 1) - Float
        # Byte 14: Valor % referente a dist�ncia entre a barra 1 o defeito / tamanho do trecho (Byte 2) - Float
        # Byte 15: Valor % referente a dist�ncia entre a barra 1 o defeito / tamanho do trecho (Byte 3) - Float
        # Byte 16: Valor % referente a dist�ncia entre a barra 1 o defeito / tamanho do trecho (Byte 4) - Float
        # Byte 17: Valor da imped�ncia de defeito em Ohms. (Byte 1) - Float
        # Byte 18: Valor da imped�ncia de defeito em Ohms. (Byte 2) - Float
        # Byte 19: Valor da imped�ncia de defeito em Ohms. (Byte 3) - Float
        # Byte 20: Valor da imped�ncia de defeito em Ohms. (Byte 4) - Float
        # Byte 21: Indica��o de c�lculo de curto-circuito com (1) ou sem pr�-falta (0).

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10 or i == 13 or i == 14 or i == 15 or i == 17 or i == 18 or i == 19:  # n�o adicionar espa�os em branco que vem na mensagem...
                continue
            elif i == 7:
                mensagem = mensagem + str(monta_inteiro_from_bytes(data[7:11])) + ';'
            elif i == 12:  # Dist�ncia
                mensagem = mensagem + str(monta_float_from_bytes(data[12:16])) + ';'
            elif i == 16:  # Imped�ncia
                mensagem = mensagem + str(monta_float_from_bytes(data[16:20])) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 5:  # Elimina Falta

        # Essa fun��o j� vem com a quantidade de bytes fechada.

        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        for i in range(len(data)):
            if ord(data[i]) == 0 and i == 2:  # n�o adicionar espa�os em branco que vem na mensagem...
                continue
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 6:  # Altera��o no Tap de Transformador

        # Essa fun��o j� vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 7 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 5 Bytes que descrevem o transformador selecionado:

        # Byte 7: N�mero do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # E 1 Byte com a varia��o do tap
        # Byte 12: Varia��o (Byte) - Inteiro sem sinal. Precisamos converter de NotSignedToSigned

        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == 8 or i == 9 or i == 10:  # n�o adicionar espa�os em branco que vem na mensagem...
                continue
            if i == 7:
                mensagem = mensagem + str(monta_inteiro_from_bytes(data[7:11])) + ';'
            elif i == 11:
                mensagem = mensagem + str(monta_byte_to_signed_int(str(ord(data[i])))) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 7:  # Altera��o no Tap de Regulador de Tens�o
        return "funcao 7 ainda n�o implementada"
    elif funcao == 8 or funcao == 11:  # Fun��es 8 e 11 possuem a mesma estrutura (Altera��o no valor de reativo BC e Altera��o em estado de BC, respectivamente)

        # Essa fun��o j� vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem a chave selecionada:

        # Byte 7: N�mero do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # Byte 12: Nova Pot�ncia Reativa (Byte 1)  - Float Fun��o 8 ; # Byte 12: Novo Estado do BC (Byte 1)  - Int Fun��o 8 ;
        # Byte 13: Nova Pot�ncia Reativa (Byte 2)  - Float Fun��o 8 ; # Byte 13: Nova Estado do BC (Byte 2)  - Int Fun��o 8 ;
        # Byte 14: Nova Pot�ncia Reativa (Byte 3)  - Float Fun��o 8 ; # Byte 14: Nova Estado do BC (Byte 3)  - Int Fun��o 8 ;
        # Byte 15: Nova Pot�ncia Reativa (Byte 4)  - Float Fun��o 8 ; # Byte 15: Nova Estado do BC (Byte 4)  - Int Fun��o 8 ;

        count = 0
        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == (7 + 4*count + 1) or i == (7 + 4*count + 2) or i == (7 + 4*count + 3):  # n�o adicionar espa�os em branco que vem na mensagem...
                if i == (10 + 4*count):
                    count = count + 1    # Se i == 11, � porque j� passou para o segundo equipamento, portanto, incrementar count
                continue
            if i == (7 + 4*count):  # 7, 12, 17,...
                if count == 0 or (count == 1 and funcao == 11):
                    mensagem = mensagem + str(monta_inteiro_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
                elif count == 1:
                    mensagem = mensagem + str(monta_float_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    elif funcao == 9:  # Altera��o no valor de suprimento
        return "funcao 9 ainda n�o implementada"
    elif funcao == 10:  # Altera��o no valor de carga

        # Essa fun��o j� vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 6 bytes iniciais
        # Byte 1: Fun��o
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 6 Bytes que descrevem a chave selecionada:

        # Byte 7: N�mero do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # Byte 12: Nova Pot�ncia Ativa (Byte 1)  - Float
        # Byte 13: Nova Pot�ncia Ativa (Byte 2)  - Float
        # Byte 14: Nova Pot�ncia Ativa (Byte 3)  - Float
        # Byte 15: Nova Pot�ncia Ativa (Byte 4)  - Float

        # Byte 16: Nova Pot�ncia Reativa (Byte 1)  - Float
        # Byte 17: Nova Pot�ncia Reativa (Byte 2)  - Float
        # Byte 18: Nova Pot�ncia Reativa (Byte 3)  - Float
        # Byte 19: Nova Pot�ncia Reativa (Byte 4)  - Float

        count = 0
        for i in range(len(data)):
            if (ord(data[i]) == 0 and i == 2) or i == (7 + 4 * count + 1) or i == (7 + 4 * count + 2) or i == (7 + 4 * count + 3):  # n�o adicionar espa�os em branco que vem na mensagem...
                if i == (10 + 4 * count):
                    count = count + 1  # Se i == 11, � porque j� passou para o segundo equipamento, portanto, incrementar count
                continue
            if i == (7 + 4 * count):  # 7, 12, 17,...
                if count == 0:
                    mensagem = mensagem + str(monta_inteiro_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
                else:
                    mensagem = mensagem + str(monta_float_from_bytes(data[(7 + 4 * count): (7 + 4 * count + 4)])) + ';'
            else:
                mensagem = mensagem + str(ord(data[i])) + ";"

        # print "msg reconstruida, " + mensagem
        return str(mensagem)

    else:
        return u"Fun��o n�o identificada, mensagem n�o p�de ser reconstru�da!"


def func100acknowledgment(funcao, flag):
    """ Funcao resposta para o MC �s fun��es 03, 04, 05, 06, 07, 08, 09, 10 e 11. Se todos os dados
    foram recebidos e o DSSim conseguiu executar a sua respectiva fun��o, retorna flag = 1
    se n�o, flag = 0."""
    msg_retornada = [chr(0)] * 5

    msg_retornada[0] = chr(100)
    msg_retornada[1] = chr(5) # Possui 5 BYTES!!!
    msg_retornada[2] = chr(0)
    msg_retornada[3] = chr(funcao)
    msg_retornada[4] = chr(flag)

    return msg_retornada
