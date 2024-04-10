###  # -*- coding: iso-8859-15 -*-

""" Software para teste da comunica��o entre um aplicativo Python e o DSSimPC-V2.0

autores: Celso Rocha, Paulo Radatz

Esse software corresponde a etapa inicial do Projeto de Integra��o do DSSimPC-V2.0 ao Laborat�rio de
SmartGrids do Enerq-USP.


"""

__author__ = 'CelsoRocha' and 'Paulo Radatz'

import os
import tkFileDialog
import tkMessageBox
import Tkinter as tk
from LED import *
from Fontes.DSSIM import *
from Fontes.Auxiliar import *
from formConfiguracoes import *
from Fontes.MC import *
import threading
from PIL import Image, ImageTk

# import Fontes.CommunicationTest



# import matplotlib
# matplotlib.use("TkAgg")
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# from matplotlib.figure import Figure
# from matplotlib.font_manager import FontProperties

# from matplotlib.lines import Line2D
# from matplotlib.patches import Rectangle
# from matplotlib.text import Text
# from matplotlib.image import AxesImage
# from matplotlib import style
# style.use('ggplot')

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Helvetica", 10)
SMALL_FONT = ("Helvetica", 8)

class Form(tk.Frame):

    @classmethod
    def main(cls):
        root = tk.Tk()
        celso_gui = cls(root)
        root.mainloop()   # � uma fun��o da classe Tkinter.Tk, a qual o objeto root pertence. � essa fun��o que mant�m
        #  a janela sempre vis�vel e n�o deixa ela fechar
        return celso_gui

    def __init__(self, root):   # N�o entendi direito
        tk.Frame.__init__(self, root)   # N�o entendi isso aqui
        self.root = root
        self.root.protocol('WM_DELETE_WINDOW', self.exit_form)
        self._setup()   # Inicializa propriedades visuais do Form
        self.dssim_obj = None
        self.mc_obj = None
        self.define_bindings()   # Define os bindings dos widgets a eventos

    def _setup(self, **kwargs):
        self.root.title(u"M�dulo de Conex�o DSSim - M�dulo Central")
        self.root.geometry('1000x650')
        # self.root.iconbitmap('icons/main4.ico')

    # --------------------------------------------------Menu---------------------------------------------------------- #
        
        menu_principal = tk.Menu(self.root)

    # -------------------------------------------------Menu Opções---------------------------------------------------- #
       
        self.menu_config = tk.Menu(menu_principal, tearoff=0, activebackground='#004c99', activeforeground='white')

        self.menu_config.add_command(label="Editar IP e Porta", command=self.abre_config)

    # ------------------------------------------Menu -------------------------------------- #

        menu_principal.add_cascade(label=u"Opções", menu=self.menu_config)

    # ---------------------------------------------------------------------------------------------------------------- #

        self.root.config(menu=menu_principal, bg='#2A2C2B')  # Necess�rio para adicionar o menu ao frame root.

    # -------------------------------------------------FRAMES--------------------------------------------------------- #
        frame = tk.Frame(self.root)  # Criado s� para ajustar os pads das LabelFrames DSSim e M�dulo Central
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        # Frame para inser��o das figuras:
        figures_frame = tk.Frame(frame, bd=2, relief=tk.FLAT)
        figures_frame.pack(padx=2, pady=2, expand=NO, fill=tk.BOTH, anchor=tk.N, side=tk.TOP)

        path = os.path.join(os.path.dirname(__file__), '..', 'Images')

        # Definir essas vari�veis como globais para manter na GUI ap�s a execu��o desse m�todo.
        global img_epri
        global img_enerq
        img1 = Image.open(path + '\EPRI logo 2015_RGB.png')
        resized_img1 = img1.resize((200, 50), Image.ANTIALIAS)
        # img1.save("\EPRI logo 2015_RGB2.png", "png")

        img2 = Image.open(path + '\logonovo_vert.png')
        resized_img2 = img2.resize((50, 50), Image.ANTIALIAS)
        # img2.save()

        img_epri = ImageTk.PhotoImage(resized_img1)
        img_enerq = ImageTk.PhotoImage(resized_img2)

        lbEPRI = tk.Label(figures_frame, image=img_epri)
        lbEPRI.pack(padx=2, pady=2, expand=NO, fill=tk.BOTH, anchor=tk.NE, side=tk.RIGHT)

        lbEnerq = tk.Label(figures_frame, image=img_enerq)
        lbEnerq.pack(padx=2, pady=2, expand=NO, fill=tk.BOTH, anchor=tk.NW, side=tk.RIGHT)


        # Label com instru��es
        instrucoes = "Instru��es: \n 1-Inicie o DSSim, carregando rede desejada no formato *.dsp; 2- Conecte-se ao servidor DSSim \n 3- Inicie o servidor " \
                     "para comunica��o com o M�dulo Central; 4- No M�dulo Central, conecte-se com o simulador  "
        lbInstrucoes = tk.Label(figures_frame, text=instrucoes, justify=LEFT)
        lbInstrucoes.pack(padx=0, pady=0, expand=YES, fill=tk.BOTH, anchor=tk.NW, side=tk.LEFT)


    # ------------------------------------------------Frame DSSim-PC-------------------------------------------------- #



        # LabelFrame Maior
        dssim_frame = tk.LabelFrame(frame, text=u'Comunica��o com o DSSim-PC V2.0', bd=2, relief=tk.GROOVE)
        dssim_frame.pack(padx=2, pady=2, expand=tk.YES, fill=tk.BOTH, anchor=tk.N, side=tk.TOP)

        # Frame Auxiliar Principal para organizar Frames auxiliares 1 e 2
        frame_aux_main_dssim = tk.Frame(dssim_frame, bd=0, relief=tk.GROOVE)
        frame_aux_main_dssim.pack(padx=0, pady=0, expand=tk.NO, fill=tk.BOTH, anchor=tk.N, side=tk.TOP)

        # Frame Auxiliar para colocar os c�digos do protocolo
        frame_aux1_dssim = tk.Frame(frame_aux_main_dssim, bd=0, relief=tk.GROOVE)
        frame_aux1_dssim.pack(padx=0, pady=0, expand=tk.NO, fill=tk.BOTH, anchor=tk.NW, side=tk.LEFT)

        frame_aux2_dssim = tk.Frame(frame_aux_main_dssim, bd=0, relief=tk.GROOVE)
        frame_aux2_dssim.pack(padx=0, pady=0, expand=tk.NO, fill=tk.BOTH, anchor=tk.NW, side=tk.RIGHT)

        label_ip_dssim = tk.Label(frame_aux1_dssim, text="TCP/IP:")
        label_ip_dssim.grid(padx=0, pady=0, row=0, column=0)
        self.ip_dssim = tk.StringVar()
        self.ip_dssim.set("127.0.0.1")
        entry_ip_dssim = tk.Entry(frame_aux1_dssim, width=15, textvariable=self.ip_dssim, state="readonly")
        entry_ip_dssim.grid(row=0, column=1, sticky=tk.W)

        label_port_dssim = tk.Label(frame_aux1_dssim, text="TCP/Port:")
        label_port_dssim.grid(padx=0, pady=0, row=0, column=2)
        self.port_dssim = tk.StringVar()
        self.port_dssim.set("6345")
        entry_port_dssim = tk.Entry(frame_aux1_dssim, width=15, textvariable=self.port_dssim, state="readonly")
        entry_port_dssim.grid(row=0, column=3, sticky=tk.W)

        self.bt_conectar_dssim = tk.Button(frame_aux1_dssim, text="Conectar")
        self.bt_conectar_dssim.grid(row=0, column=4, sticky=tk.W, padx=10)

        lbStatus_dssim = tk.Label(frame_aux2_dssim, text="Status:")
        lbStatus_dssim.pack(padx=0, pady=0, expand=tk.NO, fill=tk.X, anchor=tk.N, side=tk.LEFT)

        # Adicionando LED
        self.ledStatus_dssim = LED(master=frame_aux2_dssim, width=17, height=17, appearance=RAISED, status=STATUS_OFF, bd=0, bg=None
                           ,shape=ROUND, outline="black", blink=0, blinkrate=1, orient=None, takefocus=0)
        self.ledStatus_dssim.frame.pack(expand=tk.NO, fill=tk.X, anchor=tk.N, side=tk.RIGHT, padx=0, pady=0)

        # LabelFrame para separar Pacotes Enviados
        dssim_enviados = tk.LabelFrame(dssim_frame, text=u'Pacotes Enviados', bd=2, relief=tk.GROOVE)
        dssim_enviados.pack(padx=2, pady=2, expand=tk.YES, fill=tk.BOTH, anchor=tk.W, side=tk.LEFT)

        self.txtEnv_dssim = tk.Text(dssim_enviados)
        self.txtEnv_dssim.pack(expand=tk.YES, fill=tk.BOTH)
        self.txtEnv_dssim.config(state=DISABLED, wrap=tk.NONE)   #  state: Modo Leitura      wrap: Deixa a quantidade de caracteres por linha livre

        # Scroll Vertical
        scrollY_Env_dssim = tk.Scrollbar(self.txtEnv_dssim, orient=VERTICAL)
        scrollY_Env_dssim.config(command=self.txtEnv_dssim.yview)
        scrollY_Env_dssim.pack(side=tk.RIGHT, fill=tk.Y)

        # Scroll Horizontal
        scrollX_Env_dssim = tk.Scrollbar(self.txtEnv_dssim, orient=HORIZONTAL)
        scrollX_Env_dssim.config(command=self.txtEnv_dssim.xview)
        scrollX_Env_dssim.pack(side=tk.BOTTOM, fill=tk.X)

        self.txtEnv_dssim.config(xscrollcommand=scrollX_Env_dssim.set, yscrollcommand=scrollY_Env_dssim.set)

        # LabelFrame para separar Pacotes Recebidos
        dssim_recebidos = tk.LabelFrame(dssim_frame, text=u'Pacotes Recebidos', bd=2, relief=tk.GROOVE)
        dssim_recebidos.pack(padx=2, pady=2, expand=tk.YES, fill=tk.BOTH, anchor=tk.E, side=tk.LEFT)

        self.txtRec_dssim = tk.Text(dssim_recebidos)
        self.txtRec_dssim.pack(expand=tk.YES, fill=tk.BOTH)
        self.txtRec_dssim.config(state=DISABLED, wrap=tk.NONE)   #  state: Modo Leitura      wrap: Deixa a quantidade de caracteres por linha livre

        # Scroll Vertical
        scrollY_Rec_dssim = tk.Scrollbar(self.txtRec_dssim, orient=VERTICAL)
        scrollY_Rec_dssim.config(command=self.txtRec_dssim.yview)
        scrollY_Rec_dssim.pack(side=tk.RIGHT, fill=tk.Y)

        # Scroll Horizontal
        scrollX_Rec_dssim = tk.Scrollbar(self.txtRec_dssim, orient=HORIZONTAL)
        scrollX_Rec_dssim.config(command=self.txtRec_dssim.xview)
        scrollX_Rec_dssim.pack(side=tk.BOTTOM, fill=tk.X)

        self.txtRec_dssim.config(xscrollcommand=scrollX_Rec_dssim.set, yscrollcommand=scrollY_Rec_dssim.set)

    # ------------------------------------------------Frame M�dulo Central-------------------------------------------- #

        mc_frame = tk.LabelFrame(frame, text=u'Comunica��o com o M�dulo Central', bd=2, relief=tk.GROOVE)
        mc_frame.pack(padx=2, pady=2, expand=tk.YES, fill=tk.BOTH,  anchor=tk.N, side=tk.TOP)

        frame_aux_main_mc = tk.Frame(mc_frame, bd=0, relief=tk.GROOVE)
        frame_aux_main_mc.pack(padx=0, pady=0, expand=tk.NO, fill=tk.BOTH, anchor=tk.N, side=tk.TOP)

        frame_aux1_mc = tk.Frame(frame_aux_main_mc, bd=0, relief=tk.GROOVE)
        frame_aux1_mc.pack(padx=0, pady=0, expand=tk.NO, fill=tk.BOTH, anchor=tk.NW, side=tk.LEFT)

        frame_aux2_mc = tk.Frame(frame_aux_main_mc, bd=0, relief=tk.GROOVE)
        frame_aux2_mc.pack(padx=0, pady=0, expand=tk.NO, fill=tk.BOTH, anchor=tk.NW, side=tk.RIGHT)

        label_port_mc = tk.Label(frame_aux1_mc, text="Porta do Servidor TCP:")
        label_port_mc.grid(padx=0, pady=0, row=0, column=0)
        self.port_mc = tk.StringVar()
        self.port_mc.set("1024")
        entry_port_mc = tk.Entry(frame_aux1_mc, width=15, textvariable=self.port_mc, state="readonly")
        entry_port_mc.grid(row=0, column=1, sticky=tk.W)

        self.bt_criar_servidor_mc = tk.Button(frame_aux1_mc, text="Criar")
        self.bt_criar_servidor_mc.grid(row=0, column=4, sticky=tk.W, padx=10)

        lbStatus_mc = tk.Label(frame_aux2_mc, text="Status:")
        lbStatus_mc.pack(padx=0, pady=0, expand=tk.NO, fill=tk.X, anchor=tk.N, side=tk.LEFT)

        # Adicionando LED
        self.ledStatus_mc = LED(master=frame_aux2_mc, width=17, height=17, appearance=RAISED, status=STATUS_OFF, bd=0, bg=None
                           ,shape=ROUND, outline="black", blink=0, blinkrate=1, orient=None, takefocus=0)
        self.ledStatus_mc.frame.pack(expand=tk.NO, fill=tk.X, anchor=tk.N, side=tk.RIGHT, padx=0, pady=0)

        mc_enviados = tk.LabelFrame(mc_frame, text=u'Pacotes Enviados', bd=2, relief=tk.GROOVE)
        mc_enviados.pack(padx=2, pady=2, expand=tk.YES, fill=tk.BOTH, anchor=tk.W, side=tk.LEFT)

        self.txtEnv_mc = tk.Text(mc_enviados)
        self.txtEnv_mc.pack(expand=tk.YES, fill=tk.BOTH)
        self.txtEnv_mc.config(state=DISABLED, wrap=tk.NONE)   #  state: Modo Leitura      wrap: Deixa a quantidade de caracteres por linha livre

        scrollY_Env_mc = tk.Scrollbar(self.txtEnv_mc, orient=VERTICAL)
        scrollY_Env_mc.config(command=self.txtEnv_mc.yview)
        scrollY_Env_mc.pack(side=tk.RIGHT, fill=tk.Y)

        scrollX_Env_mc = tk.Scrollbar(self.txtEnv_mc, orient=HORIZONTAL)
        scrollX_Env_mc.config(command=self.txtEnv_mc.xview)
        scrollX_Env_mc.pack(side=tk.BOTTOM, fill=tk.X)

        self.txtEnv_mc.config(xscrollcommand=scrollX_Env_mc.set, yscrollcommand=scrollY_Env_mc.set)

        mc_recebidos = tk.LabelFrame(mc_frame, text=u'Pacotes Recebidos', bd=2, relief=tk.GROOVE)
        mc_recebidos.pack(padx=2, pady=2, expand=tk.YES, fill=tk.BOTH, anchor=tk.E, side=tk.LEFT)

        self.txtRec_mc = tk.Text(mc_recebidos)
        self.txtRec_mc.pack(expand=tk.YES, fill=tk.BOTH)
        self.txtRec_mc.config(state=DISABLED, wrap=tk.NONE)   #  state: Modo Leitura      wrap: Deixa a quantidade de caracteres por linha livre

        scrollY_Rec_mc = tk.Scrollbar(self.txtRec_mc, orient=VERTICAL)
        scrollY_Rec_mc.config(command=self.txtRec_mc.yview)
        scrollY_Rec_mc.pack(side=tk.RIGHT, fill=tk.Y)

        scrollX_Rec_mc = tk.Scrollbar(self.txtRec_mc, orient=HORIZONTAL)
        scrollX_Rec_mc.config(command=self.txtRec_mc.xview)
        scrollX_Rec_mc.pack(side=tk.BOTTOM, fill=tk.X)

        self.txtRec_mc.config(xscrollcommand=scrollX_Rec_mc.set, yscrollcommand=scrollY_Rec_mc.set)
    # ---------------------------------------------------------------------------------------------------------------- #

    # ------------------------------------------------Frame Barra de Status ------------------------------------------ #

        self.statusDSSim = tk.StringVar()
        self.statusDSSim.set(u"Status DSSim: Desconectado")
        barraStatus = tk.Label(self.root, textvariable=self.statusDSSim, bd=1, relief=tk.SUNKEN, anchor=tk.SW)
        barraStatus.pack(side=LEFT, fill=None)

        self.statusMC = tk.StringVar()
        self.statusMC.set(u"Status M�dulo Central: Desconectado")
        barraStatus = tk.Label(self.root, textvariable=self.statusMC, bd=1, relief=tk.SUNKEN, anchor=tk.SW)
        barraStatus.pack(side=LEFT, fill=X, expand=tk.YES)


    # --------------------------------------------------Bindings------------------------------------------------------ #

    def define_bindings(self):
        self.bt_conectar_dssim.bind("<Button-1>", self.conecta_dssim)
        self.bt_criar_servidor_mc.bind("<Button-1>", self.cria_servidor_mc_in_thread)




    # --------------------------------------------------FUN��ES------------------------------------------------------- #

    def conecta_dssim(self, event):
        """ M�todo que cria um objeto socket do tipo client para se comunicar com o servidor DSSim."""

        self.dssim_obj = DSSim(self.ip_dssim.get(), int(self.port_dssim.get()), 16384, self)
        if self.dssim_obj.connect() is True:
            self.ledStatus_dssim.turnon()  # Muda o status para ON
            self.ledStatus_dssim.blinkon()  # Ativa o pisca
            self.statusDSSim.set(u"Status DSSim: Conectado")

            self.dssim_obj.armazena_path()
            self.dssim_obj.armazena_nomes_elementos()
            self.dssim_obj.armazena_nomes_barras()
            # self.funcoes_teste()
            self.ledStatus_dssim.store_dssim_obj(self.dssim_obj, self)

    def abre_config(self):

        self.formConfig = formConfiguracoes(self.root, self)

    def cria_servidor_mc_in_thread(self, event):
        """ Roda o m�todo cria_servidor em um Thread separado para n�o travar a interface."""
        self.bt_criar_servidor_mc.config(state='disabled')
        self.thread = threading.Thread(None, self.cria_servidor_mc, None, (), {})
        self.thread.start()

    def cria_servidor_mc(self):
        """ M�todo que cria um objeto socket do tipo server para se comunicar com o cliente MC."""
        self.mc_obj = MC(self, int(self.port_mc.get()), "127.0.0.1", self.dssim_obj)
        if self.mc_obj.cria_servidor() is True:
            self.ledStatus_mc.turnon()   # Muda o status para ON
            self.ledStatus_mc.warn()
            self.ledStatus_mc.blinkon()
            self.statusMC.set(u"Status Servidor para comunica��o com MC: Escutando...")

        if self.mc_obj.modo_escuta() is False:  # Deixa o servidor no modo escuta e aguardando por conex�es
            # se retornar falso, � porque a conex�o foi encerrada, ent�o, devemos reativar o bot�o para criar
            # uma nova conex�o
            self.bt_criar_servidor_mc.config(state='normal')

    # def choose_file(self):
    #
    #     self.file_chosen = tkFileDialog.askopenfilename(filetypes=[('.DSS Files', '*.dss'), ('All Files', '*.*')])
    #     if self.file_chosen == "":  # Se nenhum file foi escolhido
    #         filename = None
    #     else:
    #         self.root.title("OpenDSS Data Visualization" + " " + " - " + " " + os.path.basename(self.file_chosen))
    #         print os.path.abspath(self.file_chosen)
    #
    #         print os.path.dirname(self.file_chosen)
    #         self.v.set(self.file_chosen)    # Seta a minha text variable da label self.directory

    def escreve_mensagem(self, conexao, tipo, mensagem):
        # conexao: dssim ou modulo central (checar classes Conexao e Tipo_Conexao em Auxiliar.py
        # tipo: enviada ou recebida
        print mensagem
        # if conexao == Conexao.DSSIM_CON:
        #     if tipo == Tipo_Conexao.ENV:
        #         self.txtEnv_dssim.config(state=NORMAL)
        #         self.txtEnv_dssim.insert(END, mensagem)
        #         self.txtEnv_dssim.config(state=DISABLED)
        #     elif tipo == Tipo_Conexao.REC:
        #         self.txtRec_dssim.config(state=NORMAL)
        #         self.txtRec_dssim.insert(END, mensagem)
        #         self.txtRec_dssim.config(state=DISABLED)
        # elif conexao == Conexao.MC_CON:
        #     if tipo == Tipo_Conexao.ENV:
        #         self.txtEnv_mc.config(state=NORMAL)
        #         self.txtEnv_mc.insert(tk.END, mensagem)
        #         self.txtEnv_mc.config(state=DISABLED)
        #     elif tipo == Tipo_Conexao.REC:
        #         self.txtRec_mc.config(state=NORMAL)
        #         self.txtRec_mc.insert(tk.END, mensagem)
        #         self.txtRec_mc.config(state=DISABLED)

    def exit_form(self):
        if tkMessageBox.askokcancel("Sair", "Voc� realmente deseja sair?"):
            self.root.destroy()

    # --------------------------------------------------DSSIM Control----------------------------------------------- #

    def funcoes_teste(self):
        if not self.dssim_obj:
            ctypes.windll.user32.MessageBoxW(0, u"Conex�o TCP n�o encontrada!", u"Conex�o DSSimPC-v2.0", 0)
        else:
            self.dssim_obj.get_last_simulation_type()
            self.dssim_obj.get_switch_state("275CF000707709_id6464")
            print "oi"
            # self.dssim_obj.get_simulation_time('s')
            # self.dssim_obj.get_simulation_time('m')
            # self.dssim_obj.get_simulation_time('h')
            # self.dssim_obj.get_simulation_time('d')
            #
            # self.dssim_obj.get_all_nodes_voltages('kV')
            #
            # self.dssim_obj.get_all_nodes_voltages('pu')
            # self.dssim_obj.send_dss_command("get earthmodel")
            #
            # self.dssim_obj.get_bus_voltages("29")
            # self.dssim_obj.get_elem_currents("line.l31")
            # self.dssim_obj.get_elem_voltages("transformer.reg1a", 2)
            # self.dssim_obj.get_switch_state("sw2")
            #
            # self.dssim_obj.get_total_powers("line.l19", 1)
            # self.dssim_obj.get_total_powers("line.l19", 2)
            # self.dssim_obj.get_total_powers("line.l19", None)
            # self.dssim_obj.get_phase_powers("line.l19", 1, 1)
            # self.dssim_obj.get_phase_powers("line.l19", 1, 2)
            # self.dssim_obj.get_phase_powers("line.l19", 1, 3)
            # self.dssim_obj.get_phase_powers("line.l19", 2, 1)
            # self.dssim_obj.get_phase_powers("line.l19", 2, 2)
            # self.dssim_obj.get_phase_powers("line.l19", 2, 3)
            #
            # self.dssim_obj.get_transformer_tap("transformer.reg1a", 1)
            # self.dssim_obj.get_transformer_tap("transformer.reg1a", 2)
            #
            # self.dssim_obj.get_capacitor_state("capacitor.c90b")
            # self.dssim_obj.get_capacitor_kvar("capacitor.c90b")
            # self.dssim_obj.get_last_event()

    # ---------------------------------------------------------------------------------------------------------------- #


if __name__ == "__main__":
    """Start the GUI by default."""
    Form.main()
