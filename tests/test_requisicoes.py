"""
TESTES DA REQUISIÇÃO (funcionalidade extra)
===========================================
Quando um produto dá entrada, as requisições abertas dele são atendidas
automaticamente, da mais antiga para a mais nova.
"""
import pytest

import banco
from banco import ErroEstoque


def status():
    return {r.id: (r.status, r.atendida) for r in banco.listar_requisicoes()}


def test_entrada_atende_requisicoes_da_mais_antiga_para_a_mais_nova():
    banco.criar_requisicao("Caneta", 10, "RH")       # RQ0001
    banco.criar_requisicao("Caneta", 5, "Financeiro")  # RQ0002
    banco.inserir("Caneta", 12, 2.5)
    assert status() == {"RQ0001": (banco.REQ_ATENDIDA, 10), "RQ0002": (banco.REQ_PARCIAL, 2)}


def test_requisicao_de_produto_ainda_nao_cadastrado_e_aceita():
    id_req, _ = banco.criar_requisicao("Notebook", 2, "TI")
    assert id_req == "RQ0001"
    assert banco.listar_itens() == []  # requisição não mexe no estoque


def test_cancelar_requisicao_ja_atendida_e_recusado():
    banco.criar_requisicao("Caneta", 2)
    banco.inserir("Caneta", 2, 2.5)
    with pytest.raises(ErroEstoque):
        banco.cancelar_requisicao("RQ0001")
