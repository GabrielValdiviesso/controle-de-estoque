"""
TESTES DE CONSISTÊNCIA E ENTRADAS INVÁLIDAS
===========================================
Regra do case: "uma operação inválida não deve deixar o estoque em um
estado inconsistente".

A prova mais forte disso é comparar o ARQUIVO antes e depois: se a operação
foi recusada, a planilha precisa estar idêntica, byte a byte.
"""
import hashlib

import pytest
from openpyxl import Workbook

import banco
from banco import ErroEstoque
from conftest import situacao


def impressao_digital(arquivo):
    """Resumo (hash) do conteúdo do arquivo: muda se QUALQUER byte mudar."""
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


# ================================================================== quantidades inválidas
# Bug real encontrado na revisão: antes, retirar(-5) AUMENTAVA o estoque,
# porque só a tela validava. Estes testes garantem que ele não volta.

QUANTIDADES_INVALIDAS = [0, -5, 2.5, "10", None, True]

OPERACOES = {
    "entrada": lambda q: banco.inserir("Caneta", q, 2.5),
    "saida": lambda q: banco.retirar("Caneta", q),
    "reserva": lambda q: banco.reservar("Caneta", q, "Pedido"),
    "bloqueio": lambda q: banco.bloquear("Caneta", q, "Motivo"),
    "requisicao": lambda q: banco.criar_requisicao("Caneta", q),
    "edicao": lambda q: banco.editar("Caneta", nova_quantidade=q),
}


@pytest.mark.parametrize("quantidade", QUANTIDADES_INVALIDAS)
@pytest.mark.parametrize("operacao", OPERACOES)
def test_quantidade_invalida_e_recusada_e_nao_altera_o_arquivo(operacao, quantidade, planilha_temporaria):
    banco.inserir("Caneta", 10, 2.5)
    antes = impressao_digital(planilha_temporaria)
    with pytest.raises(ErroEstoque):
        OPERACOES[operacao](quantidade)
    assert impressao_digital(planilha_temporaria) == antes


def test_quantidade_inteira_vinda_como_decimal_e_aceita():
    banco.inserir("Caneta", 3.0, 2.5)  # ex.: número lido do Excel
    assert situacao("Caneta").quantidade == 3


@pytest.mark.parametrize("valor", [-1, "abc", None])
def test_valor_invalido_e_recusado(valor):
    with pytest.raises(ErroEstoque):
        banco.inserir("Caneta", 10, valor)
    assert situacao("Caneta") is None


# ================================================================== recusas de regra não gravam nada

RECUSAS = {
    "retirar mais que o disponível": lambda: banco.retirar("Caneta", 99),
    "reservar mais que o disponível": lambda: banco.reservar("Caneta", 99, "Pedido"),
    "bloquear mais que o disponível": lambda: banco.bloquear("Caneta", 99, "Motivo"),
    "liberar ID inexistente": lambda: banco.liberar("R9999"),
    "liberar ID já encerrado": lambda: banco.liberar("R0002"),
    "produto inexistente": lambda: banco.retirar("Lápis", 1),
    "editar abaixo do comprometido": lambda: banco.editar("Caneta", nova_quantidade=2),
    "renomear para nome existente": lambda: banco.editar("Caneta", novo_nome="Borracha"),
    "excluir com reserva ativa": lambda: banco.excluir("Caneta"),
}


@pytest.mark.parametrize("recusa", RECUSAS)
def test_operacao_recusada_nao_altera_o_arquivo(recusa, planilha_temporaria):
    banco.inserir("Caneta", 10, 2.5)
    banco.inserir("Borracha", 5, 1.0)
    banco.reservar("Caneta", 3, "Pedido A")   # R0001 ativo
    banco.reservar("Caneta", 1, "Pedido B")
    banco.liberar("R0002")                    # R0002 encerrado
    antes = impressao_digital(planilha_temporaria)
    with pytest.raises(ErroEstoque):
        RECUSAS[recusa]()
    assert impressao_digital(planilha_temporaria) == antes


def test_importacao_com_um_item_invalido_nao_grava_nenhum(planilha_temporaria):
    antes = impressao_digital(planilha_temporaria)
    lista = [("Caneta", 10, 2.5), ("Lápis", -3, 1.0), ("Borracha", 5, 1.0)]
    with pytest.raises(ErroEstoque):
        banco.inserir_lista(lista)
    assert impressao_digital(planilha_temporaria) == antes
    assert banco.listar_itens() == []


def test_arquivo_aberto_no_excel_vira_mensagem_amigavel(monkeypatch, planilha_temporaria):
    """Simula o Windows bloqueando a gravação (planilha aberta no Excel)."""
    banco.inserir("Caneta", 10, 2.5)

    def bloqueado(*args, **kwargs):
        raise PermissionError("arquivo em uso")

    # context(): a simulação vale só dentro do "with" (a planilha temporária continua valendo)
    with monkeypatch.context() as m:
        m.setattr(Workbook, "save", bloqueado)
        with pytest.raises(ErroEstoque, match="Feche o estoque.xlsx"):
            banco.retirar("Caneta", 1)
    assert situacao("Caneta").quantidade == 10  # a retirada não aconteceu


def test_queda_no_meio_da_gravacao_nao_corrompe_o_arquivo(monkeypatch, planilha_temporaria):
    """Simula o computador caindo NO MEIO da gravação (arquivo escrito pela metade).

    Graças à gravação atômica (grava num .tmp e só depois troca), o
    estoque.xlsx original continua inteiro e o .tmp incompleto é descartado.
    """
    banco.inserir("Caneta", 10, 2.5)
    antes = impressao_digital(planilha_temporaria)

    def grava_pela_metade(self, caminho):
        with open(caminho, "wb") as f:
            f.write(b"PK\x03\x04 metade de um arquivo")  # lixo: um xlsx incompleto
        raise OSError(28, "No space left on device")      # e então falha (ex.: disco cheio)

    with monkeypatch.context() as m:
        m.setattr(Workbook, "save", grava_pela_metade)
        with pytest.raises(ErroEstoque, match="Nada foi alterado"):
            banco.retirar("Caneta", 4)

    assert impressao_digital(planilha_temporaria) == antes            # original intacto
    assert not planilha_temporaria.with_name(planilha_temporaria.name + ".tmp").exists()  # sem lixo
    assert banco.consultar("Caneta").quantidade == 10                 # e continua legível


# ================================================================== histórico (auditoria)

def test_toda_operacao_fica_registrada_no_historico():
    banco.inserir("Caneta", 10, 2.5)
    banco.retirar("Caneta", 2)
    id_reserva, _ = banco.reservar("Caneta", 3, "Pedido")
    banco.bloquear("Caneta", 1, "Avaria")
    banco.liberar(id_reserva)
    tipos = [r.tipo for r in reversed(banco.listar_historico())]  # do mais antigo ao mais novo
    assert tipos == [banco.ENTRADA, banco.SAIDA, banco.RESERVA, banco.BLOQUEIO, banco.LIBERACAO]


def test_operacao_recusada_nao_entra_no_historico():
    banco.inserir("Caneta", 10, 2.5)
    with pytest.raises(ErroEstoque):
        banco.retirar("Caneta", 50)
    assert len(banco.listar_historico()) == 1  # só a entrada
