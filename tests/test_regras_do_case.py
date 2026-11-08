"""
TESTES DAS 6 FUNCIONALIDADES DO CASE
====================================
Entrada, Saída, Reservar, Bloquear, Liberar e Consultar — cada uma com o
caminho feliz e as recusas que o case exige ("não deve ser possível...").

Leitura de um teste:
    banco.inserir(...)                 → prepara o cenário
    with pytest.raises(ErroEstoque):   → "isto TEM que dar erro"
    assert ...                         → "isto TEM que ser verdade"
"""
import pytest

import banco
from banco import ErroEstoque
from conftest import situacao


# ================================================================== 1. Entrada

def test_entrada_cria_produto_novo():
    banco.inserir("Caneta", 10, 2.5)
    item = situacao("Caneta")
    assert (item.quantidade, item.disponivel, item.valor) == (10, 10, 2.5)


def test_entrada_em_produto_existente_soma_e_atualiza_valor():
    banco.inserir("Caneta", 10, 2.5)
    banco.inserir("caneta", 5, 3.0)  # mesmo produto, escrito em minúsculas
    item = situacao("Caneta")
    assert item.quantidade == 15
    assert item.valor == 3.0
    assert len(banco.listar_itens()) == 1  # não criou um segundo produto


# ================================================================== 2. Saída

def test_saida_diminui_o_total():
    banco.inserir("Caneta", 10, 2.5)
    banco.retirar("Caneta", 4)
    assert situacao("Caneta").quantidade == 6


def test_saida_maior_que_o_disponivel_e_recusada():
    banco.inserir("Caneta", 10, 2.5)
    with pytest.raises(ErroEstoque):
        banco.retirar("Caneta", 11)
    assert situacao("Caneta").quantidade == 10  # nada mudou


def test_saida_nao_usa_unidades_reservadas_nem_bloqueadas():
    banco.inserir("Caneta", 10, 2.5)
    banco.reservar("Caneta", 6, "Pedido 1")
    banco.bloquear("Caneta", 2, "Avariadas")
    with pytest.raises(ErroEstoque):
        banco.retirar("Caneta", 3)  # total 10, mas só 2 disponíveis
    banco.retirar("Caneta", 2)      # exatamente o disponível: permitido
    assert situacao("Caneta").disponivel == 0


def test_saida_de_tudo_remove_o_produto():
    banco.inserir("Caneta", 3, 2.5)
    banco.retirar("Caneta", 3)
    assert situacao("Caneta") is None


def test_produto_inexistente_e_recusado():
    with pytest.raises(ErroEstoque):
        banco.retirar("Lápis", 1)
    with pytest.raises(ErroEstoque):
        banco.reservar("Lápis", 1, "Pedido")


# ================================================================== 3. Reservar

def test_reservar_gera_id_e_tira_do_disponivel_sem_mudar_o_total():
    banco.inserir("Caneta", 10, 2.5)
    id_reserva, _ = banco.reservar("Caneta", 4, "Pedido 123")
    item = situacao("Caneta")
    assert id_reserva == "R0001"
    assert (item.quantidade, item.reservado, item.disponivel) == (10, 4, 6)


def test_reservar_mais_que_o_disponivel_e_recusado():
    banco.inserir("Caneta", 10, 2.5)
    banco.bloquear("Caneta", 3, "Avariadas")
    with pytest.raises(ErroEstoque):
        banco.reservar("Caneta", 8, "Pedido")  # só 7 disponíveis
    assert situacao("Caneta").reservado == 0


# ================================================================== 4. Bloquear

def test_bloquear_gera_id_e_tira_do_disponivel():
    banco.inserir("Caneta", 10, 2.5)
    id_bloqueio, _ = banco.bloquear("Caneta", 2, "Em inspeção")
    item = situacao("Caneta")
    assert id_bloqueio == "B0001"
    assert (item.quantidade, item.bloqueado, item.disponivel) == (10, 2, 8)


def test_bloquear_mais_que_o_disponivel_e_recusado():
    banco.inserir("Caneta", 10, 2.5)
    banco.reservar("Caneta", 6, "Pedido")
    with pytest.raises(ErroEstoque):
        banco.bloquear("Caneta", 5, "Avariadas")  # só 4 disponíveis
    assert situacao("Caneta").bloqueado == 0


# ================================================================== várias ao mesmo tempo

def test_varias_reservas_e_bloqueios_simultaneos_de_pedidos_diferentes():
    banco.inserir("Caneta", 100, 2.5)
    banco.reservar("Caneta", 10, "Pedido A")
    banco.reservar("Caneta", 15, "Pedido B")
    banco.bloquear("Caneta", 5, "Avaria lote 1")
    banco.bloquear("Caneta", 3, "Inspeção")
    item = situacao("Caneta")
    assert (item.quantidade, item.reservado, item.bloqueado, item.disponivel) == (100, 25, 8, 67)
    ids = sorted(m.id for m in banco.listar_movimentos())
    assert ids == ["B0001", "B0002", "R0001", "R0002"]


# ================================================================== 5. Liberar

def test_liberar_reserva_devolve_ao_disponivel():
    banco.inserir("Caneta", 10, 2.5)
    id_reserva, _ = banco.reservar("Caneta", 4, "Pedido")
    banco.liberar(id_reserva)
    item = situacao("Caneta")
    assert (item.quantidade, item.reservado, item.disponivel) == (10, 0, 10)


def test_liberar_bloqueio_devolve_ao_disponivel():
    banco.inserir("Caneta", 10, 2.5)
    id_bloqueio, _ = banco.bloquear("Caneta", 3, "Inspeção")
    banco.liberar(id_bloqueio)
    assert situacao("Caneta").disponivel == 10


def test_liberar_um_nao_afeta_os_outros():
    banco.inserir("Caneta", 20, 2.5)
    r1, _ = banco.reservar("Caneta", 5, "Pedido A")
    banco.reservar("Caneta", 7, "Pedido B")
    banco.liberar(r1)
    assert situacao("Caneta").reservado == 7


def test_liberar_duas_vezes_o_mesmo_id_e_recusado():
    banco.inserir("Caneta", 10, 2.5)
    id_reserva, _ = banco.reservar("Caneta", 4, "Pedido")
    banco.liberar(id_reserva)
    with pytest.raises(ErroEstoque):
        banco.liberar(id_reserva)  # senão "criaria" 4 unidades do nada
    assert situacao("Caneta").disponivel == 10


def test_liberar_id_inexistente_e_recusado():
    with pytest.raises(ErroEstoque):
        banco.liberar("R9999")


def test_id_e_aceito_em_minusculas():
    banco.inserir("Caneta", 10, 2.5)
    banco.reservar("Caneta", 4, "Pedido")
    banco.liberar("r0001")
    assert situacao("Caneta").reservado == 0


def test_ids_nao_sao_reaproveitados():
    banco.inserir("Caneta", 10, 2.5)
    banco.reservar("Caneta", 1, "Pedido A")
    banco.liberar("R0001")
    novo_id, _ = banco.reservar("Caneta", 1, "Pedido B")
    assert novo_id == "R0002"  # R0001 continua identificando a reserva antiga


# ================================================================== Dar baixa (extra)

def test_dar_baixa_tira_do_total_e_do_reservado():
    banco.inserir("Caneta", 10, 2.5)
    id_reserva, _ = banco.reservar("Caneta", 4, "Pedido")
    banco.dar_baixa(id_reserva)
    item = situacao("Caneta")
    assert (item.quantidade, item.reservado, item.disponivel) == (6, 0, 6)


# ================================================================== 6. Consultar

def test_consultar_mostra_total_disponivel_reservado_e_bloqueado():
    banco.inserir("Caneta", 50, 2.5)
    banco.inserir("Borracha", 8, 1.0)
    banco.reservar("Caneta", 10, "Pedido")
    banco.bloquear("Caneta", 5, "Avaria")
    item = banco.consultar("caneta")  # nome em minúsculas também encontra
    assert item.objeto == "Caneta"
    assert item.quantidade == 50
    assert item.reservado == 10
    assert item.bloqueado == 5
    assert item.disponivel == 35  # 50 − 10 − 5
    assert banco.consultar("Borracha").disponivel == 8  # o outro produto não é afetado


def test_consultar_produto_inexistente_e_recusado():
    with pytest.raises(ErroEstoque):
        banco.consultar("Lápis")
