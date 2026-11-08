"""
PRODUTOS: ADICIONAR, RETIRAR, EDITAR, EXCLUIR E LISTAR
======================================================
As operações da aba "Estoque". Toda operação que muda algo também deixa um
registro na aba "Movimentações" (ver historico.py).

Regras de negócio:
- Adicionar um produto que já existe SOMA a quantidade e ATUALIZA o valor.
- Retirar só tira do que está DISPONÍVEL (não mexe no reservado/bloqueado).
- Se o total de um produto chegar a zero, ele sai da aba Estoque.
- Editar: a quantidade não pode ficar menor que (reservado + bloqueado), e o
  novo nome não pode ser igual ao de outro produto.
- Excluir: só se o produto não tiver reservas/bloqueios ativos.
- Toda ENTRADA dá baixa automática nas requisições abertas do produto
  (ver requisicoes.py).
"""
from . import config
from .historico import registrar
from .modelos import ErroEstoque, Item
from .planilha import (abrir, abrir_leitura, achar_linha, item_com_saldo, ler_movimentos,
                       mensagem_sem_saldo, mesmo_nome, salvar, tirar_do_estoque)
from .requisicoes import atender_requisicoes, renomear_nas_requisicoes
from .utilidades import moeda, validar_quantidade, validar_valor


def inserir(objeto, quantidade, valor, observacao=""):
    """Adiciona unidades de um produto.

    Parâmetros:
        objeto     – nome do produto (ex.: "Caneta azul")
        quantidade – inteiro maior que zero
        valor      – valor unitário em reais
        observacao – texto livre que vai para o histórico (opcional)
    Retorna a mensagem de sucesso (texto). Em caso de problema, ErroEstoque.
    """
    objeto = objeto.strip()
    if not objeto:
        raise ErroEstoque("Digite o nome do objeto.")
    quantidade = validar_quantidade(quantidade)
    valor = validar_valor(valor)
    planilha, aba, _ = abrir()  # "_" = não vamos usar a aba de reservas aqui
    linha = achar_linha(aba, objeto)
    if linha:
        # já existe → soma e atualiza o valor
        linha[1].value = (linha[1].value or 0) + quantidade
        linha[2].value = valor
        nome, saldo = linha[0].value, linha[1].value
        msg = f"'{nome}' atualizado: agora tem {saldo} unidade(s)."
    else:
        # não existe → nova linha no final
        aba.append([objeto, quantidade, valor])
        nome, saldo = objeto, quantidade
        observacao = ("Novo produto. " + observacao).strip()
        msg = f"'{objeto}' adicionado com {quantidade} unidade(s)."

    # baixa automática nas requisições abertas deste produto
    atendidas = atender_requisicoes(planilha, nome, quantidade)
    if atendidas:
        texto = "Requisições: " + ", ".join(atendidas)
        observacao = f"{observacao} | {texto}" if observacao else texto
        msg += f" {texto}."

    registrar(planilha, config.ENTRADA, nome, quantidade, saldo, valor, observacao)
    salvar(planilha)
    return msg


def retirar(objeto, quantidade, observacao=""):
    """Tira unidades DISPONÍVEIS de um produto. Retorna a mensagem."""
    quantidade = validar_quantidade(quantidade)
    planilha, aba, aba_mov = abrir()
    linha, item = item_com_saldo(aba, aba_mov, objeto)
    if quantidade > item.disponivel:
        raise ErroEstoque(mensagem_sem_saldo(item))
    restante = tirar_do_estoque(aba, linha, quantidade)
    registrar(planilha, config.SAIDA, item.objeto, quantidade, restante, item.valor, observacao)
    salvar(planilha)
    if restante == 0:
        return f"'{item.objeto}' zerou e foi removido do estoque."
    return f"Retirado {quantidade}. Restam {restante} unidade(s) de '{item.objeto}'."


def editar(objeto, novo_nome=None, nova_quantidade=None, novo_valor=None, observacao=""):
    """Corrige os dados de um produto já cadastrado.

    Passe só o que quer mudar (o que ficar como None continua igual).
    Exemplo: editar("pao", novo_nome="Pão francês", novo_valor=0.8)

    - Novo nome: as reservas/bloqueios do produto passam a usar o nome novo.
    - Nova quantidade: é o TOTAL físico (como numa contagem de inventário).
    Retorna a mensagem com o que mudou.
    """
    if nova_quantidade is not None:
        nova_quantidade = validar_quantidade(nova_quantidade)
    if novo_valor is not None:
        novo_valor = validar_valor(novo_valor)
    planilha, aba, aba_mov = abrir()
    linha, item = item_com_saldo(aba, aba_mov, objeto)
    mudancas = []  # lista de textos tipo "valor: R$ 1,00 → R$ 1,20"

    # ---- nome
    novo_nome = (novo_nome if novo_nome is not None else item.objeto).strip()
    if not novo_nome:
        raise ErroEstoque("O nome do produto não pode ficar vazio.")
    if novo_nome != item.objeto:
        outro = achar_linha(aba, novo_nome)
        if outro and outro[0].row != linha[0].row:  # .row = nº da linha; outra linha = outro produto
            raise ErroEstoque(f"Já existe um produto chamado '{outro[0].value}'.")
        # leva as reservas/bloqueios (ativos e histórico) para o nome novo
        for linha_mov, m in ler_movimentos(aba_mov):
            if mesmo_nome(m.objeto, item.objeto):
                linha_mov[2].value = novo_nome
        renomear_nas_requisicoes(planilha, item.objeto, novo_nome)  # requisições abertas também
        linha[0].value = novo_nome
        mudancas.append(f"nome: '{item.objeto}' → '{novo_nome}'")

    # ---- quantidade total
    diferenca = 0
    if nova_quantidade is not None and nova_quantidade != item.quantidade:
        comprometido = item.reservado + item.bloqueado
        if nova_quantidade < comprometido:
            raise ErroEstoque(f"A quantidade não pode ficar menor que {comprometido} "
                              f"({item.reservado} reservada(s) + {item.bloqueado} bloqueada(s)).")
        if nova_quantidade <= 0:
            raise ErroEstoque("A quantidade precisa ser maior que zero. Para remover o produto, use Excluir.")
        linha[1].value = nova_quantidade
        diferenca = nova_quantidade - item.quantidade
        mudancas.append(f"quantidade: {item.quantidade} → {nova_quantidade}")

    # ---- valor
    if novo_valor is not None and novo_valor != item.valor:
        linha[2].value = novo_valor
        mudancas.append(f"valor: {moeda(item.valor)} → {moeda(novo_valor)}")

    if not mudancas:
        raise ErroEstoque("Nada foi alterado.")
    descricao = "; ".join(mudancas)
    registrar(planilha, config.EDICAO, novo_nome, diferenca, linha[1].value, linha[2].value,
              descricao + (f" | {observacao.strip()}" if observacao.strip() else ""))
    salvar(planilha)
    return f"'{novo_nome}' atualizado — {descricao}."


def excluir(objeto, observacao=""):
    """Apaga o produto da aba Estoque (fica registrado no histórico)."""
    planilha, aba, aba_mov = abrir()
    linha, item = item_com_saldo(aba, aba_mov, objeto)
    if item.reservado or item.bloqueado:
        raise ErroEstoque(f"'{item.objeto}' tem {item.reservado} reservada(s) e {item.bloqueado} bloqueada(s). "
                          "Libere ou dê baixa nelas antes de excluir.")
    registrar(planilha, config.EXCLUSAO, item.objeto, item.quantidade, 0, item.valor, observacao)
    aba.delete_rows(linha[0].row)
    salvar(planilha)
    return f"'{item.objeto}' foi excluído do estoque ({item.quantidade} unidade(s))."


def listar_itens():
    """Lista todos os produtos (lista de Item), com reservado/bloqueado/disponível.

    Feita para ser rápida mesmo com muitos produtos:
    1. abre a planilha só para leitura;
    2. passa UMA vez pelas reservas/bloqueios, somando por produto num dicionário;
    3. passa UMA vez pelos produtos, pegando os totais do dicionário.
    """
    planilha = abrir_leitura()
    try:
        # passo 2 — dicionário: "nome em minúsculas" → (reservado, bloqueado)
        comprometido = {}
        for linha in planilha[config.ABA_MOV].iter_rows(min_row=2, max_col=8, values_only=True):
            id_mov, tipo, objeto, qtd, _, _, status, _ = (tuple(linha) + (None,) * 8)[:8]
            if id_mov is None or status != config.ATIVO:
                continue
            chave = str(objeto).strip().lower()
            reservado, bloqueado = comprometido.get(chave, (0, 0))
            if tipo == config.RESERVA:
                reservado += qtd or 0
            else:
                bloqueado += qtd or 0
            comprometido[chave] = (reservado, bloqueado)

        # passo 3 — monta a lista de produtos
        itens = []
        for linha in planilha.worksheets[0].iter_rows(min_row=2, max_col=3, values_only=True):
            objeto, qtd, valor = (tuple(linha) + (None,) * 3)[:3]
            if objeto is not None:
                reservado, bloqueado = comprometido.get(str(objeto).strip().lower(), (0, 0))
                itens.append(Item(str(objeto), qtd or 0, valor or 0, reservado, bloqueado))
        return itens
    finally:
        planilha.close()  # "finally" roda sempre, mesmo se der erro no meio
