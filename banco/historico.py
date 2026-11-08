"""
HISTÓRICO DE MOVIMENTAÇÕES
==========================
Registra cada operação do estoque na aba "Movimentações" e permite consultá-las.

Como é usado pelos outros módulos:
    planilha, aba, aba_mov = abrir()
    ... faz a operação ...
    registrar(planilha, config.SAIDA, "Caneta", 5, saldo=35, valor=2.5, observacao="Pedido 12")
    salvar(planilha)          # grava a operação E o registro juntos

Como o registro é gravado no mesmo salvar() da operação, não existe o caso de
"a operação aconteceu mas não ficou no histórico" (ou o contrário).
"""
from . import config
from .modelos import Registro
from .planilha import abrir_leitura, agora

# Tipos que AUMENTAM ou DIMINUEM o total físico (usado para mostrar + ou −)
TIPOS_ENTRADA = (config.ENTRADA, config.IMPORTACAO)
TIPOS_SAIDA = (config.SAIDA, config.BAIXA, config.EXCLUSAO)


def registrar(planilha, tipo, objeto, quantidade, saldo, valor, observacao=""):
    """Acrescenta uma linha no histórico (na memória — grava no salvar())."""
    aba = planilha[config.ABA_HIST]
    aba.append([agora(), tipo, objeto, quantidade, saldo, valor, (observacao or "").strip()])
    aba.cell(row=aba.max_row, column=1).number_format = config.FORMATO_DATA


def quantidade_com_sinal(registro):
    """Texto da quantidade com sinal: "+10" (entrada), "−5" (saída), "3" (reserva)."""
    q = registro.quantidade or 0
    if registro.tipo in TIPOS_ENTRADA:
        return f"+{q}"
    if registro.tipo in TIPOS_SAIDA:
        return f"−{q}"
    if registro.tipo == config.EDICAO:
        return f"+{q}" if q > 0 else ("0" if q == 0 else f"−{abs(q)}")
    return str(q)


def listar_historico():
    """Todos os registros, do mais novo para o mais antigo (lista de Registro)."""
    planilha = abrir_leitura()
    try:
        registros = []
        for linha in planilha[config.ABA_HIST].iter_rows(min_row=2, max_col=7, values_only=True):
            data, tipo, objeto, qtd, saldo, valor, obs = (tuple(linha) + (None,) * 7)[:7]
            if tipo is None:
                continue  # linha vazia
            registros.append(Registro(data, tipo, str(objeto or ""), qtd or 0, saldo or 0, valor or 0, obs or ""))
    finally:
        planilha.close()
    return registros[::-1]
