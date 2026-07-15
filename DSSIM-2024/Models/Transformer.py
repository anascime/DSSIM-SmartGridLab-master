# -*- coding: UTF-8 -*-
'''
@date: 14-07-2026
@description: Transformer model for DSSIM 🌎
@author: Anascime
'''
from dataclasses import dataclass, field, fields
from typing import List, Optional, Union


@dataclass
class Transformer:
    """
    Contêiner de dados (Data Container) que representa fielmente o elemento
    'Transformer' do OpenDSS. Não possui chamadas de API ativas e não interage
    com o ambiente em tempo de simulação, focando apenas na parametrização estática.
    """
    # -------------------------------------------------------------------------
    # IDENTIFICAÇÃO
    # -------------------------------------------------------------------------
    name: str  # Nome do transformador. Não possui default, sendo obrigatório.

    # -------------------------------------------------------------------------
    # PROPRIEDADES GERAIS DO EQUIPAMENTO
    # -------------------------------------------------------------------------
    phases: int = 3
    """Número de fases do transformador. Padrão = 3."""

    windings: int = 2
    """Número total de enrolamentos. Padrão = 2."""

    # -------------------------------------------------------------------------
    # PROPRIEDADES DE ENROLAMENTO ÚNICO (Modo Stateful)
    # Estas propriedades se referem ao enrolamento ativo definido por 'wdg'.
    # -------------------------------------------------------------------------
    wdg: int = 1
    """Define o índice do enrolamento ativo para as propriedades abaixo (1..windings)."""

    bus: Optional[str] = None
    """Nome da barra (com ou sem nós) conectada ao enrolamento ativo."""

    conn: str = "wye"
    """Conexão do enrolamento ativo: 'wye' (estrela) ou 'delta' (triângulo)."""

    kv: Optional[float] = None
    """Tensão nominal do enrolamento ativo em kV (linha-linha para 3 fases; linha-neutro para 1 fase)."""

    kva: Optional[float] = None
    """Potência nominal base (kVA) do enrolamento ativo."""

    tap: float = 1.0
    """Posição atual do tap em pu para o enrolamento ativo. Padrão = 1.0."""

    pct_r: float = 0.2
    """Resistência em porcentagem (%) na base de kVA do enrolamento ativo. Padrão = 0.2."""

    rneut: float = -1.0
    """Resistência de aterramento do neutro (ohms). -1.0 significa aterramento sólido. Padrão = -1.0."""

    xneut: float = 0.0
    """Reatância de aterramento do neutro (ohms). Padrão = 0.0."""

    # -------------------------------------------------------------------------
    # PROPRIEDADES MULTI-ENROLAMENTOS (Modo Array)
    # Alternativa mais concisa à parametrização por 'wdg'.
    # -------------------------------------------------------------------------
    buses: Optional[List[str]] = None
    """Vetor de barras de conexão para todos os enrolamentos."""

    conns: Optional[List[str]] = None
    """Vetor de conexões ('wye', 'delta') para todos os enrolamentos."""

    kvs: Optional[List[float]] = None
    """Vetor de tensões nominais (kV) para todos os enrolamentos."""

    kvas: Optional[List[float]] = None
    """Vetor de potências (kVA) para todos os enrolamentos."""

    taps: Optional[List[float]] = None
    """Vetor de taps atuais em pu para todos os enrolamentos."""

    pct_rs: Optional[List[float]] = None
    """Vetor com as resistências percentuais (%Rs) para todos os enrolamentos."""

    # -------------------------------------------------------------------------
    # IMPEDÂNCIAS DE CURTO-CIRCUITO E VAZAMENTO
    # -------------------------------------------------------------------------
    xhl: float = 7.0
    """Reatância de curto-circuito entre os enrolamentos 1 (High) e 2 (Low) em %."""

    xht: float = 35.0
    """Reatância de curto-circuito entre os enrolamentos 1 (High) e 3 (Tertiary) em %."""

    xlt: float = 30.0
    """Reatância de curto-circuito entre os enrolamentos 2 (Low) e 3 (Tertiary) em %."""

    xscarray: Optional[List[float]] = None
    """Array das reatâncias de curto-circuito (%) para transformadores com mais de 3 enrolamentos."""

    # -------------------------------------------------------------------------
    # PERDAS, MAGNETIZAÇÃO E CORREÇÕES (PPM)
    # -------------------------------------------------------------------------
    pct_noloadloss: float = 0.0
    """Perdas a vazio (no núcleo) especificadas em porcentagem. Padrão = 0.0."""

    pct_loadloss: float = 0.0
    """Perdas em carga (no cobre) em plena potência. Geralmente omitido se %r for parametrizado."""

    pct_imag: float = 0.0
    """Corrente de magnetização em porcentagem. Padrão = 0.0."""

    ppm_antifloat: float = 1.0
    """Condutância minúscula adicionada à diagonal da matriz Y para evitar nós flutuantes (em partes por milhão)."""

    rdcohms: float = 0.0
    """Resistência em corrente contínua (CC) para análises GIC (Correntes Induzidas Geomagneticamente)."""

    # -------------------------------------------------------------------------
    # DADOS TÉRMICOS E DE CLASSIFICAÇÃO (RATINGS)
    # -------------------------------------------------------------------------
    thermal: float = 2.0
    """Constante de tempo térmico do transformador em horas. Padrão = 2.0."""

    n: float = 0.8
    """Expoente de capacidade térmica m (para equação de resfriamento/aquecimento)."""

    m: float = 0.8
    """Expoente térmico para cálculos de ponto quente (hot spot)."""

    flrise: float = 65.0
    """Elevação de temperatura em carga total (plena carga) em °C. Padrão = 65."""

    hsrise: float = 15.0
    """Elevação de temperatura do ponto mais quente em relação à temperatura de plena carga (°C)."""

    normhkva: Optional[float] = None
    """Limite máximo de kVA normal admitido pelo transformador."""

    emerghkva: Optional[float] = None
    """Limite máximo de emergência do transformador em kVA."""

    normamps: Optional[float] = None
    """Limite normal em Amperes para cálculos simplificados de carga suportada."""

    emergamps: Optional[float] = None
    """Limite de emergência em Amperes."""

    seasons: int = 1
    """Número de estações do ano se os ratings variarem sazonalmente."""

    ratings: Optional[List[float]] = None
    """Vetor de limites normais em Amperes considerando sazonalidade (se aplicável)."""

    # -------------------------------------------------------------------------
    # CONFIGURAÇÕES E LIMITES DE TAP
    # -------------------------------------------------------------------------
    maxtap: float = 1.10
    """Posição máxima permitida para o tap em p.u. Padrão = 1.10."""

    mintap: float = 0.90
    """Posição mínima permitida para o tap em p.u. Padrão = 0.90."""

    numtaps: int = 32
    """Número total de steps de tap disponíveis (do mínimo ao máximo). Padrão = 32."""

    # -------------------------------------------------------------------------
    # DADOS OPERACIONAIS E CONFIABILIDADE
    # -------------------------------------------------------------------------
    sub: str = "n"
    """Designa se o transformador está na subestação principal ('y' ou 'n')."""

    subname: str = ""
    """Nome da subestação (se sub='y')."""

    bank: str = ""
    """Nome do banco ao qual o transformador pertence (usado por controladores RegControl)."""

    xfmrcode: str = ""
    """Nome de um XfmrCode predefinido com propriedades em formato de catálogo."""

    leadlag: str = "Lag"
    """Convenção de defasagem angular ('Lead' para Euro ou 'Lag' para ANSI)."""

    xrconst: bool = False
    """Define se a relação X/R permanece constante em simulações harmônicas."""

    core: str = "shell"
    """Geometria do núcleo: 'shell', '1-phase', '3-leg', etc."""

    faultrate: float = 0.1
    """Número de falhas projetadas por ano (análises de confiabilidade)."""

    pctperm: float = 20.0
    """Porcentagem de falhas que se tornam eventos permanentes. Padrão = 20.0."""

    repair: float = 3.0
    """Tempo estimado de reparo em horas. Padrão = 3.0."""

    basefreq: float = 60.0
    """Frequência base de operação em Hertz."""

    enabled: bool = True
    """Sinaliza se o transformador está ativo no circuito da simulação (True/False)."""

    def to_opendss_cmd(self) -> str:
        """
        Converte as instâncias da classe em uma string de comando interpretável
        pela sintaxe da interface COM/Direct do OpenDSS. Omite valores nulos
        ou iguais aos defaults do próprio OpenDSS para manter os scripts limpos.
        """
        # Mapeamento do nome python para o parâmetro idêntico na sintaxe OpenDSS.
        prop_mapping = {
            "pct_r": "%r",
            "pct_rs": "%Rs",
            "pct_noloadloss": "%noloadloss",
            "pct_loadloss": "%loadloss",
            "pct_imag": "%imag"
        }

        cmd = [f"New Transformer.{self.name}"]

        # Iterar dinamicamente sobre todos os atributos da classe via reflexão
        for f in fields(self):
            if f.name == "name":
                continue

            value = getattr(self, f.name)

            # Pula campos não definidos ou que se encontram em seu respectivo valor padrão.
            if value is None or value == f.default:
                continue

            # Identifica o nome nativo da propriedade para o OpenDSS
            dss_prop_name = prop_mapping.get(f.name, f.name)

            # Manipulação de conversão de tipos (Listas e Booleanos)
            if isinstance(value, list):
                # Representação em OpenDSS array de colchetes ex: kVs=[13.8, 0.22]
                str_list = ", ".join(str(item) for item in value)
                cmd.append(f"{dss_prop_name}=[{str_list}]")

            elif isinstance(value, bool):
                # Conversão explícita de Boolean para 'Yes' / 'No' suportados pelo OpenDSS
                str_bool = "Yes" if value else "No"
                cmd.append(f"{dss_prop_name}={str_bool}")

            else:
                # String, float, ints genéricos
                cmd.append(f"{dss_prop_name}={value}")

        return " ".join(cmd)