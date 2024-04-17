###  # -*- coding: iso-8859-15 -*-

""" Software para teste da comunica??o entre um aplicativo Python e o DSSimPC-V2.0

autores: Celso Rocha, Paulo Radatz

Esse software corresponde a etapa inicial do Projeto de Integra??o do DSSimPC-V2.0 ao Laborat?rio de
SmartGrids do Enerq-USP.


"""
#
# __author__ = 'CelsoRocha' and 'Paulo Radatz'
#
import DSSIM
#
TCP_IP = '127.0.0.1'
TCP_PORT = 6345
BUFFER_SIZE = 8192  # Qual valor utilizar aqui?

# arquivo = "voltages_pu"
# arquivo2 = "voltages_kv"


teste = DSSIM.DSSim(TCP_IP, TCP_PORT, BUFFER_SIZE, None)
teste.connect()
print teste.get_simulation_time('s')
print teste.get_simulation_time('m')
print teste.get_simulation_time('h')
print teste.get_simulation_time('d')



teste.check_sim_needed(18, 0, 0)
teste.solve_time(18, 0, 0)

# b = teste.get_all_nodes_voltages('kV')
# escreve_lista_par(arquivo2, b)
# print b
#
# a = teste.get_all_nodes_voltages('pu')
# escreve_lista(arquivo, a)
# print a

# for i in range(10):
#     teste.send_dss_command("solve")
#     time.sleep(3)


# teste.send_dss_command("set number=6")
# print teste.send_dss_command("get earthmodel")

# print teste.send_dss_command("set mode= snapshot")
# teste.send_dss_command("solve")
# print teste.send_dss_command("set number=10")

#
# for i in range(10):
#     print teste.step_in()
#     # print teste.send_dss_command("solve")
#     time.sleep(2)
#     if i == 3:
#         teste.set_switch("sw2", 0)
#         time.sleep(1)
#         teste.refresh_gui("isolation")
#     if i == 6:
#         teste.set_switch("sw2", 1)
#         time.sleep(1)
#         teste.refresh_gui("isolation")
# print teste.step_in()


# print teste.end_simulation()

# while True:
#     time.sleep(1)
#     a = teste.get_last_event()
#     print a
#     print type(a), len(a)


# print "bus_voltages",           teste.get_bus_voltages("29")
# print "element currents",       teste.get_elem_currents("line.l31")
# print "element voltages",       teste.get_elem_voltages("transformer.reg1a", 2)
# print "switch state",           teste.get_switch_state("sw2")
# print "element total powers", teste.get_total_powers("line.l19", 1)
# print "element total powers", teste.get_total_powers("line.l19", 2)
# print "element total powers", teste.get_total_powers("line.l19", None)
# print "element total powers", teste.get_phase_powers("line.l19", 1, 1)
# print "element total powers", teste.get_phase_powers("line.l19", 1, 2)
# print "element total powers", teste.get_phase_powers("line.l19", 1, 3)
# print "element total powers", teste.get_phase_powers("line.l19", 2, 1)
# print "element total powers", teste.get_phase_powers("line.l19", 2, 2)
# print "element total powers", teste.get_phase_powers("line.l19", 2, 3)
# # print "element total powers", teste.get_phase_powers("line.l19", 2, 4)
#
# print teste.get_transformer_tap("transformer.reg1a", 1)
# print teste.get_transformer_tap("transformer.reg1a", 2)
# # print teste.get_transformer_tap("transformer.reg1a", 3)
#
# print teste.get_capacitor_state("capacitor.c90b")
# print teste.get_capacitor_kvar("capacitor.c90b")
#
# print teste.get_last_event()
#
#
#
#
# teste.close()



