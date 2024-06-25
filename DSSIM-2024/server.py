###  # -*- coding: UTF-8 -*-

import sys
import socket
import struct
import datetime
import threading
# import thread
# import Core.MC as coreMC
import Core.DSSIM as DSSIM
import App.Fontes.Auxiliar as aux
from Tools.test_tools import *

TCP_IP = '127.0.0.1'
TCP_PORT = 6345
BUFFER_SIZE = 8192  # Qual valor utilizar aqui?


resp92 = "\x02\x80\x00"
resp92_enc = resp92.encode('latin')
resp94 = "\x02\x79\x00"
resp94_enc = resp94.encode('latin')


dssim_obj = DSSIM.DSSim(TCP_IP, TCP_PORT, BUFFER_SIZE, None)    #> teste
dssim_obj.connect()
dssim_obj.armazena_path()
dssim_obj.armazena_nomes_elementos()

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

        message = reconstroi_msg(msg)
        # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.REC, message + "\n\n")
        print(msg)
        print(message)

        msg_dividida = message.split(";")
        funcao = msg_dividida[0]
        print('funcao: ', funcao)

        # dssim_obj = 2    #> dssim_obj=None para teste
        #! verificar se esses "is not", funcionam e/ou fazem sentido
        if dssim_obj is not None:  # Verifica se existe conexão com o DSSim
            if funcao == "99":  # Retorna ID do equipamento por meio de código
                codigo_equipamento = msg_dividida[-2]
                print('codigo_equipamento: ', codigo_equipamento)

                tipo_equipamento = msg_dividida[5]
                print('tipo_equipamento: ', tipo_equipamento)

                # id_equipamento = 6285  #< int númro grande dá problema
                # id_equipamento = 1  #> int funcionando
                id_equipamento = dssim_obj.retorna_id(codigo_equipamento, tipo_equipamento)  # int
                print('id_equipamento: ', id_equipamento)

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

                count = 0
                lista_equipamentos = []  # lista de tuplas
                for i in range(len(msg_dividida)-1):  # -1 porque tem um espaço a mais que vem por causa do split(";")
                    if i == (5 + count*2):
                            tipo_equipamento = msg_dividida[i]
                            print(tipo_equipamento)
                            id_equipamento = msg_dividida[i+1]
                            print(id_equipamento)
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

                    if i == 1:
                        print("oi")
                    equipamento.append(chr(int(tipo_equipamento)))  # Tipo

                    id_equip_bytes = struct.pack('<Q', int(id_equipamento))[0:4]  # Id
                    equipamento.append(id_equip_bytes.decode())

                    if tipo_equipamento == "1":  # Barra
                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento, "barra")
                        voltages = dssim_obj.get_bus_voltages(nome_opendss)  # salva array com registros

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
                        currents = dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros
                        voltages_1 = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        voltages_2 = dssim_obj.get_elem_voltages(nome_opendss, 2)  # salva array com registros
                        powers_total = dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros
                        power_phase_a = dssim_obj.get_phase_powers(nome_opendss, 1, 1)  #* Cuidado aqui, precisamos verificar as fases disponíveis antes...
                        power_phase_b = dssim_obj.get_phase_powers(nome_opendss, 1, 2)
                        power_phase_c = dssim_obj.get_phase_powers(nome_opendss, 1, 3)

                        # va1 = struct.pack('<f', voltages_1[0])[0:4]
                        # va1_angle = struct.pack('<f', voltages_1[1])[0:4]
                        # vb1 = struct.pack('<f', voltages_1[2])[0:4]
                        # vb1_angle = struct.pack('<f', voltages_1[3])[0:4]
                        # vc1 = struct.pack('<f', voltages_1[4])[0:4]
                        # vc1_angle = struct.pack('<f', voltages_1[5])[0:4]
                        # vn1 = struct.pack('<f', voltages_1[6])[0:4]
                        # vn1_angle = struct.pack('<f', voltages_1[7])[0:4]

                        va1 = struct.pack('<f', 0)[0:4]
                        va1_angle = struct.pack('<f', 0)[0:4]
                        vb1 = struct.pack('<f', 0)[0:4]
                        vb1_angle = struct.pack('<f', 0)[0:4]
                        vc1 = struct.pack('<f', 0)[0:4]
                        vc1_angle = struct.pack('<f', 0)[0:4]
                        vn1 = struct.pack('<f', 0)[0:4]
                        vn1_angle = struct.pack('<f', 0)[0:4]

                        equipamento.append(va1_angle.decode())  # Ângulo Fase - Terminal 1
                        equipamento.append(va1.decode())  # Módulo Fase A - Terminal 1
                        equipamento.append(vb1.decode())  # Módulo Fase B - Terminal 1
                        equipamento.append(vb1_angle.decode())  # Ângulo Fase B - Terminal 1
                        equipamento.append(vc1.decode())  # Módulo Fase C - Terminal 1
                        equipamento.append(vc1_angle.decode())  # Ângulo Fase C - Terminal 1
                        equipamento.append(vn1.decode())  # Módulo Neutro - Terminal 1
                        equipamento.append(vn1_angle.decode())  # Ângulo Neutro - Terminal 1

                        # va2 = voltages_2[0]
                        # va2_angle = voltages_2[1]
                        # vb2 = voltages_2[2]
                        # vb2_angle = voltages_2[3]
                        # vc2 = voltages_2[4]
                        # vc2_angle = voltages_2[5]
                        # vn2 = voltages_2[6]
                        # vn2_angle = voltages_2[7]

                        va2 = float(0)
                        va2_angle = float(0)
                        vb2 = float(0)
                        vb2_angle = float(0)
                        vc2 = float(0)
                        vc2_angle = float(0)
                        vn2 = float(0)
                        vn2_angle = float(0)

                        equipamento.append((struct.pack('<f', va2)[0:4]).decode())  # Módulo Fase A - Terminal 2
                        equipamento.append((struct.pack('<f', va2_angle)[0:4]).decode())  # Ângulo Fase - Terminal 2
                        equipamento.append((struct.pack('<f', vb2)[0:4]).decode())  # Módulo Fase B - Terminal 2
                        equipamento.append((struct.pack('<f', vb2_angle)[0:4]).decode())  # Ângulo Fase B - Terminal 2
                        equipamento.append((struct.pack('<f', vc2)[0:4]).decode())  # Módulo Fase C - Terminal 2
                        equipamento.append((struct.pack('<f', vc2_angle)[0:4]).decode())  # Ângulo Fase C - Terminal 2
                        equipamento.append((struct.pack('<f', vn2)[0:4]).decode())  # Módulo Neutro - Terminal 2
                        equipamento.append((struct.pack('<f', vn2_angle)[0:4]).decode())  # Ângulo Neutro - Terminal 2

                        ia = float(0)
                        ia_angle = float(0)
                        ib = float(0)
                        ib_angle = float(0)
                        ic = float(0)
                        ic_angle = float(0)
                        in_ = float(0)
                        in_angle = float(0)

                        # ia = currents[0]
                        # ia_angle = currents[1]
                        # ib = currents[2]
                        # ib_angle = currents[3]
                        # ic = currents[4]
                        # ic_angle = currents[5]
                        # in_ = currents[6]  # in_
                        # in_angle = currents[7]

                        equipamento.append((struct.pack('<f', ia)[0:4]).decode())  # Módulo Fase A
                        equipamento.append((struct.pack('<f', ia_angle)[0:4]).decode())  # Ângulo Fase
                        equipamento.append((struct.pack('<f', ib)[0:4]).decode())  # Módulo Fase B
                        equipamento.append((struct.pack('<f', ib_angle)[0:4]).decode())  # Ângulo Fase B
                        equipamento.append((struct.pack('<f', ic)[0:4]).decode())  # Módulo Fase C
                        equipamento.append((struct.pack('<f', ic_angle)[0:4]).decode())  # Ângulo Fase C
                        equipamento.append((struct.pack('<f', in_)[0:4]).decode())  # Módulo Neutro
                        equipamento.append((struct.pack('<f', in_angle)[0:4]).decode())  # Ângulo Neutro

                        switch_state = chr(int(dssim_obj.get_switch_state(nome_opendss.split(".")[1])))   # switch state não tá funcionando para a última chave
                        equipamento.append(switch_state)
                        cbr = chr(int(0))
                        equipamento.append(cbr)
                        cbtl = chr(int(0))
                        equipamento.append(cbtl)
                        lockout = chr(int(dssim_obj.get_switch_lock(nome_opendss.split(".")[1]))) # checaaaar
                        equipamento.append(lockout)

                        # Em qual terminal?
                        p_3f = float(0) # powers_total[0]/1000.0  # converter de kW para MW
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

                        # Id da barra de referência (assumi como sendo a barra 1 da chave) Convertendo o valor do ID para 4 bytes segundo o formato Little Endian
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
                        voltages_1 = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        voltages_2 = dssim_obj.get_elem_voltages(nome_opendss, 2)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)  # salva array com registros

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

                        equipamento.append(struct.pack('<f', va1)[0:4])  # Módulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va1_angle)[0:4])  # Ângulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb1)[0:4])  # Módulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb1_angle)[0:4])  # Ângulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc1)[0:4])  # Módulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc1_angle)[0:4])  # Ângulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn1)[0:4])  # Módulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn1_angle)[0:4])  # Ângulo Neutro - Terminal 1

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

                        equipamento.append(struct.pack('<f', va2)[0:4])  # Módulo Fase A - Terminal 2
                        equipamento.append(struct.pack('<f', va2_angle)[0:4])  # Ângulo Fase - Terminal 2
                        equipamento.append(struct.pack('<f', vb2)[0:4])  # Módulo Fase B - Terminal 2
                        equipamento.append(struct.pack('<f', vb2_angle)[0:4])  # Ângulo Fase B - Terminal 2
                        equipamento.append(struct.pack('<f', vc2)[0:4])  # Módulo Fase C - Terminal 2
                        equipamento.append(struct.pack('<f', vc2_angle)[0:4])  # Ângulo Fase C - Terminal 2
                        equipamento.append(struct.pack('<f', vn2)[0:4])  # Módulo Neutro - Terminal 2
                        equipamento.append(struct.pack('<f', vn2_angle)[0:4])  # Ângulo Neutro - Terminal 2

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

                        equipamento.append(struct.pack('<f', ia1)[0:4])  # Módulo Fase A
                        equipamento.append(struct.pack('<f', ia1_angle)[0:4])  # Ângulo Fase
                        equipamento.append(struct.pack('<f', ib1)[0:4])  # Módulo Fase B
                        equipamento.append(struct.pack('<f', ib1_angle)[0:4])  # Ângulo Fase B
                        equipamento.append(struct.pack('<f', ic1)[0:4])  # Módulo Fase C
                        equipamento.append(struct.pack('<f', ic1_angle)[0:4])  # Ângulo Fase C
                        equipamento.append(struct.pack('<f', in1_)[0:4])  # Módulo Neutro
                        equipamento.append(struct.pack('<f', in1_angle)[0:4])  # Ângulo Neutro

                        equipamento.append(struct.pack('<f', ia2)[0:4])  # Módulo Fase A
                        equipamento.append(struct.pack('<f', ia2_angle)[0:4])  # Ângulo Fase
                        equipamento.append(struct.pack('<f', ib2)[0:4])  # Módulo Fase B
                        equipamento.append(struct.pack('<f', ib2_angle)[0:4])  # Ângulo Fase B
                        equipamento.append(struct.pack('<f', ic2)[0:4])  # Módulo Fase C
                        equipamento.append(struct.pack('<f', ic2_angle)[0:4])  # Ângulo Fase C
                        equipamento.append(struct.pack('<f', in2_)[0:4])  # Módulo Neutro
                        equipamento.append(struct.pack('<f', in2_angle)[0:4])  # Ângulo Neutro

                        tap1, step1 = dssim_obj.get_transformer_tap(nome_opendss, 1)
                        tap2, step2 = dssim_obj.get_transformer_tap(nome_opendss, 2)

                        if step2 != 0:
                            step = step2
                        elif tap1 != 0:
                            step = step1
                        else:
                            step = 0

                        equipamento.append(struct.pack('<h', step)[0])  # Passo do tap. Converter para signed int

                    elif tipo_equipamento == "6":  # Capacitor Série
                        form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda não implementado!" + "\n\n")
                        return None

                    elif tipo_equipamento == "7":  # Capacitor

                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros

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

                        equipamento.append(struct.pack('<f', va)[0:4])  # Módulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # Ângulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb)[0:4])  # Módulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # Ângulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc)[0:4])  # Módulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # Ângulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn)[0:4])  # Módulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # Ângulo Neutro - Terminal 1


                        kvar = dssim_obj.get_capacitor_kvar(nome_opendss)
                        equipamento.append(struct.pack('<f', kvar)[0:4])  # Potência Reativa kvar

                        estado = dssim_obj.get_capacitor_state(nome_opendss)  # Estado do capacitor
                        equipamento.append(chr(estado))

                    elif tipo_equipamento == "8":  # Gerador
                        form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda não implementado!" + "\n\n")
                        return None

                    elif tipo_equipamento == "9" or tipo_equipamento == "10":  # Suprimento ou Carga

                        if tipo_equipamento == "9":
                            nome_opendss = "Vsource.source"  # nome default do elemento circuito do OpenDSS
                        else:
                            nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)
                        powers_total = dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros

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

                        equipamento.append(struct.pack('<f', va)[0:4])  # Módulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # Ângulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb)[0:4])  # Módulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # Ângulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc)[0:4])  # Módulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # Ângulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn)[0:4])  # Módulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # Ângulo Neutro - Terminal 1

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

                        equipamento.append(struct.pack('<f', ia)[0:4])  # Módulo Fase A
                        equipamento.append(struct.pack('<f', ia_angle)[0:4])  # Ângulo Fase
                        equipamento.append(struct.pack('<f', ib)[0:4])  # Módulo Fase B
                        equipamento.append(struct.pack('<f', ib_angle)[0:4])  # Ângulo Fase B
                        equipamento.append(struct.pack('<f', ic)[0:4])  # Módulo Fase C
                        equipamento.append(struct.pack('<f', ic_angle)[0:4])  # Ângulo Fase C
                        equipamento.append(struct.pack('<f', in_)[0:4])  # Módulo Neutro
                        equipamento.append(struct.pack('<f', in_angle)[0:4])  # Ângulo Neutro

                        if tipo_equipamento == "9":  # Suprimento
                            p_3f = powers_total[0] * -1/1000.0
                            q_3f = powers_total[1] * -1/1000.0
                        else:  # Carga
                            p_3f = powers_total[0]/1000.0
                            q_3f = powers_total[1]/1000.0

                        equipamento.append(struct.pack('<f', p_3f)[0:4])  # Potência Ativa Trifásica, sentido saindo do suprimento
                        equipamento.append(struct.pack('<f', q_3f)[0:4])  # Potência Reativa Trifásica, sentido saindo do suprimento

                    elif tipo_equipamento == "11":  # Filtro
                        form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro do equipamento " + tipo_equipamento + " ainda não implementado!" + "\n\n")
                        return None
                    elif tipo_equipamento == "12":  # Reator

                        nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
                        voltages = dssim_obj.get_elem_voltages(nome_opendss, 1)  # salva array com registros
                        currents = dssim_obj.get_elem_currents(nome_opendss)
                        powers_total = dssim_obj.get_total_powers(nome_opendss, 1)  # salva array com registros

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

                        equipamento.append(struct.pack('<f', va)[0:4])  # Módulo Fase A - Terminal 1
                        equipamento.append(struct.pack('<f', va_angle)[0:4])  # Ângulo Fase - Terminal 1
                        equipamento.append(struct.pack('<f', vb)[0:4])  # Módulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vb_angle)[0:4])  # Ângulo Fase B - Terminal 1
                        equipamento.append(struct.pack('<f', vc)[0:4])  # Módulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vc_angle)[0:4])  # Ângulo Fase C - Terminal 1
                        equipamento.append(struct.pack('<f', vn)[0:4])  # Módulo Neutro - Terminal 1
                        equipamento.append(struct.pack('<f', vn_angle)[0:4])  # Ângulo Neutro - Terminal 1

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

                    else:
                        form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Registro não identificado. Tipo de Equipamento " + tipo_equipamento + " não identificado!" + "\n\n")
                        return None

                    lista_equipamentos_todos = lista_equipamentos_todos + equipamento  # Concatena lista

                # Mensagem Display
                msg = str(ord(msg_retornada[0])) + ";" + str(qtde_bytes) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";" + str(ord(msg_retornada[5])) + ";" + tipo_calculo + ";"   # Não mostraremos os registros dos equipamentos pq a msg pode
                # ser muito extensa
                # form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

                msg_retornada = msg_retornada + lista_equipamentos_todos
                resposta = "".join(str(x) for x in msg_retornada)
                resposta2 = "".join(x for x in msg_retornada)
                resp_encode = resposta.encode()  #> bytes
                resp_b = f"b'{resposta}'"  #> string
                resp_def = teste_cria_resposta_encodada(resposta)
                resp_encode = resposta  #> bytes
                # resp_ascii = resposta.encode('ascii', 'ignore')
                # resp_bytes = bytes(resposta)
                return resposta

            elif funcao == "3":  # Alteração de Estado de Chave
                print('funcao: ', funcao)

                return

                qtde_bytes_rcv = msg_dividida[1]
                hora = msg_dividida[2]
                minuto = msg_dividida[3]
                segundo = msg_dividida[4]
                id_equipamento = msg_dividida[6]
                comando = int(msg_dividida[7])

                nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)[5:]  # retira o "Line." do nome Completo do elemento Line que é um switch
                estado_atual = int(dssim_obj.get_switch_state(nome_opendss))

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
                form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

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

            # elif funcao == "6":  # Alteração de Tap de Transformador

            #     qtde_bytes_rcv = msg_dividida[1]
            #     hora = msg_dividida[2]
            #     minuto = msg_dividida[3]
            #     segundo = msg_dividida[4]

            #     tipo_equipamento = msg_dividida[5]
            #     id_equipamento = msg_dividida[6]
            #     variacao_tap = int(msg_dividida[7])

            #     nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
            #     resposta = dssim_obj.varia_tap(nome_opendss, variacao_tap)

            #     if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
            #         msg_retornada = func100acknowledgment(int(funcao), 1)
            #     else:
            #         msg_retornada = func100acknowledgment(int(funcao), 0)

            #     # Mensagem Display
            #     msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

            #     return "".join(str(x) for x in msg_retornada)

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

            # elif funcao == "11":  # Alteração do Estado de BC

            #     qtde_bytes_rcv = msg_dividida[1]
            #     hora = msg_dividida[2]
            #     minuto = msg_dividida[3]
            #     segundo = msg_dividida[4]

            #     tipo_equipamento = msg_dividida[5]
            #     id_equipamento = msg_dividida[6]
            #     novo_estado = msg_dividida[7]

            #     nome_opendss = dssim_obj.get_nome_opendss(id_equipamento)
            #     resposta = dssim_obj.set_capacitor_state(nome_opendss, int(novo_estado))

            #     if resposta == 'OK':  # 0 é o valor retornado pelo DSSim quando essa função é executada.
            #         msg_retornada = func100acknowledgment(int(funcao), 1)
            #     else:
            #         msg_retornada = func100acknowledgment(int(funcao), 0)

            #     # Mensagem Display
            #     msg = str(ord(msg_retornada[0])) + ";" + str(ord(msg_retornada[1])) + ";" + str(ord(msg_retornada[3])) + ";" + str(ord(msg_retornada[4])) + ";"
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, msg + "\n\n")

            #     return "".join(str(x) for x in msg_retornada)

            # else:
            #     print(u"Função " + funcao + u" não reconhecida")
            #     form.escreve_mensagem(Conexao.MC_CON, Tipo_Conexao.ENV, "Nada enviado!" + "\n\n")
            #     return None

        return "nao existe objeto dssim"

def decodifica_mensagem(conn, data):
    """ Método que recebe a str com a mensagem que vem no Buffer e decodifica cada pacote de mensagem.
    Foi necessário criar essa função, pois como o envio e recebimento de mensagens é assíncrono, pode ser
    que em uma determinada leitura do conteúdo do buffer venha mais de um pacote de mensagem."""


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
        print('quantidade_bytes: ', quantidade_bytes)

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

                print('\nlen_data: ', data_len)
                # print('data_encode:\t\t', data.encode())
                # print('resposta_encode:\t', resposta.encode())
                print(f'len_resposta: {resposta_len}\n')

                # conn.sendall(resposta)
                conn.send(resposta.encode('latin'))

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


def reconstroi_msg(data):
    """ Função que reconstrói uma mensagem recebida do Módulo Central"""

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

        # Essa função já vem com a quantidade de bytes fechada.

        # Essa mensagem possui sempre 7 bytes iniciais
        # Byte 1: Função
        # Byte 2: Quantidade de Bytes - byte 1
        # Byte 3: Quantidade de Bytes - byte 2 = 0
        # Byte 4: Hora
        # Byte 5: Minuto
        # Byte 6: Segundo

        # Mais 5 Bytes que descrevem o transformador selecionado:

        # Byte 7: Número do Tipo do Equipamento
        # Byte 8: Id do Equipamento (Byte 1) - Inteiro
        # Byte 9: Id do Equipamento (Byte 2) - Inteiro
        # Byte 10: Id do Equipamento (Byte 3) - Inteiro
        # Byte 11: Id do Equipamento (Byte 4) - Inteiro

        # E 1 Byte com a variação do tap
        # Byte 12: Variação (Byte) - Inteiro sem sinal. Precisamos converter de NotSignedToSigned

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
        return "funcao 7 ainda não implementada"

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

try:
    '''
        #* Passar uma string VAZIA significa que o servidor também pode ouvir conexões de entrada de outros computadores.
        #> Se fosse passado 127.0.0.1, então ele ouviria apenas as chamadas feitas dentro do PC local.
    '''
    HOST = ''  # localhost
    # reserve uma PORT neste PC
    PORT = 1024

    s = socket.socket() # cria objeto socket
    print('Socket criado com sucesso')

    s.bind((HOST, PORT))

    print('socket escutando em %s' %(PORT))

    s.listen(5) # põe socket em modo escuta
    print ('socket está escutando')

    # MC = coreMC.MC


    i = 0

    def main(c,numOfThread):
        while True:
            # print('main while ', i)

            # rcvdData_semDecode = c.recv(1024)
            # print('rcvdData_semDecode: ', rcvdData_semDecode)

            # rcvdData = rcvdData_semDecode.decode()
            rcvdData = c.recv(1024).decode()
            # print('rcvdData: ', rcvdData)

            decodifica_mensagem(c, rcvdData)

            # print(f'Thread: {numOfThread+1}\n')
            # print(f'Thread: {numOfThread+1}\n\t S: {rcvdData}')

            # sendData = input('N: ')
            # c.send(sendData.encode())

            # if(sendData.lower() == 'bye'):
            #     break
            if(rcvdData == ''):
                c.close()

        c.close()

    while True:
        # print('while ', i)
        c, addr = s.accept()
        print('Conexão estabelecida com', addr)

        # thread.start_new_thread(main,(c,i,))
        t1 = threading.Thread(target=main, args=(c,1,))
        t1.start()
        t1.join()

        i+=1

        s.close()

except KeyboardInterrupt:
    print(f'Fechando a conexão e liberando a porta {PORT}.')
    c.close()
    sys.exit()



    # # a forever loop until we interrupt it or
    # # an error occurs
    # while True:

    #     # Establish connection with client.
    #     c, addr = s.accept()
    #     print ('Conexão estabelecida com', addr)

    #     # send a thank you message to the client. encoding to send byte type.
    #     c.send('Gratiluz por conectar'.encode())

    #     # Close the connection with the client
    #     c.close()
    #     print('socket fechado')

    #     # Breaking once connection closed
    #     break

