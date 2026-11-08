"""
MODELOS DE DADOS
================
Define o "formato" das informações que circulam pelo programa. Em vez de passar
listas soltas como ("Caneta", 40, 2.5), o código usa objetos com nomes claros:
item.objeto, item.quantidade, item.disponivel...

📚 Conceito usado: @dataclass
   É um jeito curto de criar uma classe que só guarda dados. O Python cria
   sozinho o __init__, então Item("Caneta", 40, 2.5) já funciona.
"""
from dataclasses import dataclass
from datetime import datetime


class ErroEstoque(Exception):
    """Erro "esperado", com uma mensagem amigável para mostrar ao usuário.

    Exemplo: tentar retirar mais do que existe. As funções do banco usam
    `raise ErroEstoque("mensagem")` e quem chamou (menu ou janela) mostra a
    mensagem, em vez de o programa fechar com um erro técnico.
    """


@dataclass
class Item:
    """Um produto do estoque, já com os números de reserva e bloqueio somados."""

    objeto: str          # nome do produto
    quantidade: int      # total físico (inclui reservado e bloqueado)
    valor: float         # valor unitário em reais
    reservado: int = 0   # soma das reservas ATIVAS deste produto
    bloqueado: int = 0   # soma dos bloqueios ATIVOS deste produto

    # @property: é calculado na hora, mas usado como campo → item.disponivel
    @property
    def disponivel(self):
        """O que realmente pode ser usado: total − reservado − bloqueado."""
        return self.quantidade - self.reservado - self.bloqueado

    @property
    def valor_total(self):
        """Quanto vale tudo deste produto (quantidade × valor unitário)."""
        return self.quantidade * self.valor


@dataclass
class Movimento:
    """Uma linha da aba "Reservas e Bloqueios"."""

    id: str              # ex.: "R0001" (reserva) ou "B0001" (bloqueio)
    tipo: str            # config.RESERVA ou config.BLOQUEIO
    objeto: str          # nome do produto
    quantidade: int
    referencia: str      # nº do pedido (reserva) ou motivo (bloqueio)
    data: datetime       # quando foi criado
    status: str          # config.ATIVO, config.LIBERADO ou config.BAIXA
    data_fim: datetime   # quando foi liberado/baixado (vazio se ainda ativo)


@dataclass
class Requisicao:
    """Uma linha da aba "Requisições" (pedido de compra/reposição)."""

    id: str              # ex.: "RQ0001"
    objeto: str
    quantidade: int      # quanto foi pedido
    atendida: int        # quanto já chegou
    solicitante: str     # quem/qual setor pediu
    observacao: str
    data: datetime       # quando foi pedida
    status: str          # config.REQ_ABERTA, REQ_PARCIAL, REQ_ATENDIDA ou REQ_CANCELADA
    data_atendimento: datetime

    @property
    def falta(self):
        """Quanto ainda não chegou."""
        return max(self.quantidade - self.atendida, 0)


@dataclass
class Registro:
    """Uma linha da aba "Movimentações" (histórico)."""

    data: datetime
    tipo: str            # config.ENTRADA, config.SAIDA, config.EDICAO...
    objeto: str
    quantidade: int      # quanto foi movimentado (na Edição, a diferença)
    saldo: int           # total físico do produto depois da operação
    valor: float         # valor unitário no momento
    observacao: str
