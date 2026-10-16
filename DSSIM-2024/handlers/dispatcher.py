import datetime
import struct
import logging

logger = logging.getLogger('server.dispatcher')

class CommandDispatcher:
    def __init__(self, dssim_obj):
        self.dssim_obj = dssim_obj

        # Mapeamento dinâmico das funções (Rotas) tratadoras (Handlers)
        # Chave: string do código da função -> Valor: método responsável
        self.rotas = {
            "99": self.handle_get_id,
            "1":  self.handle_get_registers,
            "3":  self.handle_switch_state,
            "6":  self.handle_tap_change,
            "7":  self.handle_tap_change,
            "11": self.handle_capacitor_state
        }

    def process(self, message: str) -> str:
        """
        Ponto de entrada único para todas as mensagens.
        Substitui a antiga função gigante `process_data`.
        """
        if not self.dssim_obj:
            return "nao existe objeto dssim"

        msg_dividida = message.split(";")
        funcao = msg_dividida[0]

        logger.debug(f"Processando função: {funcao}")

        # Busca o handler correspondente. Se não existir, usa o fallback.
        handler = self.rotas.get(funcao, self.handle_unknown)

        try:
            # Executa o handler isolado e retorna a resposta
            return handler(msg_dividida)
        except Exception as e:
            logger.error(f"Erro ao processar função {funcao}: {e}")
            return ""

    # ---------------------------------------------------------
    # Handlers Específicos Isolados
    # ---------------------------------------------------------

    def handle_get_id(self, msg_dividida: list) -> str:
        """Trata a função 99: Retorna ID do equipamento por meio de código."""
        funcao = msg_dividida[0]
        tipo_equipamento = msg_dividida[-3]
        codigo_equipamento = msg_dividida[-2]

        id_equipamento = self.dssim_obj.retorna_id(codigo_equipamento, tipo_equipamento)

        qtde_bytes = 43
        msg_retornada = [chr(0)] * qtde_bytes
        now = datetime.datetime.now()

        msg_retornada[0] = chr(int(funcao))
        msg_retornada[1] = chr(qtde_bytes)
        msg_retornada[2] = chr(0)
        msg_retornada[3] = chr(now.hour)
        msg_retornada[4] = chr(now.minute)
        msg_retornada[5] = chr(now.second)
        msg_retornada[6] = chr(int(tipo_equipamento))

        # Id do equipamento (Convertendo para 4 bytes Little Endian)
        id_bytes = struct.pack('<Q', id_equipamento)
        msg_retornada[7:11] = [chr(b) for b in id_bytes[:4]]

        # Código do Equipamento
        for i, char in enumerate(codigo_equipamento):
            msg_retornada[11 + i] = char

        return "".join(str(x) for x in msg_retornada)

    def handle_get_registers(self, msg_dividida: list) -> str:
        """Trata a função 1: MC solicita registros de equipamentos."""
        # A lógica gigante da conversão de bytes virá para cá,
        # futuramente otimizada com um PayloadBuilder.
        return "reposta_construida"

    def handle_switch_state(self, msg_dividida: list) -> str:
        """Trata a função 3: Alteração de Estado de Chave."""
        # Lógica isolada de chaves
        return "reposta_chave"

    def handle_tap_change(self, msg_dividida: list) -> str:
        """Trata as funções 6 e 7: Alteração de Tap."""
        # Lógica isolada de taps
        return "resposta_tap"

    def handle_capacitor_state(self, msg_dividida: list) -> str:
        """Trata a função 11: Alteração do Estado de BC."""
        # Lógica isolada de banco de capacitores
        return "resposta_capacitor"

    def handle_unknown(self, msg_dividida: list) -> str:
        """Fallback para funções não mapeadas."""
        funcao = msg_dividida[0]
        logger.warning(f"Função {funcao} não reconhecida ou não implementada.")
        return ""