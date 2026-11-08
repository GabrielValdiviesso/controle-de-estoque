"""
RESERVAS E BLOQUEIOS
====================
- Reservar: separa unidades para um pedido.
- Bloquear: torna unidades indisponíveis (ex.: avariadas, em inspeção).
- Liberar:  cancela a reserva/bloqueio → as unidades voltam para o disponível.
- Dar baixa: efetiva a reserva/bloqueio → as unidades saem do estoque.

Como funciona por baixo:
  Reservar/bloquear NÃO muda a aba Estoque. Só cria uma linha "Ativo" na aba
  "Reservas e Bloqueios". O disponível é sempre calculado assim:
      disponível = total − (reservas ativas) − (bloqueios ativos)
  Liberar só muda o status para "Liberado". Dar baixa muda para "Baixa" E
  diminui o total na aba Estoque.
"""
from . import config
from .historico import registrar
from .modelos import ErroEstoque
from .planilha import (abrir, abrir_leitura, achar_linha, agora, item_com_saldo, ler_movimentos,
                       mensagem_sem_saldo, mesmo_nome, salvar, tirar_do_estoque)
from .utilidades import validar_quantidade


# ================================================================== criar

def _criar_registro(tipo, objeto, quantidade, referencia):
    """Parte comum de reservar() e bloquear(). Retorna (id, mensagem).

    (O "_" no começo do nome indica: função de uso interno deste arquivo.)
    """
    quantidade = validar_quantidade(quantidade)
    planilha, aba, aba_mov = abrir()
    _, item = item_com_saldo(aba, aba_mov, objeto)
    if quantidade > item.disponivel:
        raise ErroEstoque(mensagem_sem_saldo(item))

    # Gera o próximo ID: pega o maior número já usado com esse prefixo e soma 1.
    # Ex.: se existem R0001 e R0002, o próximo é R0003.
    prefixo = tipo[0]  # "R" de Reserva, "B" de Bloqueio
    numeros = [int(m.id[1:]) for _, m in ler_movimentos(aba_mov)
               if m.id.upper().startswith(prefixo) and m.id[1:].isdigit()]
    novo_id = f"{prefixo}{max(numeros, default=0) + 1:04d}"  # :04d → 4 dígitos (0003)

    aba_mov.append([novo_id, tipo, item.objeto, quantidade, referencia.strip(), agora(), config.ATIVO, None])
    aba_mov.cell(row=aba_mov.max_row, column=6).number_format = config.FORMATO_DATA
    # no histórico: o total físico não muda (saldo = quantidade atual)
    registrar(planilha, tipo, item.objeto, quantidade, item.quantidade, item.valor,
              f"{novo_id} — {referencia.strip()}" if referencia.strip() else novo_id)
    salvar(planilha)
    feito = "criada" if tipo == config.RESERVA else "criado"
    return novo_id, f"{tipo} {novo_id} {feito}: {quantidade} unidade(s) de '{item.objeto}'."


def reservar(objeto, quantidade, pedido=""):
    """Reserva unidades disponíveis para um pedido. Retorna (id, mensagem)."""
    return _criar_registro(config.RESERVA, objeto, quantidade, pedido)


def bloquear(objeto, quantidade, motivo=""):
    """Bloqueia unidades disponíveis. Retorna (id, mensagem)."""
    return _criar_registro(config.BLOQUEIO, objeto, quantidade, motivo)


# ================================================================== encerrar

def _achar_ativo(aba_mov, id_mov):
    """Acha o registro pelo ID. Só aceita se ainda estiver "Ativo"."""
    for linha, m in ler_movimentos(aba_mov):
        if mesmo_nome(m.id, id_mov):
            if m.status != config.ATIVO:
                raise ErroEstoque(f"{m.id} já foi encerrado (status: {m.status}).")
            return linha, m
    raise ErroEstoque(f"Não existe reserva ou bloqueio com ID '{id_mov.strip()}'.")


def _encerrar(linha, status):
    """Marca o registro como encerrado (Liberado ou Baixa) com a data de agora."""
    linha[6].value = status        # coluna G: Status
    linha[7].value = agora()       # coluna H: Data Fim
    linha[7].number_format = config.FORMATO_DATA


def liberar(id_mov):
    """Cancela a reserva/bloqueio: a quantidade volta a ficar disponível."""
    planilha, aba, aba_mov = abrir()
    linha, m = _achar_ativo(aba_mov, id_mov)
    _encerrar(linha, config.LIBERADO)
    produto = achar_linha(aba, m.objeto)
    saldo, valor = (produto[1].value, produto[2].value) if produto else (0, 0)
    registrar(planilha, config.LIBERACAO, m.objeto, m.quantidade, saldo, valor, f"{m.id} — {m.tipo} {'cancelada' if m.tipo == config.RESERVA else 'cancelado'}")
    salvar(planilha)
    return f"{m.id} liberado: {m.quantidade} unidade(s) de '{m.objeto}' voltaram a ficar disponíveis."


def dar_baixa(id_mov):
    """Efetiva a reserva/bloqueio: a quantidade sai do estoque de vez."""
    planilha, aba, aba_mov = abrir()
    linha_mov, m = _achar_ativo(aba_mov, id_mov)
    linha = achar_linha(aba, m.objeto)
    # Segurança: só acontece se alguém editou a planilha à mão de forma inconsistente
    if not linha or (linha[1].value or 0) < m.quantidade:
        raise ErroEstoque(f"'{m.objeto}' não tem {m.quantidade} unidade(s) na aba Estoque. Confira a planilha.")
    _encerrar(linha_mov, config.BAIXA)
    valor = linha[2].value  # guarda antes: a linha pode ser apagada se zerar
    restante = tirar_do_estoque(aba, linha, m.quantidade)
    registrar(planilha, config.BAIXA, m.objeto, m.quantidade, restante, valor,
              f"{m.id} — {m.referencia}" if m.referencia else m.id)
    salvar(planilha)
    return f"Baixa de {m.id}: {m.quantidade} unidade(s) de '{m.objeto}' saíram do estoque. Restam {restante}."


# ================================================================== consultar

def listar_movimentos(apenas_ativos=True):
    """Reservas e bloqueios, do mais novo para o mais antigo.

    apenas_ativos=True  → só os que ainda estão segurando unidades
    apenas_ativos=False → todo o histórico (inclui liberados e baixas)
    """
    planilha = abrir_leitura()
    try:
        movimentos = [m for _, m in ler_movimentos(planilha[config.ABA_MOV])
                      if not apenas_ativos or m.status == config.ATIVO]
    finally:
        planilha.close()
    return movimentos[::-1]  # [::-1] inverte a lista (mais novo primeiro)
