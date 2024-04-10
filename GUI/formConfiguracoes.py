###  # -*- coding: iso-8859-15 -*-

import os
import tkFileDialog
import tkMessageBox
import Tkinter as tk
from LED import *
from Fontes.DSSIM import *
from Fontes.Auxiliar import *


class formConfiguracoes():

    # @classmethod
    # def main(cls):
        # janela = tk.Toplevel(root)
        # config_janela = cls(root)
        # root.mainloop()   # é uma função da classe Tkinter.Tk, a qual o objeto root pertence. É essa função que mantém
        #  a janela sempre visível e não deixa ela fechar
        # return config_janela

    def __init__(self, root, form_principal):   # Não entendi direito
        # tk.Frame.__init__(self, root)   # Não entendi isso aqui
        self.janela = tk.Toplevel(root)
        # self.janela.config(width=tk.FALSE, height=tk.FALSE)
        self.janela.protocol('WM_DELETE_WINDOW', self.exit_form)
        self.formPrincipal = form_principal

        self._setup()   # Inicializa propriedades visuais do Form
        self.define_bindings()   # Define os bindings dos widgets a eventos


    def _setup(self, **kwargs):
        self.janela.title(u"Configurações de Conexão")
        # self.janela.geometry('250x200')
        # self.root.iconbitmap('icons/main4.ico')

        lbfDssim = tk.LabelFrame(self.janela, text=u'DSSim-PC V2.0', bd=2, relief=tk.GROOVE)
        lbfDssim.pack(padx=2, pady=2, expand=tk.NO, fill=tk.BOTH, anchor=tk.N, side=tk.TOP)

        lbTCP_IP = tk.Label(lbfDssim, text=u"TCP/IP:")
        lbTCP_IP.grid(padx=0, pady=0, row=0, column=0, sticky=tk.W)

        self.ip_dssim = tk.StringVar()
        # self.ip_dssim.set("127.0.0.1")
        self.ip_dssim.set(self.formPrincipal.ip_dssim.get())

        enTCP_IP = tk.Entry(lbfDssim, textvariable=self.ip_dssim)
        enTCP_IP.grid(padx=0, pady=0, row=0, column=1, sticky=tk.E)

        self.port_dssim = tk.StringVar()
        # self.port_dssim.set("1234")
        self.port_dssim.set(self.formPrincipal.port_dssim.get())

        lbTCP_PORT = tk.Label(lbfDssim, text=u"TCP/PORT:")
        lbTCP_PORT.grid(padx=1, pady=1, row=1, column=0, sticky=tk.W)

        enTCP_PORT = tk.Entry(lbfDssim, textvariable=self.port_dssim)
        enTCP_PORT.grid(padx=1, pady=1, row=1, column=1, sticky=tk.E)

        lbfMc = tk.LabelFrame(self.janela, text=u'Módulo Central', bd=2, relief=tk.GROOVE)
        lbfMc.pack(padx=2, pady=2, expand=tk.NO, fill=tk.BOTH, anchor=tk.N, side=tk.TOP)

        lbPortMC = tk.Label(lbfMc, text=u"Porta do Servidor:")
        lbPortMC.grid(padx=1, pady=1, row=0, column=0)

        self.port_mc = tk.StringVar()
        # self.port_mc.set("1234")
        self.port_mc.set(self.formPrincipal.port_mc.get())

        enTCP_PORTmc = tk.Entry(lbfMc, width=15, textvariable=self.port_mc)
        enTCP_PORTmc.grid(padx=1, pady=1, row=0, column=1, sticky=tk.W)


        # Botões

        frameAux = tk.Frame(self.janela)
        frameAux.pack(anchor=tk.S)

        self.btConfirma = tk.Button(frameAux, text="Confirmar")
        self.btConfirma.grid(row=0, column=0, sticky=tk.W)

        self.btCancela = tk.Button(frameAux, text="Cancelar")
        self.btCancela.grid(row=0, column=1, sticky=tk.E)

    # --------------------------------------------------Bindings------------------------------------------------------ #

    def define_bindings(self):
        self.btConfirma.bind("<Button-1>", self.altera_ip)
        self.btCancela.bind("<Button-1>", self.exit_direct)

    # --------------------------------------------------FUNÇÕES------------------------------------------------------- #

    def altera_ip(self, event):
        """Esse método deve ler o valores inseridos no Form de Configurações e atualizar o conteúdo do Form Principal"""
        self.formPrincipal.ip_dssim.set(self.ip_dssim.get())
        self.formPrincipal.port_dssim.set(self.port_dssim.get())
        self.formPrincipal.port_mc.set(self.port_mc.get())

        self.janela.destroy()

    def exit_direct(self, event):
        self.janela.destroy()

    def exit_form(self):
        if tkMessageBox.askokcancel("Sair", "Você realmente deseja sair?"):
            self.janela.destroy()




