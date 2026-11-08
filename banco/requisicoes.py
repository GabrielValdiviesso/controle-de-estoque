"""
REQUISIÇÕES (pedidos de compra/reposição)
=========================================
Uma requisição é um pedido do tipo "precisamos de 50 canetas" — ela NÃO mexe
no estoque. Fica na aba "Requisições" até o produto chegar.

Baixa automática:
  Quando o produto dá ENTRADA no estoque (inserir() ou importação), a função
  atender_requisicoes() é chamada e distribui a quantidade que chegou entre as
  requisições abertas desse produto, da MAIS ANTIGA para a mais nova:
      chegou tudo o que faltava → status "Atendida" (baixa automática)
      chegou só uma parte       → status "Parcial" (continua esperando o resto)
  O que sobrar fica normalmente no estoque.

Exemplo: RQ0001 pede 10 e RQ0002 pede 5. Chegam 12 unidades:
  RQ0001 → Atendida (10)   RQ0002 → Parcial (2 de 5)
"""
from . import config
from .modelos import ErroEstoque, Requisicao
from .planilha import abrir, abrir_leitura, achar_linha, agora, mesmo_nome, salvar
from .utilidades import validar_quantidade

ABERTAS = (config.REQ_ABERTA, config.REQ_PARCIAL)  # status que ainda esperam produto


def _ler_requisicoes(aba_req):
    """Lista de (linha, Requisicao) da aba Requisições."""
    resultado = []
    for linha in aba_req.iter_rows(min_row=2, max_col=9):
        if not linha or linha[0].value is None:
            continue
        v = ([c.value for c in linha] + [None] * 9)[:9]
        resultado.append((linha, Requisicao(
            id=str(v[0]), objeto=str(v[1] or ""), quantidade=v[2] or 0, atendida=v[3] or 0,
            solicitante=v[4] or "", observacao=v[5] or "", data=v[6], status=v[7],
            data_atendimento=v[8])))
    return resultado


# ================================================================== criar / cancelar

def criar_requisicao(objeto, quantidade, solicitante="", observacao=""):
    """Registra um pedido. O produto NÃO precisa existir no estoque ainda.
    Retorna (id, mensagem)."""
    objeto = objeto.strip()
    if not objeto:
        raise ErroEstoque("Digite o nome do produto.")
    quantidade = validar_quantidade(quantidade)
    planilha, aba, _ = abrir()
    aba_req = planilha[config.ABA_REQ]
    existente = achar_linha(aba, objeto)
    if existente:
        objeto = str(existente[0].value)  # usa o nome como está cadastrado ("caneta" → "Caneta")

    # próximo ID: RQ + maior número já usado + 1 (RQ0001, RQ0002...)
    numeros = [int(r.id[2:]) for _, r in _ler_requisicoes(aba_req)
               if r.id.upper().startswith("RQ") and r.id[2:].isdigit()]
    novo_id = f"RQ{max(numeros, default=0) + 1:04d}"

    aba_req.append([novo_id, objeto, quantidade, 0, solicitante.strip(), observacao.strip(),
                    agora(), config.REQ_ABERTA, None])
    aba_req.cell(row=aba_req.max_row, column=7).number_format = config.FORMATO_DATA
    salvar(planilha)
    return novo_id, (f"Requisição {novo_id} registrada: {quantidade} unidade(s) de '{objeto}'. "
                     "Ela será baixada automaticamente quando o produto der entrada no estoque.")


def cancelar_requisicao(id_req, motivo=""):
    """Cancela uma requisição que ainda está aberta (ou parcial)."""
    planilha, _, _ = abrir()
    for linha, r in _ler_requisicoes(planilha[config.ABA_REQ]):
        if mesmo_nome(r.id, id_req):
            if r.status not in ABERTAS:
                raise ErroEstoque(f"{r.id} já está como '{r.status}'.")
            linha[7].value = config.REQ_CANCELADA
            linha[8].value = agora()
            linha[8].number_format = config.FORMATO_DATA
            if motivo.strip():
                linha[5].value = (f"{r.observacao} | " if r.observacao else "") + f"Cancelada: {motivo.strip()}"
            salvar(planilha)
            return f"Requisição {r.id} cancelada."
    raise ErroEstoque(f"Não existe requisição com ID '{id_req.strip()}'.")


# ================================================================== baixa automática

def indice_abertas(aba_req):
    """Dicionário "nome em minúsculas" → lista de (linha, Requisicao) abertas,
    da mais antiga para a mais nova. Usado para atender muitos produtos de uma vez
    (importação) sem reler a aba a cada produto."""
    indice = {}
    for linha, r in _ler_requisicoes(aba_req):
        if r.status in ABERTAS:
            indice.setdefault(r.objeto.strip().lower(), []).append((linha, r))
    return indice


def atender_requisicoes(planilha, objeto, quantidade, indice=None):
    """Distribui a quantidade que chegou entre as requisições abertas do produto.

    ⚠️ Não salva: quem chama (inserir / inserir_lista) salva junto com a entrada.
    Retorna uma lista de textos, ex.: ["RQ0001 atendida", "RQ0002 parcial (2/5)"].
    """
    if indice is None:
        indice = indice_abertas(planilha[config.ABA_REQ])
    pendentes = indice.get(objeto.strip().lower(), [])
    resumo = []
    restante = quantidade
    for linha, r in list(pendentes):  # list(...) = cópia, pois vamos remover itens
        if restante <= 0:
            break
        usar = min(restante, r.falta)
        restante -= usar
        r.atendida += usar
        linha[3].value = r.atendida
        if r.falta == 0:
            r.status = config.REQ_ATENDIDA
            linha[7].value = r.status
            linha[8].value = agora()
            linha[8].number_format = config.FORMATO_DATA
            pendentes.remove((linha, r))
            resumo.append(f"{r.id} atendida")
        else:
            r.status = config.REQ_PARCIAL
            linha[7].value = r.status
            resumo.append(f"{r.id} parcial ({r.atendida}/{r.quantidade})")
    return resumo


def renomear_nas_requisicoes(planilha, nome_antigo, nome_novo):
    """Quando um produto é renomeado, as requisições ABERTAS passam a usar o nome novo
    (senão a baixa automática não as encontraria)."""
    for linha, r in _ler_requisicoes(planilha[config.ABA_REQ]):
        if r.status in ABERTAS and mesmo_nome(r.objeto, nome_antigo):
            linha[1].value = nome_novo


# ================================================================== consultar

def listar_requisicoes(apenas_abertas=False):
    """Requisições, da mais nova para a mais antiga."""
    planilha = abrir_leitura()
    try:
        requisicoes = [r for _, r in _ler_requisicoes(planilha[config.ABA_REQ])
                       if not apenas_abertas or r.status in ABERTAS]
    finally:
        planilha.close()
    return requisicoes[::-1]
