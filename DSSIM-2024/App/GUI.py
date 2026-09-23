import tkinter as tk
import customtkinter as ctk
import logging
import os
import sys
import threading

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import server


class _ChatLogHandler(logging.Handler):
    def __init__(self, append_callback):
        super().__init__()
        self.append_callback = append_callback

    def emit(self, record):
        message = self.format(record)
        self.append_callback(message)


class RemoteControlServerApp(ctk.CTk):
    """Interface gráfica para servidor de controle remoto.

    Esta classe cria uma janela responsiva com visor de conversa, campo de
    entrada e botões de comando rápido. A lógica de envio real deve ser
    implementada posteriormente nas funções placeholder.
    """

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Servidor de Controle Remoto")
        self.geometry(self._center_window_to_display(800, 600, self._get_window_scaling()))
        # self.geometry("800x600")
        self.minsize(700, 500)
        # self.attribute("-topmost", True)  # Mantém a janela sempre no topo

        self._configure_grid()
        self._create_widgets()

        self._attach_server_logger()
        self._start_server_thread()

    def _center_window_to_display(self, width: int, height: int, scale_factor: float = 1.0):
        """Centers the window to the main display/monitor"""
        screen_width = self.winfo_screenwidth()
        # print('screen_width: ', screen_width)
        screen_height = self.winfo_screenheight()
        # print('screen_height: ', screen_height)
        x = int(((screen_width/2) - (width/2)) * scale_factor)
        y = int(((screen_height/2) - (height/1.5)) * scale_factor)
        return f"{width}x{height}+{x}+{y}"

    def _configure_grid(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

    def _create_widgets(self):
        self.chat_frame = ctk.CTkFrame(self, corner_radius=0)
        self.chat_frame.grid(row=0, column=0, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=0)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(1, weight=0)

        self.side_panel = ctk.CTkFrame(self, corner_radius=0)
        self.side_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=10)
        self.side_panel.grid_columnconfigure(0, weight=1)
        self.side_panel.grid_rowconfigure(0, weight=0)
        self.side_panel.grid_rowconfigure(1, weight=0)
        self.side_panel.grid_rowconfigure(2, weight=0)
        self.side_panel.grid_rowconfigure(3, weight=0)
        self.side_panel.grid_rowconfigure(4, weight=0)
        self.side_panel.grid_rowconfigure(5, weight=1)

        self.chat_textbox = ctk.CTkTextbox(self.chat_frame, wrap="word", state="disabled")
        self.chat_textbox.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # self.chat_scrollbar = ctk.CTkScrollbar(
        #     self.chat_frame, orientation="vertical", command=self.chat_textbox.yview
        # )
        # self.chat_textbox.configure(yscrollcommand=self.chat_scrollbar.set)
        # self.chat_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        self.bottom_frame = ctk.CTkFrame(self.chat_frame, corner_radius=0)
        self.bottom_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=0)

        self.command_entry = ctk.CTkEntry(
            self.bottom_frame,
            placeholder_text="Digite um comando e pressione Enviar...",
        )
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=5)
        self.command_entry.bind("<Return>", lambda event: self.enviar_comando())

        self.send_button = ctk.CTkButton(
            self.bottom_frame,
            text="Enviar",
            command=self.enviar_comando,
        )
        self.send_button.grid(row=0, column=1, sticky="e", pady=5)

        self._create_shortcut_buttons()
        self._create_trafo_frame()

    def _create_trafo_frame(self):
        self.trafo_frame = ctk.CTkFrame(self.side_panel, corner_radius=0)
        self.trafo_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=(10, 0))
        self.trafo_frame.grid_rowconfigure(0, weight=0)
        self.trafo_frame.grid_rowconfigure(1, weight=0)
        self.trafo_frame.grid_rowconfigure(2, weight=0)
        self.trafo_frame.grid_rowconfigure(3, weight=1)
        # self.trafo_frame.grid_columnconfigure(0, weight=1)
        # self.trafo_frame.grid_columnconfigure(1, weight=0)
        # self.trafo_frame.grid_columnconfigure(2, weight=1)

        label = ctk.CTkLabel(self.trafo_frame, text="Transformador", anchor="w")
        label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.trafo_entry = ctk.CTkEntry(
            self.trafo_frame,
            placeholder_text="Nome do transformador...",
            width=180,
        )
        self.trafo_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.trafo_entry.bind("<Return>", lambda event: self.enviar_tap())

        self.tap_entry = ctk.CTkEntry(
            self.trafo_frame,
            placeholder_text="Tap (-16 a 16)...",
            width=80
        )
        self.tap_entry.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.tap_entry.bind("<Return>", lambda event: self.enviar_tap())

        self.bt_send_tap = ctk.CTkButton(
            self.trafo_frame,
            text="Enviar Tap",
            command=self.enviar_tap,
        )
        self.bt_send_tap.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))

    def _create_shortcut_buttons(self):
        label = ctk.CTkLabel(self.side_panel, text="Comandos Rápidos", anchor="w")
        label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.bt_comando_1 = ctk.CTkButton(
            self.side_panel,
            text="Tap 0",
            command=self.botao_programavel_1,
        )
        self.bt_comando_1.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.bt_comando_2 = ctk.CTkButton(
            self.side_panel,
            text="Comando 2",
            command=self.botao_programavel_2,
        )
        self.bt_comando_2.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.bt_comando_3 = ctk.CTkButton(
            self.side_panel,
            text="Comando 3",
            command=self.botao_programavel_3,
        )
        self.bt_comando_3.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        self.bt_comando_4 = ctk.CTkButton(
            self.side_panel,
            text="Comando 4",
            command=self.botao_programavel_4,
        )
        self.bt_comando_4.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

    def enviar_comando(self):
        """Lê o comando do campo de entrada e adiciona ao visor de conversa."""
        comando = self.command_entry.get().strip()
        if not comando:
            return

        self._append_chat(f"[Inserido] > {comando}")
        self.command_entry.delete(0, ctk.END)

        thread = threading.Thread(target=self._send_dss_command, args=(comando,), daemon=True)
        thread.start()

    def enviar_tap(self):
        """Lê os campos de entrada e adiciona ao visor de conversa.

        Keyword arguments:
        trafo -- Nome do transformador (string)
        tap -- Valor do tap (float) de -16 a 16, convertido para o intervalo 1 a 33 antes de enviar ao DSSIM.
        """
        trafo = "Transformer." + self.trafo_entry.get().strip()
        if not trafo:
            return

        tap = self.tap_entry.get().strip()
        if not tap:
            return

        try:
            tap = float(tap)
        except ValueError:
            self._append_chat(f"[Erro] < Valor inválido para tap: {tap}")
            return

        self._append_chat(f"[Inserido] > {trafo} - tap: {tap}")
        self.tap_entry.delete(0, ctk.END)

        thread = threading.Thread(target=self._varia_tap, args=(trafo, tap), daemon=True)
        thread.start()

    def _varia_tap(self, trafo: str, tap: float):
        """Envia o comando ao DSSIM e exibe a resposta no visor."""
        if tap < -16 or tap > 16:
            self.after(0, lambda: self._append_chat(f"[Erro] < Valor de tap fora do intervalo permitido (-16 a 16): {tap}"))
            return

        if not tap.is_integer():
            self.after(0, lambda: self._append_chat(f"[Erro] < Valor de tap deve ser um número inteiro: {tap}"))
            return

        tap = tap + 17.0
        try:
            resposta = server.dssim_obj.varia_tap(trafo, tap)
            if isinstance(resposta, bytes):
                try:
                    resposta_text = resposta.decode('utf-8', errors='replace')
                except Exception:
                    resposta_text = repr(resposta)
            else:
                resposta_text = str(resposta)

            self.after(0, lambda: self._append_chat(f"[Resposta] < {resposta_text}"))
        except Exception as exc:
            self.after(0, lambda: self._append_chat(f"[Erro] < Falha ao enviar comando: {exc}"))

    def _send_dss_command(self, comando: str):
        """Envia o comando ao DSSIM e exibe a resposta no visor."""
        try:
            resposta = server.dssim_obj.send_dss_command(comando)
            if isinstance(resposta, bytes):
                try:
                    resposta_text = resposta.decode('utf-8', errors='replace')
                except Exception:
                    resposta_text = repr(resposta)
            else:
                resposta_text = str(resposta)

            self.after(0, lambda: self._append_chat(f"[Resposta] < {resposta_text}"))
        except Exception as exc:
            self.after(0, lambda: self._append_chat(f"[Erro] < Falha ao enviar comando: {exc}"))

    def _attach_server_logger(self):
        """Adiciona o logger do servidor ao chat para mostrar mensagens do server.py."""
        handler = _ChatLogHandler(self._append_chat)
        handler.setFormatter(logging.Formatter("[server] %(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S"))
        handler.setLevel(logging.INFO)
        server.logger.addHandler(handler)
        server.logger.setLevel(logging.INFO)
        if hasattr(server, 'equipment_logger'):
            server.equipment_logger.addHandler(handler)
            server.equipment_logger.setLevel(logging.INFO)

    def _start_server_thread(self):
        """Inicia o servidor TCP do `server.py` em uma thread separada."""
        thread = threading.Thread(target=server.start_server, daemon=True)
        thread.start()

    def _append_chat(self, mensagem: str):
        """Insere nova mensagem no visor de conversa e garante rolagem automática."""
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.insert(ctk.END, mensagem + "\n")
        self.chat_textbox.configure(state="disabled")
        self.chat_textbox.see(ctk.END)

    def botao_programavel_1(self):
        """Placeholder para lógica do Botão Programável 1."""
        self._append_chat("[Ação] > Botão Programável 1 acionado")

    def botao_programavel_2(self):
        """Placeholder para lógica do Botão Programável 2."""
        self._append_chat("[Ação] > Botão Programável 2 acionado")

    def botao_programavel_3(self):
        """Placeholder para lógica do Botão Programável 3."""
        self._append_chat("[Ação] > Botão Programável 3 acionado")

    def botao_programavel_4(self):
        """Placeholder para lógica do Botão Programável 4."""
        self._append_chat("[Ação] > Botão Programável 4 acionado")


def main():
    app = RemoteControlServerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
