"""
IMPORTAR LISTA DE PRODUTOS
==========================
Lê uma planilha (.xlsx) ou um arquivo .csv com Objeto, Quantidade e Valor e
adiciona tudo de uma vez.

Funciona em 2 etapas (é assim que a janela usa):
  1. ler_lista(caminho)    → lê e valida, SEM gravar nada (serve para a prévia)
  2. inserir_lista(lista)  → grava tudo no estoque, salvando uma única vez

✏️  Para aceitar outros nomes de coluna (ex.: "Descrição do item"), basta
    acrescentar o nome em minúsculas em NOMES_COLUNAS, logo abaixo.
"""
import csv
import io
import re
from pathlib import Path

from openpyxl import Workbook, load_workbook

from . import config
from .historico import registrar
from .modelos import ErroEstoque
from .planilha import abrir, escrever_cabecalho, salvar
from .requisicoes import atender_requisicoes, indice_abertas
from .utilidades import validar_quantidade, validar_valor

# Nomes de cabeçalho reconhecidos (sempre em minúsculas)
NOMES_COLUNAS = {
    "objeto": ("objeto", "produto", "nome", "item", "descrição", "descricao"),
    "qtd": ("quantidade", "qtd", "qtde", "quant"),
    "valor": ("valor", "valor unitário", "valor unitario", "valor (r$)", "valor unitário (r$)",
              "preço", "preco", "preço unitário", "preco unitario"),
}


def _numero_da_lista(valor, inteiro, nome):
    """Converte o que veio da planilha/CSV em número.

    Aceita: 10 | 10.0 | "2,50" | "R$ 1.234,56" | "1.000" (mil, para quantidade).
    inteiro=True exige número sem casas decimais (para quantidade).
    """
    o = "a" if nome == "quantidade" else "o"  # "quantidade inválida" / "valor inválido"
    if isinstance(valor, bool):
        raise ErroEstoque(f"{nome} inválid{o}")
    if isinstance(valor, (int, float)):
        numero = valor  # célula numérica do Excel: já é número
    else:
        texto = str(valor or "").replace("R$", "").replace(" ", "").strip()
        if not texto:
            raise ErroEstoque(f"{nome} vazi{o}")
        if "," in texto and "." in texto:
            texto = texto.replace(".", "")              # 1.234,56 → 1234,56
        elif inteiro and re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
            texto = texto.replace(".", "")              # 1.000 → 1000
        try:
            numero = float(texto.replace(",", "."))     # vírgula decimal → ponto
        except ValueError:
            raise ErroEstoque(f"{nome} inválid{o}: '{valor}'")
    if inteiro:
        if numero != int(numero):
            raise ErroEstoque(f"{nome} precisa ser inteiro: '{valor}'")
        numero = int(numero)
    if numero <= 0:
        raise ErroEstoque(f"{nome} precisa ser maior que zero")
    return numero


def _linhas_do_arquivo(caminho):
    """Lê o arquivo e devolve todas as linhas como tuplas de valores."""
    caminho = Path(caminho)
    tipo = caminho.suffix.lower()  # extensão: ".xlsx", ".csv"...
    try:
        if tipo in (".xlsx", ".xlsm"):
            # data_only=True → se a célula tiver fórmula, pega o resultado
            planilha = load_workbook(caminho, read_only=True, data_only=True)
            try:
                return [tuple(linha) for linha in planilha.worksheets[0].iter_rows(values_only=True)]
            finally:
                planilha.close()
        if tipo in (".csv", ".txt"):
            # Tenta UTF-8 primeiro; se falhar, usa a codificação padrão do Windows
            for codificacao in ("utf-8-sig", "cp1252"):
                try:
                    texto = caminho.read_text(encoding=codificacao)
                    break
                except UnicodeDecodeError:
                    continue
            # Descobre sozinho se o separador é ";" "," ou TAB
            try:
                separador = csv.Sniffer().sniff(texto[:4096], delimiters=";,\t").delimiter
            except csv.Error:
                separador = ";"  # padrão do Excel em português
            return [tuple(linha) for linha in csv.reader(io.StringIO(texto), delimiter=separador)]
    except ErroEstoque:
        raise
    except PermissionError:
        raise ErroEstoque("Não consegui abrir o arquivo. Feche-o no Excel e tente de novo.")
    except Exception as erro:
        raise ErroEstoque(f"Não consegui ler o arquivo: {erro}")
    raise ErroEstoque("Formato não suportado. Use uma planilha .xlsx ou um arquivo .csv.")


def ler_lista(caminho):
    """Lê e valida a lista. NÃO grava nada.

    Retorna (produtos, erros):
      produtos – lista de (objeto, quantidade, valor), sem repetidos
                 (o mesmo objeto 2x na lista → quantidades somadas)
      erros    – textos "Linha N: motivo" das linhas que serão ignoradas
    """
    linhas = _linhas_do_arquivo(caminho)
    posicoes, inicio = (0, 1, 2), 0  # padrão: sem cabeçalho, ordem Objeto/Qtd/Valor

    # Se a 1ª linha tiver nomes conhecidos, ela é o cabeçalho: descobre em
    # qual coluna está cada informação (assim a ordem das colunas não importa).
    if linhas:
        cabecalho = [str(c or "").strip().lower() for c in linhas[0]]
        achou = {}
        for chave, nomes in NOMES_COLUNAS.items():
            for i, titulo in enumerate(cabecalho):
                if titulo in nomes:
                    achou[chave] = i
                    break
        if achou:
            faltando = [n for n, c in (("Objeto", "objeto"), ("Quantidade", "qtd"), ("Valor", "valor"))
                        if c not in achou]
            if faltando:
                raise ErroEstoque(f"O cabeçalho da lista não tem a(s) coluna(s): {', '.join(faltando)}.")
            posicoes, inicio = (achou["objeto"], achou["qtd"], achou["valor"]), 1

    produtos, erros = {}, []  # produtos: "nome minúsculo" → [objeto, qtd, valor]
    for numero, linha in enumerate(linhas[inicio:], start=inicio + 1):  # numero = linha no arquivo
        if not linha or all(c is None or str(c).strip() == "" for c in linha):
            continue  # linha em branco: pula sem aviso

        def celula(i):
            return linha[i] if i < len(linha) else None

        objeto = celula(posicoes[0])
        if isinstance(objeto, float) and objeto.is_integer():
            objeto = int(objeto)  # código numérico: "123" e não "123.0"
        objeto = str(objeto if objeto is not None else "").strip()
        try:
            if not objeto:
                raise ErroEstoque("falta o nome do objeto")
            qtd = _numero_da_lista(celula(posicoes[1]), True, "quantidade")
            valor = _numero_da_lista(celula(posicoes[2]), False, "valor")
        except ErroEstoque as erro:
            erros.append(f"Linha {numero}: {erro}")
            continue
        chave = objeto.lower()
        if chave in produtos:
            produtos[chave][1] += qtd
            produtos[chave][2] = valor
        else:
            produtos[chave] = [objeto, qtd, valor]
    return [tuple(p) for p in produtos.values()], erros


def inserir_lista(produtos, origem=""):
    """Grava a lista no estoque (mesma regra do inserir: existe → soma).

    Diferente de chamar inserir() várias vezes, aqui a planilha é aberta e
    salva UMA vez só — muito mais rápido para listas grandes.
    origem: nome do arquivo importado (vai para a observação do histórico).
    """
    if not produtos:
        raise ErroEstoque("A lista não tem nenhum produto válido.")
    # confere a lista INTEIRA antes de abrir a planilha: um item ruim → nada é gravado
    validados = []
    for objeto, qtd, valor in produtos:
        if not str(objeto).strip():
            raise ErroEstoque("A lista tem um produto sem nome.")
        validados.append((str(objeto), validar_quantidade(qtd, f"quantidade de '{objeto}'"), validar_valor(valor)))
    produtos = validados
    planilha, aba, _ = abrir()

    # Índice "nome minúsculo" → linha, para achar cada produto sem percorrer tudo
    indice = {}
    for linha in aba.iter_rows(min_row=2, max_col=3):
        if linha[0].value is not None:
            indice.setdefault(str(linha[0].value).strip().lower(), linha)

    novos = atualizados = 0
    observacao = f"Arquivo: {origem}" if origem else ""
    abertas = indice_abertas(planilha[config.ABA_REQ])  # requisições abertas, lidas uma vez só
    total_atendidas = total_parciais = 0
    for objeto, qtd, valor in produtos:
        linha = indice.get(objeto.strip().lower())
        if linha:
            linha[1].value = (linha[1].value or 0) + qtd
            linha[2].value = valor
            nome, saldo, obs = linha[0].value, linha[1].value, observacao
            atualizados += 1
        else:
            aba.append([objeto.strip(), qtd, valor])
            indice[objeto.strip().lower()] = tuple(aba[aba.max_row])[:3]
            nome, saldo, obs = objeto.strip(), qtd, ("Novo produto. " + observacao).strip()
            novos += 1
        # baixa automática nas requisições abertas deste produto
        atendidas = atender_requisicoes(planilha, nome, qtd, abertas)
        if atendidas:
            obs = f"{obs} | Requisições: {', '.join(atendidas)}" if obs else f"Requisições: {', '.join(atendidas)}"
            total_atendidas += sum(1 for a in atendidas if a.endswith("atendida"))
            total_parciais += sum(1 for a in atendidas if "parcial" in a)
        registrar(planilha, config.IMPORTACAO, nome, qtd, saldo, valor, obs)
    salvar(planilha)
    msg = f"Importação concluída: {novos} produto(s) novo(s) e {atualizados} atualizado(s)."
    if total_atendidas or total_parciais:
        msg += (f" Requisições: {total_atendidas} atendida(s) e {total_parciais} parcial(is), "
                "baixadas automaticamente.")
    return msg


def criar_modelo(caminho):
    """Salva uma planilha-modelo (cabeçalho + 2 exemplos) para o usuário preencher."""
    planilha = Workbook()
    aba = planilha.active
    aba.title = "Produtos"
    escrever_cabecalho(aba, config.COLUNAS, config.LARGURAS)
    aba.append(["Caneta azul", 50, 2.5])
    aba.append(["Caderno 10 matérias", 20, 24.9])
    try:
        planilha.save(caminho)
    except PermissionError:
        raise ErroEstoque("Não consegui salvar o modelo. Se ele estiver aberto no Excel, feche e tente de novo.")
