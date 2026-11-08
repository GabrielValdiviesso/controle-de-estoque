"""
RELATÓRIO DE MOVIMENTAÇÃO (PDF)
===============================
Gera um PDF com a movimentação de UM produto num período escolhido:

  1. Resumo: entradas e saídas (unidades e R$), saldo inicial → final, ajustes,
     reservas e bloqueios.
  2. Gráfico de barras: entradas × saídas por dia, semana ou mês.
  3. Gráfico de linha: saldo em estoque ao fim de cada período.
  4. Tabela com todas as movimentações do período.

Os dados vêm da aba "Movimentações" (ver historico.py).

📚 Biblioteca usada: reportlab
   - platypus (SimpleDocTemplate, Paragraph, Table): monta o documento e quebra
     as páginas sozinho
   - graphics (Drawing, VerticalBarChart, HorizontalLineChart): os gráficos

✏️  Cores dos gráficos: AZUL_ENTRADA e LARANJA_SAIDA, logo abaixo.
"""
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import config
from .historico import TIPOS_ENTRADA, TIPOS_SAIDA, listar_historico, quantidade_com_sinal
from .modelos import ErroEstoque
from .planilha import mesmo_nome
from .produtos import listar_itens
from .utilidades import moeda

# ------------------------------------------------------------------ aparência
AZUL_ENTRADA = colors.HexColor("#2a78d6")   # série 1: Entradas
LARANJA_SAIDA = colors.HexColor("#eb6834")  # série 2: Saídas
TINTA = colors.HexColor("#0b0b0b")          # texto principal
TINTA_2 = colors.HexColor("#52514e")        # texto secundário
APAGADO = colors.HexColor("#898781")        # rótulos de eixo
GRADE = colors.HexColor("#e1e0d9")          # linhas de grade
EIXO = colors.HexColor("#c3c2b7")           # linha de base
AZUL_MARCA = colors.HexColor("#0D2B85")     # azul do programa (cabeçalhos)
FUNDO_CARTAO = colors.HexColor("#F3F5FA")

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Atalhos de período mostrados na tela
PERIODOS = ["Últimos 7 dias", "Últimos 30 dias", "Este mês", "Mês passado", "Este ano", "Personalizado"]
AGRUPAMENTOS = {"Automático": "auto", "Por dia": "dia", "Por semana": "semana", "Por mês": "mes"}


# ================================================================== fontes
# A fonte padrão do PDF não tem símbolos como "→" e "−". Usamos a Segoe UI do
# Windows (existe em todo Windows); se não achar, cai para Helvetica.

def _registrar_fontes():
    pasta = Path("C:/Windows/Fonts")
    try:
        pdfmetrics.registerFont(TTFont("SegoeUI", str(pasta / "segoeui.ttf")))
        pdfmetrics.registerFont(TTFont("SegoeUI-Bold", str(pasta / "segoeuib.ttf")))
        return "SegoeUI", "SegoeUI-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


FONTE, FONTE_NEGRITO = _registrar_fontes()


def _texto_pdf(texto):
    """Troca símbolos que a Helvetica não tem (só necessário sem a Segoe UI)."""
    texto = str(texto)
    if FONTE == "Helvetica":
        texto = texto.replace("→", "->").replace("−", "-").replace("—", "-")
    return texto


# ================================================================== períodos

def periodo_do_atalho(nome, hoje=None):
    """Converte o atalho escolhido ("Este mês"...) em (data_inicial, data_final)."""
    hoje = hoje or date.today()
    if nome == "Últimos 7 dias":
        return hoje - timedelta(days=6), hoje
    if nome == "Últimos 30 dias":
        return hoje - timedelta(days=29), hoje
    if nome == "Este mês":
        return hoje.replace(day=1), hoje
    if nome == "Mês passado":
        fim = hoje.replace(day=1) - timedelta(days=1)
        return fim.replace(day=1), fim
    if nome == "Este ano":
        return hoje.replace(month=1, day=1), hoje
    return None  # Personalizado: o usuário digita as datas


def _inicio_do_grupo(dia, agrupamento):
    """Data que representa o grupo: o próprio dia, a segunda-feira da semana ou o dia 1º do mês."""
    if agrupamento == "semana":
        return dia - timedelta(days=dia.weekday())
    if agrupamento == "mes":
        return dia.replace(day=1)
    return dia


def _proximo_grupo(inicio, agrupamento):
    if agrupamento == "semana":
        return inicio + timedelta(days=7)
    if agrupamento == "mes":
        return (inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
    return inicio + timedelta(days=1)


def _rotulo(inicio, agrupamento):
    if agrupamento == "mes":
        return f"{MESES[inicio.month - 1]}/{inicio.strftime('%y')}"
    if agrupamento == "semana":
        return f"sem {inicio.strftime('%d/%m')}"
    return inicio.strftime("%d/%m")


# ================================================================== dados

@dataclass
class Periodo:
    rotulo: str
    entradas: int = 0
    saidas: int = 0
    saldo: int = 0  # total físico ao fim do período


@dataclass
class DadosRelatorio:
    produto: str
    de: date
    ate: date
    agrupamento: str
    registros: list = field(default_factory=list)   # movimentações do período (mais antiga primeiro)
    periodos: list = field(default_factory=list)    # lista de Periodo
    totais: dict = field(default_factory=dict)


def nomes_produtos():
    """Produtos que podem ser analisados: os do estoque + os que só aparecem no
    histórico (ex.: produtos já excluídos). Ordem alfabética."""
    nomes = {}
    for item in listar_itens():
        nomes.setdefault(item.objeto.lower(), item.objeto)
    for r in listar_historico():
        nomes.setdefault(r.objeto.lower(), r.objeto)
    return sorted(nomes.values(), key=str.lower)


def montar_dados(produto, de, ate, agrupamento="auto"):
    """Calcula tudo que vai no relatório (sem gerar o PDF)."""
    if de > ate:
        raise ErroEstoque("A data inicial é depois da data final.")
    dias = (ate - de).days + 1
    if agrupamento == "auto":
        agrupamento = "dia" if dias <= 31 else ("semana" if dias <= 120 else "mes")
    if agrupamento == "dia" and dias > 92:
        raise ErroEstoque("Período longo demais para agrupar por dia. Escolha semana ou mês.")

    do_produto = sorted((r for r in listar_historico()
                         if mesmo_nome(r.objeto, produto) and isinstance(r.data, datetime)),
                        key=lambda r: r.data)
    antes = [r for r in do_produto if r.data.date() < de]
    no_periodo = [r for r in do_produto if de <= r.data.date() <= ate]
    if not no_periodo:
        raise ErroEstoque(f"Nenhuma movimentação de '{produto}' entre "
                          f"{de.strftime('%d/%m/%Y')} e {ate.strftime('%d/%m/%Y')}.")
    saldo_inicial = antes[-1].saldo if antes else 0

    # cria todos os grupos do período (inclusive os sem movimentação, que ficam zerados)
    grupos = {}
    inicio = _inicio_do_grupo(de, agrupamento)
    while inicio <= ate:
        grupos[inicio] = Periodo(_rotulo(inicio, agrupamento))
        inicio = _proximo_grupo(inicio, agrupamento)

    totais = dict(entradas=0, saidas=0, valor_entradas=0.0, valor_saidas=0.0, ajustes=0,
                  reservas=0, bloqueios=0, liberacoes=0, movimentacoes=len(no_periodo),
                  saldo_inicial=saldo_inicial, saldo_final=no_periodo[-1].saldo)
    for r in no_periodo:
        p = grupos[_inicio_do_grupo(r.data.date(), agrupamento)]
        if r.tipo in TIPOS_ENTRADA:
            p.entradas += r.quantidade
            totais["entradas"] += r.quantidade
            totais["valor_entradas"] += r.quantidade * (r.valor or 0)
        elif r.tipo in TIPOS_SAIDA:
            p.saidas += r.quantidade
            totais["saidas"] += r.quantidade
            totais["valor_saidas"] += r.quantidade * (r.valor or 0)
        elif r.tipo == config.EDICAO:
            totais["ajustes"] += r.quantidade
        elif r.tipo == config.RESERVA:
            totais["reservas"] += r.quantidade
        elif r.tipo == config.BLOQUEIO:
            totais["bloqueios"] += r.quantidade
        elif r.tipo == config.LIBERACAO:
            totais["liberacoes"] += r.quantidade

    # saldo ao fim de cada grupo: o último saldo registrado até ali
    saldo = saldo_inicial
    por_grupo = {}
    for r in no_periodo:
        por_grupo[_inicio_do_grupo(r.data.date(), agrupamento)] = r.saldo
    for inicio, p in grupos.items():
        saldo = por_grupo.get(inicio, saldo)
        p.saldo = saldo

    nome_exibido = no_periodo[-1].objeto
    return DadosRelatorio(nome_exibido, de, ate, agrupamento, no_periodo, list(grupos.values()), totais)


# ================================================================== gráficos

def _escala(maximo):
    """Topo e passo "redondos" para o eixo (ex.: máx 37 → topo 40, passo 10)."""
    maximo = max(maximo, 1)
    bruto = maximo / 5
    potencia = 10 ** math.floor(math.log10(bruto)) if bruto >= 1 else 1
    passo = next(m * potencia for m in (1, 2, 5, 10) if m * potencia >= bruto)
    passo = max(int(passo), 1)
    return math.ceil(maximo / passo) * passo, passo


def _rotulos_espacados(rotulos, maximo=14):
    """Mostra no máximo ~14 rótulos no eixo (os outros ficam em branco)."""
    if len(rotulos) <= maximo:
        return rotulos
    pulo = math.ceil(len(rotulos) / maximo)
    return [r if i % pulo == 0 else "" for i, r in enumerate(rotulos)]


def _configurar_eixos(grafico, rotulos, topo, passo):
    grafico.valueAxis.valueMin = 0
    grafico.valueAxis.valueMax = topo
    grafico.valueAxis.valueStep = passo
    grafico.valueAxis.visibleGrid = True
    grafico.valueAxis.gridStrokeColor = GRADE
    grafico.valueAxis.gridStrokeWidth = 0.5
    grafico.valueAxis.strokeColor = colors.white  # sem linha vertical do eixo (grade basta)
    grafico.valueAxis.labels.fontName = FONTE
    grafico.valueAxis.labels.fontSize = 7
    grafico.valueAxis.labels.fillColor = APAGADO
    grafico.categoryAxis.categoryNames = _rotulos_espacados(rotulos)
    grafico.categoryAxis.strokeColor = EIXO
    grafico.categoryAxis.labels.fontName = FONTE
    grafico.categoryAxis.labels.fontSize = 7
    grafico.categoryAxis.labels.fillColor = APAGADO
    grafico.categoryAxis.labels.dy = -3
    grafico.categoryAxis.visibleTicks = False


def grafico_entradas_saidas(dados, largura):
    """Barras agrupadas: Entradas (azul) × Saídas (laranja) por período."""
    altura = 6.2 * cm
    desenho = Drawing(largura, altura)
    g = VerticalBarChart()
    g.x, g.y = 28, 22
    g.width, g.height = largura - 36, altura - 50
    g.data = [[p.entradas for p in dados.periodos], [p.saidas for p in dados.periodos]]
    topo, passo = _escala(max(max(g.data[0]), max(g.data[1])))
    _configurar_eixos(g, [p.rotulo for p in dados.periodos], topo, passo)
    g.bars.strokeWidth = 0
    g.bars[0].fillColor = AZUL_ENTRADA
    g.bars[1].fillColor = LARANJA_SAIDA
    n = len(dados.periodos)
    g.barSpacing = 1.5                       # pequeno respiro entre a barra azul e a laranja
    g.groupSpacing = 10 if n <= 12 else 4
    if n <= 12:  # poucos períodos: mostra o número em cima de cada barra (exceto zero)
        g.barLabelFormat = lambda v: f"{int(v)}" if v else ""
        g.barLabels.fontName = FONTE
        g.barLabels.fontSize = 7
        g.barLabels.fillColor = TINTA_2
        g.barLabels.nudge = 6
    desenho.add(g)

    legenda = Legend()
    legenda.x, legenda.y = largura - 150, altura - 6
    legenda.alignment = "right"
    legenda.columnMaximum = 1
    legenda.deltax = 70
    legenda.dx = legenda.dy = 7
    legenda.fontName = FONTE
    legenda.fontSize = 8
    legenda.fillColor = TINTA_2
    legenda.strokeWidth = 0
    legenda.colorNamePairs = [(AZUL_ENTRADA, "Entradas"), (LARANJA_SAIDA, "Saídas")]
    desenho.add(legenda)
    return desenho


def grafico_saldo(dados, largura):
    """Linha: saldo em estoque ao fim de cada período (uma série, sem legenda)."""
    altura = 5.2 * cm
    desenho = Drawing(largura, altura)
    g = HorizontalLineChart()
    g.x, g.y = 28, 22
    g.width, g.height = largura - 36, altura - 34
    g.data = [[p.saldo for p in dados.periodos]]
    topo, passo = _escala(max(g.data[0]))
    _configurar_eixos(g, [p.rotulo for p in dados.periodos], topo, passo)
    g.joinedLines = 1
    g.lines[0].strokeColor = AZUL_ENTRADA
    g.lines[0].strokeWidth = 2
    if len(dados.periodos) <= 31:
        g.lines[0].symbol = makeMarker("FilledCircle", size=4, fillColor=AZUL_ENTRADA, strokeColor=colors.white,
                                       strokeWidth=1)
    desenho.add(g)
    return desenho


# ================================================================== PDF

def _estilos():
    base = dict(fontName=FONTE, textColor=TINTA, alignment=TA_LEFT)
    return {
        "titulo": ParagraphStyle("titulo", fontName=FONTE_NEGRITO, fontSize=18, leading=22, textColor=AZUL_MARCA),
        "sub": ParagraphStyle("sub", fontSize=10.5, leading=14, **{**base, "textColor": TINTA_2}),
        "secao": ParagraphStyle("secao", fontName=FONTE_NEGRITO, fontSize=11.5, leading=15, textColor=TINTA,
                                spaceBefore=10, spaceAfter=4),
        "celula": ParagraphStyle("celula", fontSize=8, leading=10, **base),
        "rotulo": ParagraphStyle("rotulo", fontSize=8, leading=10, **{**base, "textColor": TINTA_2}),
        "numero": ParagraphStyle("numero", fontName=FONTE_NEGRITO, fontSize=14, leading=17, textColor=TINTA),
        "nota": ParagraphStyle("nota", fontSize=8, leading=10, **{**base, "textColor": APAGADO}),
    }


def _cartoes(dados, est, largura):
    """Resumo em 4 "cartões" lado a lado."""
    t = dados.totais

    def cartao(rotulo, numero, detalhe=""):
        return [Paragraph(rotulo, est["rotulo"]), Paragraph(_texto_pdf(numero), est["numero"]),
                Paragraph(_texto_pdf(detalhe), est["rotulo"])]

    variacao = t["saldo_final"] - t["saldo_inicial"]
    sinal = "+" if variacao > 0 else ("−" if variacao < 0 else "")
    linha = [
        cartao("Entradas", f"{t['entradas']} un.", moeda(t["valor_entradas"])),
        cartao("Saídas", f"{t['saidas']} un.", moeda(t["valor_saidas"])),
        cartao("Saldo no período", f"{t['saldo_inicial']} → {t['saldo_final']}", f"variação {sinal}{abs(variacao)} un."),
        cartao("Movimentações", str(t["movimentacoes"]), f"ajustes de inventário: {t['ajustes']:+d} un."),
    ]
    tabela = Table([linha], colWidths=[largura / 4] * 4)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FUNDO_CARTAO),
        ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white),  # "respiro" entre os cartões
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ]))
    return tabela


def _tabela_movimentacoes(dados, est, largura):
    cabecalho = ["Data", "Tipo", "Qtd", "Saldo", "Valor", "Observação"]
    linhas = [[Paragraph(f"<b>{c}</b>", ParagraphStyle("h", parent=est["celula"], textColor=colors.white))
               for c in cabecalho]]
    for r in dados.registros:
        linhas.append([
            Paragraph(r.data.strftime("%d/%m/%y %H:%M"), est["celula"]),
            Paragraph(r.tipo, est["celula"]),
            Paragraph(_texto_pdf(quantidade_com_sinal(r)), est["celula"]),
            Paragraph(str(r.saldo), est["celula"]),
            Paragraph(moeda(r.valor or 0), est["celula"]),
            Paragraph(_texto_pdf(r.observacao or "—").replace("&", "&amp;").replace("<", "&lt;"), est["celula"]),
        ])
    larguras = [2.6 * cm, 2.0 * cm, 1.3 * cm, 1.3 * cm, 2.0 * cm]
    larguras.append(largura - sum(larguras))
    tabela = Table(linhas, colWidths=larguras, repeatRows=1)  # repeatRows: repete o cabeçalho a cada página
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_MARCA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO_CARTAO]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, GRADE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabela


def gerar_pdf_movimentacao(caminho, produto, de, ate, agrupamento="auto", gerado_por=""):
    """Gera o PDF do relatório de movimentação de UM produto. Retorna o caminho."""
    dados = montar_dados(produto, de, ate, agrupamento)
    est = _estilos()
    margem = 1.8 * cm
    largura = A4[0] - 2 * margem
    nome_grupo = {"dia": "dia", "semana": "semana", "mes": "mês"}[dados.agrupamento]
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    conteudo = [
        Paragraph("Relatório de movimentação", est["titulo"]),
        Paragraph(_texto_pdf(f"<b>{dados.produto}</b>  •  {de.strftime('%d/%m/%Y')} a {ate.strftime('%d/%m/%Y')}"
                             f"  •  agrupado por {nome_grupo}"), est["sub"]),
        Paragraph(_texto_pdf(f"Gerado em {agora}" + (f" por {gerado_por}" if gerado_por else "")), est["nota"]),
        Spacer(1, 10),
        _cartoes(dados, est, largura),
    ]
    t = dados.totais
    extras = []
    if t["reservas"] or t["bloqueios"] or t["liberacoes"]:
        extras.append(f"Reservado: {t['reservas']} un.  •  Bloqueado: {t['bloqueios']} un.  •  "
                      f"Liberado: {t['liberacoes']} un.  (não mudam o total físico)")
    if extras:
        conteudo += [Spacer(1, 4), Paragraph(_texto_pdf(extras[0]), est["nota"])]

    conteudo += [
        KeepTogether([Paragraph(f"Entradas e saídas por {nome_grupo}", est["secao"]),
                      grafico_entradas_saidas(dados, largura)]),
        KeepTogether([Paragraph(f"Saldo em estoque (ao fim de cada {nome_grupo})", est["secao"]),
                      grafico_saldo(dados, largura)]),
        Paragraph(f"Movimentações do período ({t['movimentacoes']})", est["secao"]),
        _tabela_movimentacoes(dados, est, largura),
        Spacer(1, 6),
        Paragraph("Entradas = entradas manuais e importações. Saídas = retiradas, baixas e exclusões. "
                  "Ajustes = edições de quantidade (inventário).", est["nota"]),
    ]

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONTE, 7.5)
        canvas.setFillColor(APAGADO)
        canvas.drawString(margem, 1.1 * cm, _texto_pdf(f"Controle de Estoque  •  {dados.produto}"))
        canvas.drawRightString(A4[0] - margem, 1.1 * cm, f"Página {doc.page}")
        canvas.restoreState()

    documento = SimpleDocTemplate(str(caminho), pagesize=A4, leftMargin=margem, rightMargin=margem,
                                  topMargin=margem, bottomMargin=margem,
                                  title=f"Relatório de movimentação - {dados.produto}")
    try:
        documento.build(conteudo, onFirstPage=rodape, onLaterPages=rodape)
    except PermissionError:
        raise ErroEstoque("Não consegui salvar o PDF. Se ele estiver aberto, feche e tente de novo.")
    return caminho
