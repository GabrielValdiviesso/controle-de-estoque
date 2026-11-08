"""
ACESSO À PLANILHA (EXCEL)
=========================
Este módulo é a "porta" para o arquivo estoque.xlsx: criar, abrir, salvar e
procurar linhas. Os outros módulos (produtos, reservas, importação) usam as
funções daqui em vez de mexer no arquivo diretamente.

📚 Biblioteca usada: openpyxl
   - load_workbook(arquivo)  → abre a planilha inteira (para ler E gravar)
   - planilha.worksheets[0]  → a 1ª aba
   - planilha["Nome da aba"] → uma aba pelo nome
   - aba.iter_rows(...)      → percorre as linhas
   - aba.append([...])       → adiciona uma linha no final
   - planilha.save(arquivo)  → grava no disco

🔁 Padrão usado em todas as operações que ALTERAM dados:
       planilha, aba, aba_mov = abrir()   # 1. abre
       ... muda as células ...            # 2. altera na memória
       salvar(planilha)                   # 3. grava (só aqui o arquivo muda)
   Se der erro antes do salvar(), o arquivo fica como estava.
"""
import os
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from . import config
from .modelos import ErroEstoque, Item, Movimento


# ================================================================== criar / abrir / salvar

def escrever_cabecalho(aba, colunas, larguras):
    """Escreve a 1ª linha (títulos em negrito) e ajusta a largura das colunas."""
    aba.append(colunas)
    for celula, largura in zip(aba[1], larguras):
        celula.font = Font(bold=True)
        aba.column_dimensions[celula.column_letter].width = largura


def criar_aba_mov(planilha):
    """Cria a aba "Reservas e Bloqueios" vazia (só o cabeçalho)."""
    aba = planilha.create_sheet(config.ABA_MOV)
    escrever_cabecalho(aba, config.COLUNAS_MOV, config.LARGURAS_MOV)


def criar_aba_hist(planilha):
    """Cria a aba "Movimentações" vazia (só o cabeçalho)."""
    aba = planilha.create_sheet(config.ABA_HIST)
    escrever_cabecalho(aba, config.COLUNAS_HIST, config.LARGURAS_HIST)


def criar_aba_req(planilha):
    """Cria a aba "Requisições" vazia (só o cabeçalho)."""
    aba = planilha.create_sheet(config.ABA_REQ)
    escrever_cabecalho(aba, config.COLUNAS_REQ, config.LARGURAS_REQ)


# Abas extras e a função que cria cada uma (usado para atualizar planilhas antigas)
ABAS_EXTRAS = {config.ABA_MOV: criar_aba_mov, config.ABA_HIST: criar_aba_hist, config.ABA_REQ: criar_aba_req}


def criar_banco():
    """Garante que a planilha existe e está no formato certo.

    - Se o arquivo não existe: cria com todas as abas.
    - Se existe mas falta alguma aba (planilha de uma versão antiga do
      programa): cria só as abas que faltam, sem mexer nos dados.
    - Se existe com colunas diferentes: avisa com ErroEstoque (não apaga nada).
    É chamada uma vez quando o programa abre.
    """
    if config.ARQUIVO.exists():
        planilha = load_workbook(config.ARQUIVO)
        cabecalho = [c.value for c in planilha.worksheets[0][1]][:3]
        if cabecalho != config.COLUNAS:
            raise ErroEstoque(
                f"O arquivo {config.ARQUIVO.name} existe mas tem colunas diferentes de {config.COLUNAS}.\n"
                "Renomeie ou apague esse arquivo e abra o programa de novo."
            )
        faltando = [nome for nome in ABAS_EXTRAS if nome not in planilha.sheetnames]
        for nome in faltando:
            ABAS_EXTRAS[nome](planilha)
        if faltando:
            salvar(planilha)
        return

    planilha = Workbook()
    aba = planilha.active
    aba.title = config.ABA_ESTOQUE
    escrever_cabecalho(aba, config.COLUNAS, config.LARGURAS)
    for criar in ABAS_EXTRAS.values():
        criar(planilha)
    salvar(planilha)


def abrir():
    """Abre a planilha para LER E GRAVAR.

    Retorna 3 coisas: (planilha, aba_estoque, aba_reservas_bloqueios).
    Use quando for alterar dados (e depois chame salvar(planilha)).
    """
    planilha = load_workbook(config.ARQUIVO)
    return planilha, planilha.worksheets[0], planilha[config.ABA_MOV]


def abrir_leitura():
    """Abre a planilha SÓ PARA LER — bem mais rápido em planilhas grandes.

    ⚠️ Não dá para salvar uma planilha aberta assim. Feche com planilha.close()
    quando terminar (as funções usam try/finally para garantir isso).
    """
    return load_workbook(config.ARQUIVO, read_only=True)


def salvar(planilha):
    """Grava a planilha no disco de forma ATÔMICA (tudo ou nada).

    Como funciona:
      1. grava tudo num arquivo temporário (estoque.xlsx.tmp), ao lado do original;
      2. só se a gravação terminar inteira, troca o original pelo temporário
         (os.replace: a troca é instantânea, feita pelo sistema operacional).
    Se o programa ou o computador cair no meio do passo 1, o estoque.xlsx
    original continua intacto — no máximo sobra um .tmp, que é descartado.

    O erro mais comum é o arquivo estar aberto no Excel (o Windows bloqueia a
    gravação). Nesse caso, transformamos o erro técnico numa mensagem amigável.
    """
    temporario = config.ARQUIVO.with_name(config.ARQUIVO.name + ".tmp")
    try:
        planilha.save(temporario)
        os.replace(temporario, config.ARQUIVO)
    except PermissionError:  # arquivo aberto no Excel
        raise ErroEstoque("Feche o estoque.xlsx no Excel e tente de novo.")
    except OSError as erro:  # disco cheio, pasta sem permissão, etc.
        raise ErroEstoque(f"Não foi possível gravar o estoque ({erro.strerror or erro}). Nada foi alterado.")
    finally:
        temporario.unlink(missing_ok=True)  # se sobrou um .tmp (falha no meio), apaga


# ================================================================== procurar dados

def mesmo_nome(a, b):
    """Compara dois nomes ignorando maiúsculas e espaços nas pontas.
    Assim "Caneta", "caneta" e " CANETA " são o mesmo produto."""
    return str(a).strip().lower() == str(b).strip().lower()


def achar_linha(aba, objeto):
    """Procura o produto na aba Estoque.

    Retorna a linha (3 células: objeto, quantidade, valor) ou None se não achar.
    Mudar o valor de uma célula (linha[1].value = 10) muda a planilha na memória.
    """
    for linha in aba.iter_rows(min_row=2, max_col=3):  # min_row=2 pula o cabeçalho
        if linha[0].value is not None and mesmo_nome(linha[0].value, objeto):
            return linha
    return None


def ler_movimentos(aba_mov):
    """Lê toda a aba "Reservas e Bloqueios".

    Retorna uma lista de pares (linha, Movimento):
    - linha: as células, para quem precisa ALTERAR o registro (ex.: liberar)
    - Movimento: os valores já organizados, para quem só precisa LER
    """
    resultado = []
    for linha in aba_mov.iter_rows(min_row=2, max_col=8):
        if not linha or linha[0].value is None:
            continue  # linha vazia
        # completa com None caso a linha tenha menos de 8 colunas preenchidas
        v = ([c.value for c in linha] + [None] * 8)[:8]
        resultado.append((linha, Movimento(
            id=str(v[0]), tipo=v[1], objeto=str(v[2]), quantidade=v[3] or 0,
            referencia=v[4] or "", data=v[5], status=v[6], data_fim=v[7])))
    return resultado


# ================================================================== ferramentas de saldo
# Usadas por produtos.py e reservas.py para saber quanto está disponível.

def somar_comprometido(item, movimentos):
    """Soma no item as reservas e bloqueios ATIVOS que são dele."""
    for m in movimentos:
        if m.status == config.ATIVO and mesmo_nome(m.objeto, item.objeto):
            if m.tipo == config.RESERVA:
                item.reservado += m.quantidade
            else:
                item.bloqueado += m.quantidade
    return item


def item_com_saldo(aba, aba_mov, objeto):
    """Acha o produto e calcula quanto dele está reservado/bloqueado/disponível.

    Retorna (linha, Item). Se o produto não existir, levanta ErroEstoque.
    """
    linha = achar_linha(aba, objeto)
    if not linha:
        raise ErroEstoque(f"'{str(objeto).strip()}' não existe no estoque.")
    item = Item(str(linha[0].value), linha[1].value or 0, linha[2].value or 0)
    movimentos = [m for _, m in ler_movimentos(aba_mov)]
    return linha, somar_comprometido(item, movimentos)


def mensagem_sem_saldo(item):
    """Texto de erro quando pedem mais do que está disponível."""
    msg = f"Só tem {item.disponivel} unidade(s) disponível(is) de '{item.objeto}'."
    if item.reservado or item.bloqueado:
        msg += f" ({item.reservado} reservada(s), {item.bloqueado} bloqueada(s))"
    return msg


def tirar_do_estoque(aba, linha, quantidade):
    """Diminui o total físico do produto.

    Se chegar a zero, a linha do produto é apagada da aba Estoque.
    Retorna quanto sobrou.
    """
    restante = (linha[1].value or 0) - quantidade
    if restante <= 0:
        aba.delete_rows(linha[0].row)  # linha[0].row = número da linha no Excel
        return 0
    linha[1].value = restante
    return restante


def agora():
    """Data e hora atuais, sem segundos (é o que aparece na planilha)."""
    return datetime.now().replace(second=0, microsecond=0)
