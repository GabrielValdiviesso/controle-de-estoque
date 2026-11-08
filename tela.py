"""Janela gráfica do Controle de Estoque.

Rode com:  python tela.py
O banco de dados continua sendo o estoque.xlsx (toda a lógica fica na pasta banco/).
"""
import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

import banco

# ---------------------------------------------------------------- aparência

AZUL_ESCURO = "#0A2472"   # cabeçalho
AZUL_ONDA = "#15378F"     # ondas do cabeçalho
AZUL_BOTAO = "#0D2B85"
AZUL_HOVER = "#1E46B8"
AZUL_MEDIO = "#5B74B8"
AZUL_CLARO = "#E3E9F7"
FUNDO = "#F3F5FA"
BRANCO = "#FFFFFF"
TEXTO = "#1B2440"
CINZA = "#6B7280"
VERDE = "#1E8E3E"
VERMELHO = "#C62828"
LARANJA = "#B26A00"

FONTE = "Segoe UI"
ESTOQUE_BAIXO = 5  # itens com essa quantidade DISPONÍVEL ou menos aparecem no relatório


def fonte(tamanho, negrito=False):
    return ctk.CTkFont(FONTE, tamanho, "bold" if negrito else "normal")


def desenhar_icone(tipo, cor="white"):
    """Desenha o ícone em alta resolução (fica nítido depois de reduzido)."""
    S = 160
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    vazio = (0, 0, 0, 0)

    if tipo == "caixa":
        c = S / 2
        d.polygon([(c, S * .06), (S * .94, S * .28), (c, S * .50), (S * .06, S * .28)], fill=cor)
        d.polygon([(S * .06, S * .34), (c - 5, S * .56), (c - 5, S * .96), (S * .06, S * .74)], fill=cor)
        d.polygon([(S * .94, S * .34), (c + 5, S * .56), (c + 5, S * .96), (S * .94, S * .74)], fill=cor)
        d.line([(S * .28, S * .17), (S * .72, S * .39)], fill=vazio, width=10)  # fita da caixa
    elif tipo == "mais":
        d.rounded_rectangle([S * .42, S * .08, S * .58, S * .92], radius=12, fill=cor)
        d.rounded_rectangle([S * .08, S * .42, S * .92, S * .58], radius=12, fill=cor)
    elif tipo == "cadeado":
        w = 15
        d.arc([S * .26, S * .04, S * .74, S * .52], 180, 360, fill=cor, width=w)
        d.line([(S * .26 + w / 2, S * .27), (S * .26 + w / 2, S * .48)], fill=cor, width=w)
        d.line([(S * .74 - w / 2, S * .27), (S * .74 - w / 2, S * .48)], fill=cor, width=w)
        d.rounded_rectangle([S * .12, S * .42, S * .88, S * .95], radius=16, fill=cor)
        d.ellipse([S * .43, S * .55, S * .57, S * .69], fill=vazio)
        d.rectangle([S * .47, S * .64, S * .53, S * .81], fill=vazio)
    elif tipo == "prancheta":
        w = 13
        d.rounded_rectangle([S * .16, S * .12, S * .84, S * .95], radius=14, outline=cor, width=w)
        d.rounded_rectangle([S * .34, S * .04, S * .66, S * .22], radius=8, fill=cor)
        for y in (.42, .60, .78):
            d.line([(S * .32, S * y), (S * .68, S * y)], fill=cor, width=11)
    elif tipo == "relogio":
        w = 14
        d.ellipse([S * .08, S * .08, S * .92, S * .92], outline=cor, width=w)
        d.line([(S * .5, S * .5), (S * .5, S * .24)], fill=cor, width=w)
        d.line([(S * .5, S * .5), (S * .70, S * .62)], fill=cor, width=w)
        d.ellipse([S * .44, S * .44, S * .56, S * .56], fill=cor)
    elif tipo == "barras":
        for x, topo in ((.08, .58), (.39, .34), (.70, .08)):
            d.rounded_rectangle([S * x, S * topo, S * (x + .22), S * .92], radius=8, fill=cor)
    elif tipo == "sair":
        w = 13
        d.line([(S * .55, S * .12), (S * .12, S * .12), (S * .12, S * .88), (S * .55, S * .88)],
               fill=cor, width=w, joint="curve")
        d.line([(S * .38, S * .50), (S * .90, S * .50)], fill=cor, width=w)
        d.line([(S * .70, S * .30), (S * .91, S * .50), (S * .70, S * .70)], fill=cor, width=w, joint="curve")
    return img


# ---------------------------------------------------------------- componentes

class Cabecalho(tk.Canvas):
    """Faixa azul com ondas, ícone da caixa e o título."""

    def __init__(self, master, escala):
        self.s = escala
        super().__init__(master, height=int(150 * escala), bg=AZUL_ESCURO, highlightthickness=0)
        tam = int(80 * escala)
        self.icone = ImageTk.PhotoImage(desenhar_icone("caixa").resize((tam, tam), Image.LANCZOS))
        self.bind("<Configure>", self.desenhar)

    def desenhar(self, _evento=None):
        self.delete("all")
        w, h, s = self.winfo_width(), self.winfo_height(), self.s
        # ondas
        self.create_polygon(0, h * .45, w * .18, h * .62, w * .32, h, w * .32, h, 0, h, 0, h,
                            fill=AZUL_ONDA, outline="", smooth=True)
        self.create_polygon(w * .62, 0, w * .62, 0, w, 0, w, 0, w, h * .75, w * .86, h * .35,
                            fill=AZUL_ONDA, outline="", smooth=True)
        # ícone | título
        cx, cy = w / 2, h / 2
        self.create_image(cx - 120 * s, cy, image=self.icone)
        self.create_line(cx - 52 * s, cy - 46 * s, cx - 52 * s, cy + 46 * s, fill="white", width=max(2, int(2 * s)))
        self.create_text(cx - 24 * s, cy, text="Controle de\nEstoque", anchor="w", fill="white",
                         font=(FONTE, -int(32 * s), "bold"))


class BotaoMenu(ctk.CTkFrame):
    """Botão grande arredondado com ícone + texto (como na imagem de referência)."""

    def __init__(self, master, texto, icone, comando):
        super().__init__(master, fg_color=AZUL_BOTAO, corner_radius=18, height=56)
        self.pack_propagate(False)
        self.comando = comando
        imagem = ctk.CTkImage(desenhar_icone(icone), size=(32, 32))
        self.lb_icone = ctk.CTkLabel(self, text="", image=imagem, width=40)
        self.lb_texto = ctk.CTkLabel(self, text=texto, font=fonte(21, True), text_color="white")
        self.lb_icone.place(relx=.28, rely=.5, anchor="center")
        self.lb_texto.place(relx=.28, x=40, rely=.5, anchor="w")

        for widget in (self, self.lb_icone, self.lb_texto):
            widget.bind("<Button-1>", lambda _e: self.comando())
            widget.bind("<Enter>", lambda _e: self.configure(fg_color=AZUL_HOVER))
            widget.bind("<Leave>", self._saiu)

    def _saiu(self, _evento):
        # só volta a cor se o mouse saiu de verdade do botão (e não entrou no texto/ícone)
        x, y = self.winfo_pointerxy()
        dentro = (self.winfo_rootx() <= x < self.winfo_rootx() + self.winfo_width()
                  and self.winfo_rooty() <= y < self.winfo_rooty() + self.winfo_height())
        if not dentro:
            self.configure(fg_color=AZUL_BOTAO)


def botao(master, texto, comando, **extra):
    opcoes = dict(fg_color=AZUL_BOTAO, hover_color=AZUL_HOVER, corner_radius=12,
                  height=44, font=fonte(16, True))
    opcoes.update(extra)
    return ctk.CTkButton(master, text=texto, command=comando, **opcoes)


def botao_claro(master, texto, comando, **extra):
    """Botão secundário (azul clarinho), para ações como Editar, Cancelar, Limpar."""
    opcoes = dict(width=86, height=38, corner_radius=10, fg_color=AZUL_CLARO, hover_color="#CBD6F0",
                  text_color=AZUL_BOTAO, font=fonte(13, True))
    opcoes.update(extra)
    return ctk.CTkButton(master, text=texto, command=comando, **opcoes)


def ler_data_campo(campo, borda="#C9D2E8"):
    """Data digitada num filtro (dd/mm/aaaa ou dd/mm/aa). Vazio → None.
    Se for inválida, deixa a borda vermelha e devolve None (filtro ignorado)."""
    texto = campo.get().strip()
    campo.configure(border_color=borda)
    if not texto:
        return None
    for formato in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    campo.configure(border_color=VERMELHO)
    return None


def estilo_tabelas(escala):
    """Visual das tabelas (ttk.Treeview) — chamado uma vez ao abrir a janela."""
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Estoque.Treeview", background=BRANCO, fieldbackground=BRANCO, foreground=TEXTO,
                     rowheight=int(30 * escala), font=(FONTE, -int(14 * escala)), borderwidth=0)
    estilo.configure("Estoque.Treeview.Heading", background=AZUL_BOTAO, foreground="white",
                     font=(FONTE, -int(14 * escala), "bold"), relief="flat", padding=int(5 * escala))
    estilo.map("Estoque.Treeview.Heading", background=[("active", AZUL_HOVER)])
    estilo.map("Estoque.Treeview", background=[("selected", AZUL_HOVER)], foreground=[("selected", "white")])
    estilo.layout("Estoque.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])  # sem borda


def criar_tabela(master, colunas, escala):
    """colunas: lista de (chave, título, largura, alinhamento). A 1ª coluna de texto estica.
    Retorna (moldura, tabela)."""
    moldura = ctk.CTkFrame(master, fg_color=BRANCO, corner_radius=12)
    tabela = ttk.Treeview(moldura, columns=[c[0] for c in colunas], show="headings",
                          style="Estoque.Treeview", selectmode="browse")
    for chave, titulo, largura, lado in colunas:
        tabela.heading(chave, text=titulo, anchor=lado)
        tabela.column(chave, width=int(largura * escala), minwidth=int(40 * escala), anchor=lado,
                      stretch=lado == "w")
    tabela.tag_configure("par", background="#F6F8FD")
    tabela.tag_configure("encerrado", foreground="#9AA0AC")
    rolagem = ctk.CTkScrollbar(moldura, command=tabela.yview, height=40)  # height baixo: não força altura mínima
    tabela.configure(yscrollcommand=rolagem.set)
    tabela.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    rolagem.pack(side="right", fill="y", padx=4, pady=8)
    return moldura, tabela


def criar_abas(master):
    abas = ctk.CTkTabview(
        master, fg_color=BRANCO, corner_radius=14, text_color="white",
        segmented_button_fg_color=AZUL_MEDIO, segmented_button_selected_color=AZUL_BOTAO,
        segmented_button_selected_hover_color=AZUL_HOVER, segmented_button_unselected_color=AZUL_MEDIO,
        segmented_button_unselected_hover_color=AZUL_HOVER)
    abas.pack(fill="both", expand=True)
    abas._segmented_button.configure(font=fonte(14, True))
    return abas


def mensagem(master):
    return ctk.CTkLabel(master, text="", font=fonte(14), wraplength=540, justify="left")


def avisar(rotulo, texto, erro=False):
    rotulo.configure(text=texto, text_color=VERMELHO if erro else VERDE)


class TelaComTitulo(ctk.CTkFrame):
    """Base das telas internas: botão Voltar + título + área de mensagem."""

    titulo = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", pady=(0, 12))
        ctk.CTkButton(topo, text="← Voltar", width=90, height=34, corner_radius=10,
                      fg_color=AZUL_CLARO, hover_color="#CBD6F0", text_color=AZUL_BOTAO,
                      font=fonte(14, True), command=app.ir_inicio).pack(side="left")
        ctk.CTkLabel(topo, text=self.titulo, font=fonte(22, True), text_color=TEXTO).pack(side="left", padx=16)
        self.mensagem = mensagem(self)

    def avisar(self, texto, erro=False):
        avisar(self.mensagem, texto, erro)


# ---------------------------------------------------------------- telas

class TelaInicio(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        itens = [
            ("Ver Estoque", "caixa", lambda: app.mostrar(TelaEstoque)),
            ("Adicionar Produto", "mais", lambda: app.mostrar(TelaAdicionar)),
            ("Reservas e Bloqueios", "cadeado", lambda: app.mostrar(TelaReservas)),
            ("Requisições", "prancheta", lambda: app.mostrar(TelaRequisicoes)),
            ("Movimentações", "relogio", lambda: app.mostrar(TelaHistorico)),
            ("Relatórios", "barras", lambda: app.mostrar(TelaRelatorios)),
            ("Sair", "sair", app.destroy),
        ]
        for texto, icone, comando in itens:
            BotaoMenu(self, texto, icone, comando).pack(fill="x", pady=5)


class TelaEstoque(TelaComTitulo):
    titulo = "Estoque"

    def __init__(self, master, app):
        super().__init__(master, app)

        # a parte de baixo é montada primeiro (side="bottom") para a tabela não espremê-la
        self.mensagem.pack(side="bottom", fill="x", pady=(8, 0))
        retirada = ctk.CTkFrame(self, fg_color=BRANCO, corner_radius=12)
        retirada.pack(side="bottom", fill="x", pady=(6, 0))
        ctk.CTkLabel(retirada, text="Retirar do selecionado:", font=fonte(14), text_color=TEXTO
                     ).pack(side="left", padx=(14, 8), pady=12)
        self.qtd = ctk.CTkEntry(retirada, width=64, height=38, placeholder_text="Qtd", font=fonte(15),
                                justify="center")
        self.qtd.pack(side="left")
        botao(retirada, "Retirar", self.retirar, width=90, height=38).pack(side="right", padx=(6, 12))
        self.obs = ctk.CTkEntry(retirada, height=38, font=fonte(13), border_color="#C9D2E8",
                                placeholder_text="Observação (opcional)")
        self.obs.pack(side="left", fill="x", expand=True, padx=(6, 0))
        for campo in (self.qtd, self.obs):
            campo.bind("<Return>", lambda _e: self.retirar())
        self.total = ctk.CTkLabel(self, text="", font=fonte(17, True), text_color=TEXTO, anchor="e")
        self.total.pack(side="bottom", fill="x", pady=(10, 4))

        # barra de pesquisa
        pesquisa = ctk.CTkFrame(self, fg_color="transparent")
        pesquisa.pack(fill="x", pady=(0, 8))
        self.busca = ctk.CTkEntry(pesquisa, height=38, font=fonte(15), border_color="#C9D2E8",
                                  placeholder_text="🔍  Pesquisar produto pelo nome")
        self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<KeyRelease>", self._digitou)
        self.busca.bind("<Return>", lambda _e: self._enter_na_busca())
        self.busca.bind("<Escape>", lambda _e: self._limpar_busca())
        self.contador = ctk.CTkLabel(pesquisa, text="", font=fonte(13), text_color=CINZA)
        self.contador.pack(side="left", padx=(10, 0))
        botao_claro(pesquisa, "✏ Editar", self.editar).pack(side="left", padx=(10, 0))
        botao_claro(pesquisa, "🗑 Excluir", self.excluir, text_color=VERMELHO).pack(side="left", padx=(6, 0))
        self._agendado = None

        moldura, self.tabela = criar_tabela(self, [
            ("objeto", "Objeto", 130, "w"), ("total", "Total", 52, "center"),
            ("res", "Reserv.", 62, "center"), ("bloq", "Bloq.", 50, "center"),
            ("disp", "Disp.", 52, "center"), ("valor", "Valor", 82, "e"), ("vtotal", "Valor total", 112, "e"),
        ], app.escala)
        moldura.pack(fill="both", expand=True)
        self.tabela.bind("<Double-1>", lambda _e: self.editar())  # dois cliques = editar

        self.itens = []      # todos os produtos
        self.visiveis = []   # os que aparecem na tabela (depois da pesquisa)
        self.recarregar()
        self.after(100, self.busca.focus)

    LIMITE_LINHAS = 300  # desenhar milhares de linhas deixa a janela lenta; a pesquisa resolve

    def recarregar(self):
        self.itens = banco.listar_itens()
        for item in self.itens:
            item.chave = item.objeto.lower()
        if not self.itens:
            self.avisar("O estoque está vazio. Use 'Adicionar Produto' para cadastrar.")
        total = sum(i.valor_total for i in self.itens)
        self.total.configure(text=f"Valor total do estoque:  {banco.moeda(total)}")
        self._preencher()

    def _digitou(self, evento):
        if evento.keysym in ("Return", "Escape"):
            return
        # espera a pessoa parar de digitar um instante antes de filtrar
        if self._agendado:
            self.after_cancel(self._agendado)
        self._agendado = self.after(200, self._preencher)

    def _preencher(self):
        self._agendado = None
        termo = self.busca.get().strip().lower()
        encontrados = [i for i in self.itens if termo in i.chave] if termo else self.itens
        if termo:  # quem começa com o termo aparece primeiro
            encontrados.sort(key=lambda i: (not i.chave.startswith(termo), i.chave))
        self.visiveis = encontrados[:self.LIMITE_LINHAS]

        self.tabela.delete(*self.tabela.get_children())
        for i, item in enumerate(self.visiveis):
            self.tabela.insert("", "end", iid=str(i), tags=("par",) if i % 2 else (), values=(
                item.objeto, item.quantidade, item.reservado, item.bloqueado, item.disponivel,
                banco.moeda(item.valor), banco.moeda(item.valor_total)))

        n = len(encontrados)
        if n > self.LIMITE_LINHAS:
            texto = f"mostrando {self.LIMITE_LINHAS} de {n:,}".replace(",", ".")
        elif termo:
            texto = f"{n} encontrado(s)"
        else:
            texto = f"{n:,} produto(s)".replace(",", ".")
        self.contador.configure(text=texto, text_color=LARANJA if n > self.LIMITE_LINHAS else CINZA)
        if termo and n == 0:
            self.avisar(f"Nenhum produto com '{self.busca.get().strip()}'.", erro=True)
        elif self.mensagem.cget("text").startswith("Nenhum produto"):
            self.avisar("")

    def _enter_na_busca(self):
        if self._agendado:
            self.after_cancel(self._agendado)
        self._preencher()
        if self.visiveis:  # Enter seleciona o primeiro resultado e vai para a quantidade
            self.tabela.selection_set("0")
            self.tabela.see("0")
            self.qtd.focus()

    def _limpar_busca(self):
        self.busca.delete(0, "end")
        self._preencher()

    def _item_selecionado(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            self.avisar("Clique em um item da tabela primeiro.", erro=True)
            return None
        return self.visiveis[int(selecionado[0])]

    def _selecionar(self, nome):
        """Seleciona (e rola até) o produto com esse nome, se estiver na tabela."""
        for i, item in enumerate(self.visiveis):
            if item.objeto == nome:
                self.tabela.selection_set(str(i))
                self.tabela.see(str(i))

    def retirar(self):
        item = self._item_selecionado()
        if not item:
            return
        try:
            quantidade = banco.converter_numero(self.qtd.get(), inteiro=True, nome="quantidade")
            msg = banco.retirar(item.objeto, quantidade, self.obs.get())
        except banco.ErroEstoque as erro:
            return self.avisar(str(erro), erro=True)
        self.qtd.delete(0, "end")
        self.obs.delete(0, "end")
        self.recarregar()
        self._selecionar(item.objeto)  # mantém o mesmo item selecionado
        self.avisar(msg)

    def editar(self):
        item = self._item_selecionado()
        if item:
            JanelaEditar(self, item)

    def depois_de_editar(self, nome, msg):
        """Chamado pela JanelaEditar depois de salvar."""
        self.recarregar()
        self._selecionar(nome)
        self.avisar(msg)

    def excluir(self):
        item = self._item_selecionado()
        if not item:
            return
        if not messagebox.askyesno(
                "Excluir produto",
                f"Excluir '{item.objeto}' do estoque?\n\n{item.quantidade} unidade(s) vão sair.\n"
                "A exclusão fica registrada em Movimentações.", parent=self):
            return
        try:
            msg = banco.excluir(item.objeto)
        except banco.ErroEstoque as erro:
            return self.avisar(str(erro), erro=True)
        self.recarregar()
        self.avisar(msg)


class JanelaEditar(ctk.CTkToplevel):
    """Janelinha para corrigir nome, quantidade total e valor de um produto."""

    def __init__(self, tela, item):
        super().__init__(tela)
        self.tela, self.item = tela, item
        self.title("Editar produto")
        self.configure(fg_color=FUNDO)
        self.resizable(False, False)
        self.transient(tela.winfo_toplevel())  # fica sempre na frente da janela principal

        cartao = ctk.CTkFrame(self, fg_color=BRANCO, corner_radius=14)
        cartao.pack(fill="both", expand=True, padx=18, pady=18)
        ctk.CTkLabel(cartao, text="Editar produto", font=fonte(19, True), text_color=TEXTO, anchor="w"
                     ).pack(fill="x", padx=20, pady=(16, 0))

        # valor sem perder casas decimais (2,5 → "2,50"; 0,333 → "0,333")
        valor = f"{item.valor:.2f}" if round(item.valor, 2) == item.valor else str(item.valor)
        self.campos = {}
        for chave, rotulo, atual in (("nome", "Nome", item.objeto),
                                     ("qtd", "Quantidade total", str(item.quantidade)),
                                     ("valor", "Valor unitário (R$)", valor.replace(".", ","))):
            ctk.CTkLabel(cartao, text=rotulo, font=fonte(14, True), text_color=TEXTO, anchor="w"
                         ).pack(fill="x", padx=20, pady=(12, 3))
            campo = ctk.CTkEntry(cartao, width=340, height=38, font=fonte(15), border_color="#C9D2E8")
            campo.insert(0, atual)
            campo.pack(fill="x", padx=20)
            campo.bind("<Return>", lambda _e: self.salvar())
            self.campos[chave] = campo
            if chave == "qtd" and (item.reservado or item.bloqueado):
                ctk.CTkLabel(cartao, text=f"Mínimo {item.reservado + item.bloqueado} "
                                          f"({item.reservado} reservada(s) + {item.bloqueado} bloqueada(s))",
                             font=fonte(12), text_color=CINZA, anchor="w").pack(fill="x", padx=22)

        ctk.CTkLabel(cartao, text="Observação (opcional)", font=fonte(14, True), text_color=TEXTO, anchor="w"
                     ).pack(fill="x", padx=20, pady=(12, 3))
        self.obs = ctk.CTkEntry(cartao, height=38, font=fonte(14), border_color="#C9D2E8",
                                placeholder_text="Ex.: correção de cadastro, contagem")
        self.obs.pack(fill="x", padx=20)
        self.obs.bind("<Return>", lambda _e: self.salvar())

        self.mensagem = ctk.CTkLabel(cartao, text="", font=fonte(13), wraplength=340, justify="left")
        self.mensagem.pack(fill="x", padx=20, pady=(8, 0))
        botoes = ctk.CTkFrame(cartao, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(6, 18))
        botao_claro(botoes, "Cancelar", self.destroy, width=110, height=42).pack(side="left")
        botao(botoes, "Salvar", self.salvar, height=42).pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.bind("<Escape>", lambda _e: self.destroy())

        # centraliza sobre a janela principal
        self.update_idletasks()
        pai = tela.winfo_toplevel()
        x = pai.winfo_rootx() + (pai.winfo_width() - self.winfo_width()) // 2
        y = pai.winfo_rooty() + (pai.winfo_height() - self.winfo_height()) // 3
        self.wm_geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.after(150, self._focar)

    def _focar(self):
        self.grab_set()  # enquanto esta janela estiver aberta, a principal não recebe cliques
        self.campos["nome"].focus()

    def salvar(self):
        try:
            nome = self.campos["nome"].get()
            quantidade = banco.converter_numero(self.campos["qtd"].get(), inteiro=True, nome="quantidade")
            valor = banco.converter_numero(self.campos["valor"].get(), nome="valor")
            msg = banco.editar(self.item.objeto, nome, quantidade, valor, self.obs.get())
        except banco.ErroEstoque as erro:
            return self.mensagem.configure(text=str(erro), text_color=VERMELHO)
        self.destroy()
        self.tela.depois_de_editar(nome.strip(), msg)


class TelaAdicionar(TelaComTitulo):
    titulo = "Adicionar Produto"

    def __init__(self, master, app):
        super().__init__(master, app)
        abas = self.abas = criar_abas(self)
        self._montar_um_produto(abas.add("Um produto"))
        self._montar_importacao(abas.add("Importar lista"))
        self.after(100, self.campos["objeto"].focus)

    # ---------------------------------------------------- aba "Um produto"
    def _montar_um_produto(self, aba):
        self.campos = {}
        for chave, rotulo, dica in (("objeto", "Objeto", "Ex.: Caneta azul"),
                                    ("qtd", "Quantidade", "Ex.: 10"),
                                    ("valor", "Valor unitário (R$)", "Ex.: 2,50")):
            ctk.CTkLabel(aba, text=rotulo, font=fonte(15, True), text_color=TEXTO, anchor="w"
                         ).pack(fill="x", padx=12, pady=(10, 4))
            campo = ctk.CTkEntry(aba, height=40, font=fonte(16), placeholder_text=dica,
                                 corner_radius=10, border_color="#C9D2E8")
            campo.pack(fill="x", padx=12)
            campo.bind("<Return>", lambda _e: self.salvar())
            self.campos[chave] = campo

        botao(aba, "Salvar", self.salvar, height=46, font=fonte(18, True)).pack(fill="x", padx=12, pady=(18, 8))
        ctk.CTkLabel(aba, text="Se o objeto já existir, a quantidade é somada e o valor atualizado.",
                     font=fonte(13), text_color=CINZA, wraplength=540).pack()
        self.mensagem = mensagem(aba)
        self.mensagem.pack(fill="x", padx=12, pady=(8, 0))

    # ---------------------------------------------------- aba "Importar lista"
    def _montar_importacao(self, aba):
        ctk.CTkLabel(aba, text="Importe uma planilha Excel (.xlsx) ou um arquivo .csv com as colunas "
                               "Objeto, Quantidade e Valor. Produtos que já existem têm a quantidade somada.",
                     font=fonte(13), text_color=CINZA, wraplength=560, justify="left", anchor="w"
                     ).pack(fill="x", padx=4)
        botoes = ctk.CTkFrame(aba, fg_color="transparent")
        botoes.pack(fill="x", pady=(8, 4))
        botao(botoes, "📂  Escolher arquivo…", self.escolher_arquivo, height=38, font=fonte(14, True)
              ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(botoes, text="⬇  Baixar modelo", height=38, corner_radius=12, fg_color=AZUL_CLARO,
                      hover_color="#CBD6F0", text_color=AZUL_BOTAO, font=fonte(14, True),
                      command=self.baixar_modelo).pack(side="left", padx=(5, 0))
        self.arquivo = ctk.CTkLabel(aba, text="Nenhum arquivo escolhido.", font=fonte(13),
                                    text_color=CINZA, anchor="w")
        self.arquivo.pack(fill="x", padx=4)

        # parte de baixo antes da tabela (para não ser espremida)
        self.msg_importacao = mensagem(aba)
        self.msg_importacao.pack(side="bottom", fill="x", padx=4, pady=(4, 0))
        self.confirmar = botao(aba, "Confirmar importação", self.importar, height=42, hover_color="#16722F")
        self._liberar_confirmar(False)
        self.confirmar.pack(side="bottom", fill="x", pady=(6, 0))
        self.erros = ctk.CTkLabel(aba, text="", font=fonte(12), text_color=VERMELHO, anchor="w",
                                  justify="left", wraplength=560)
        self.erros.pack(side="bottom", fill="x", padx=4)

        moldura, self.previa = criar_tabela(aba, [
            ("objeto", "Objeto", 190, "w"), ("qtd", "Qtd", 60, "center"),
            ("valor", "Valor", 90, "e"), ("situacao", "Situação", 160, "w"),
        ], self.app.escala)
        moldura.configure(fg_color=FUNDO)
        moldura.pack(fill="both", expand=True, pady=(4, 0))
        self.lista = []

    def _liberar_confirmar(self, ligado, texto="Confirmar importação"):
        self.confirmar.configure(state="normal" if ligado else "disabled", text=texto,
                                 fg_color=VERDE if ligado else "#B8C0D0", text_color_disabled="white")

    def escolher_arquivo(self):
        caminho = filedialog.askopenfilename(
            parent=self, title="Escolha a lista de produtos",
            filetypes=[("Planilha ou CSV", "*.xlsx *.xlsm *.csv *.txt"), ("Todos os arquivos", "*.*")])
        if caminho:
            self.carregar_arquivo(caminho)

    def carregar_arquivo(self, caminho):
        """Lê o arquivo e mostra a prévia (ainda não grava nada)."""
        self.lista = []
        self.previa.delete(*self.previa.get_children())
        self._liberar_confirmar(False)
        self.erros.configure(text="")
        self.nome_arquivo = Path(caminho).name
        self.arquivo.configure(text=f"Arquivo: {self.nome_arquivo}", text_color=TEXTO)
        try:
            self.lista, erros = banco.ler_lista(caminho)
            existentes = {i.objeto.lower(): i for i in banco.listar_itens()}
        except banco.ErroEstoque as erro:
            return avisar(self.msg_importacao, str(erro), erro=True)

        for i, (objeto, qtd, valor) in enumerate(self.lista[:300]):  # prévia limitada p/ não travar
            atual = existentes.get(objeto.lower())
            situacao = f"Soma → fica {atual.quantidade + qtd}" if atual else "Novo"
            self.previa.insert("", "end", iid=str(i), tags=("par",) if i % 2 else (),
                               values=(objeto, qtd, banco.moeda(valor), situacao))
        novos = sum(1 for o, _, _ in self.lista if o.lower() not in existentes)

        if erros:
            mostrar = erros[:3] + ([f"… e mais {len(erros) - 3}"] if len(erros) > 3 else [])
            self.erros.configure(text=f"{len(erros)} linha(s) serão ignoradas:  " + "   •   ".join(mostrar))
        if self.lista:
            self._liberar_confirmar(True, f"Confirmar importação de {len(self.lista)} produto(s)")
            extra = "  (a prévia mostra os 300 primeiros)" if len(self.lista) > 300 else ""
            avisar(self.msg_importacao, f"Prévia: {novos} novo(s) e {len(self.lista) - novos} que já existem. "
                                        f"Nada foi gravado ainda.{extra}")
            self.msg_importacao.configure(text_color=TEXTO)
        else:
            avisar(self.msg_importacao, "Nenhuma linha válida encontrada no arquivo.", erro=True)

    def importar(self):
        if not self.lista:
            return
        avisar(self.msg_importacao, "Importando…")
        self.update_idletasks()
        try:
            msg = banco.inserir_lista(self.lista, origem=self.nome_arquivo)
        except banco.ErroEstoque as erro:
            return avisar(self.msg_importacao, str(erro), erro=True)
        self.lista = []
        self.previa.delete(*self.previa.get_children())
        self._liberar_confirmar(False)
        self.erros.configure(text="")
        self.arquivo.configure(text="Nenhum arquivo escolhido.", text_color=CINZA)
        avisar(self.msg_importacao, msg)

    def baixar_modelo(self):
        caminho = filedialog.asksaveasfilename(
            parent=self, title="Salvar modelo de importação", defaultextension=".xlsx",
            initialfile="modelo_importacao.xlsx", filetypes=[("Planilha Excel", "*.xlsx")])
        if not caminho:
            return
        try:
            banco.criar_modelo(caminho)
        except banco.ErroEstoque as erro:
            return avisar(self.msg_importacao, str(erro), erro=True)
        avisar(self.msg_importacao, f"Modelo salvo em: {caminho}  — preencha e importe aqui.")

    def salvar(self):
        try:
            objeto = self.campos["objeto"].get()
            quantidade = banco.converter_numero(self.campos["qtd"].get(), inteiro=True, nome="quantidade")
            valor = banco.converter_numero(self.campos["valor"].get(), nome="valor")
            msg = banco.inserir(objeto, quantidade, valor)
        except banco.ErroEstoque as erro:
            return self.avisar(str(erro), erro=True)
        for campo in self.campos.values():
            campo.delete(0, "end")
        self.campos["objeto"].focus()
        self.avisar(msg)


class FormMovimento(ctk.CTkFrame):
    """Formulário de Reservar ou Bloquear (fica dentro de uma aba)."""

    def __init__(self, master, tela, tipo):
        super().__init__(master, fg_color="transparent")
        self.tela, self.tipo = tela, tipo
        reserva = tipo == banco.RESERVA
        self.itens = {}

        def rotulo(texto):
            ctk.CTkLabel(self, text=texto, font=fonte(15, True), text_color=TEXTO, anchor="w"
                         ).pack(fill="x", padx=8, pady=(10, 4))

        rotulo("Objeto")
        self.objeto = tk.StringVar()
        self.objeto.trace_add("write", lambda *_: self._mostrar_disponivel())
        self.combo = ctk.CTkComboBox(self, variable=self.objeto, values=[], height=40, font=fonte(15),
                                     dropdown_font=fonte(14), button_color=AZUL_BOTAO,
                                     button_hover_color=AZUL_HOVER, border_color="#C9D2E8")
        self.combo.pack(fill="x", padx=8)
        self.disponivel = ctk.CTkLabel(self, text="", font=fonte(13), text_color=CINZA, anchor="w")
        self.disponivel.pack(fill="x", padx=10)

        rotulo("Quantidade")
        self.qtd = ctk.CTkEntry(self, height=40, font=fonte(15), placeholder_text="Ex.: 5", border_color="#C9D2E8")
        self.qtd.pack(fill="x", padx=8)
        rotulo("Pedido / solicitação (opcional)" if reserva else "Motivo (opcional)")
        self.ref = ctk.CTkEntry(self, height=40, font=fonte(15), border_color="#C9D2E8",
                                placeholder_text="Ex.: Pedido 1234" if reserva else "Ex.: Avariado, em inspeção")
        self.ref.pack(fill="x", padx=8)
        for campo in (self.qtd, self.ref):
            campo.bind("<Return>", lambda _e: self.confirmar())

        botao(self, "Reservar" if reserva else "Bloquear", self.confirmar, height=46
              ).pack(fill="x", padx=8, pady=(18, 6))
        self.mensagem = mensagem(self)
        self.mensagem.pack(fill="x", padx=8)

    def atualizar(self, itens):
        self.itens = {i.objeto.lower(): i for i in itens}
        self.combo.configure(values=[i.objeto for i in itens])
        self._mostrar_disponivel()

    def _mostrar_disponivel(self):
        item = self.itens.get(self.objeto.get().strip().lower())
        texto = f"Disponível: {item.disponivel} de {item.quantidade} unidade(s)" if item else ""
        self.disponivel.configure(text=texto)

    def confirmar(self):
        funcao = banco.reservar if self.tipo == banco.RESERVA else banco.bloquear
        try:
            quantidade = banco.converter_numero(self.qtd.get(), inteiro=True, nome="quantidade")
            _, msg = funcao(self.objeto.get(), quantidade, self.ref.get())
        except banco.ErroEstoque as erro:
            return avisar(self.mensagem, str(erro), erro=True)
        self.qtd.delete(0, "end")
        self.ref.delete(0, "end")
        self.tela.recarregar()
        avisar(self.mensagem, msg + "  Use o ID para consultar ou liberar depois.")


class TelaReservas(TelaComTitulo):
    titulo = "Reservas e Bloqueios"

    def __init__(self, master, app):
        super().__init__(master, app)
        abas = self.abas = criar_abas(self)

        self.form_reserva = FormMovimento(abas.add("Reservar"), self, banco.RESERVA)
        self.form_reserva.pack(fill="both", expand=True)
        self.form_bloqueio = FormMovimento(abas.add("Bloquear"), self, banco.BLOQUEIO)
        self.form_bloqueio.pack(fill="both", expand=True)
        self._montar_consulta(abas.add("Consultar / Liberar"))
        self.recarregar()

    FILTRO_TIPO = {"Todos os tipos": None, "Reservas": banco.RESERVA, "Bloqueios": banco.BLOQUEIO}
    FILTRO_STATUS = {"Ativos": banco.ATIVO, "Liberados": banco.LIBERADO, "Baixas": banco.BAIXA, "Todos": None}
    BORDA = "#C9D2E8"

    def _montar_consulta(self, aba):
        # ---- ferramenta de consulta: busca + tipo + status + período
        self.busca = ctk.CTkEntry(aba, height=36, font=fonte(14), border_color=self.BORDA,
                                  placeholder_text="🔍  Buscar por ID, pedido/motivo ou objeto")
        self.busca.pack(fill="x", pady=(0, 6))
        self.busca.bind("<KeyRelease>", lambda _e: self._preencher())

        filtros = ctk.CTkFrame(aba, fg_color="transparent")
        filtros.pack(fill="x", pady=(0, 6))
        menu = dict(height=34, font=fonte(13), dropdown_font=fonte(13), fg_color=AZUL_CLARO,
                    button_color="#CBD6F0", button_hover_color="#B5C4EA", text_color=TEXTO,
                    command=lambda _v: self._preencher())
        self.f_tipo = ctk.CTkOptionMenu(filtros, values=list(self.FILTRO_TIPO), width=132, **menu)
        self.f_tipo.pack(side="left")
        self.f_status = ctk.CTkOptionMenu(filtros, values=list(self.FILTRO_STATUS), width=112, **menu)
        self.f_status.pack(side="left", padx=6)
        self.f_de = ctk.CTkEntry(filtros, width=104, height=34, font=fonte(13), border_color=self.BORDA,
                                 placeholder_text="Data inicial")
        self.f_ate = ctk.CTkEntry(filtros, width=104, height=34, font=fonte(13), border_color=self.BORDA,
                                  placeholder_text="Data final")
        for campo in (self.f_de, self.f_ate):
            campo.pack(side="left", padx=(0, 6))
            campo.bind("<KeyRelease>", lambda _e: self._preencher())
        ctk.CTkButton(filtros, text="Limpar", width=70, height=34, corner_radius=8, fg_color=AZUL_CLARO,
                      hover_color="#CBD6F0", text_color=AZUL_BOTAO, font=fonte(13, True),
                      command=self._limpar_filtros).pack(side="left")

        # ---- parte de baixo antes da tabela (para não ser espremida)
        self.msg_consulta = mensagem(aba)
        self.msg_consulta.pack(side="bottom", fill="x", pady=(4, 0))
        acoes = ctk.CTkFrame(aba, fg_color="transparent")
        acoes.pack(side="bottom", fill="x", pady=(6, 0))
        botao(acoes, "Liberar", self.liberar, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
        botao(acoes, "Dar baixa", self.dar_baixa, height=40, fg_color="#8A1C1C",
              hover_color=VERMELHO).pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.detalhe = ctk.CTkLabel(aba, text="", font=fonte(13), text_color=CINZA, anchor="w",
                                    justify="left", wraplength=560)
        self.detalhe.pack(side="bottom", fill="x", pady=(6, 0), padx=4)

        moldura, self.tabela = criar_tabela(aba, [
            ("id", "ID", 62, "center"), ("tipo", "Tipo", 72, "center"), ("objeto", "Objeto", 110, "w"),
            ("qtd", "Qtd", 45, "center"), ("ref", "Pedido/Motivo", 120, "w"), ("data", "Data", 80, "center"),
            ("status", "Status", 70, "center"),
        ], self.app.escala)
        moldura.configure(fg_color=FUNDO)
        moldura.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", lambda _e: self._mostrar_detalhe())
        self.movimentos = []
        self.visiveis = []

    def _limpar_filtros(self):
        self.f_tipo.set("Todos os tipos")
        self.f_status.set("Ativos")
        for campo in (self.busca, self.f_de, self.f_ate):
            campo.delete(0, "end")
        self.focus()  # devolve o texto de dica aos campos
        self._preencher()

    def _ler_data(self, campo):
        """Data digitada no filtro (dd/mm/aaaa ou dd/mm/aa). Borda vermelha se inválida."""
        texto = campo.get().strip()
        campo.configure(border_color=self.BORDA)
        if not texto:
            return None
        for formato in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                pass
        campo.configure(border_color=VERMELHO)
        return None

    def recarregar(self):
        itens = banco.listar_itens()
        self.form_reserva.atualizar(itens)
        self.form_bloqueio.atualizar(itens)
        self.movimentos = banco.listar_movimentos(apenas_ativos=False)
        self._preencher()

    def _passa_no_filtro(self, m, termo, tipo, status, de, ate):
        if termo and termo not in f"{m.id} {m.referencia} {m.objeto}".lower():
            return False
        if tipo and m.tipo != tipo:
            return False
        if status and m.status != status:
            return False
        if de or ate:
            if not hasattr(m.data, "date"):
                return False
            if (de and m.data.date() < de) or (ate and m.data.date() > ate):
                return False
        return True

    def _mostrar_detalhe(self):
        selecao = self.tabela.selection()
        if not selecao:
            n = len(self.visiveis)
            self.detalhe.configure(
                text_color=CINZA,
                text=f"{n} resultado(s). Clique em um item para ver os detalhes.\n"
                     "Liberar = volta para o disponível   •   Dar baixa = sai do estoque")
            return
        m = self.visiveis[int(selecao[0])]
        rotulo = "Pedido" if m.tipo == banco.RESERVA else "Motivo"
        encerrado = f"   |   Encerrado: {banco.data_curta(m.data_fim)}" if m.data_fim else ""
        self.detalhe.configure(
            text_color=TEXTO,
            text=f"{m.id}  •  {m.tipo}  •  {m.objeto}  •  {m.quantidade} un.  •  {m.status}\n"
                 f"{rotulo}: {m.referencia or '—'}   |   Criado: {banco.data_curta(m.data)}{encerrado}")

    def _preencher(self):
        termo = self.busca.get().strip().lower()
        tipo = self.FILTRO_TIPO[self.f_tipo.get()]
        status = self.FILTRO_STATUS[self.f_status.get()]
        de, ate = self._ler_data(self.f_de), self._ler_data(self.f_ate)
        self.visiveis = [m for m in self.movimentos if self._passa_no_filtro(m, termo, tipo, status, de, ate)]
        self.tabela.delete(*self.tabela.get_children())
        for i, m in enumerate(self.visiveis):
            tags = ["par"] if i % 2 else []
            if m.status != banco.ATIVO:
                tags.append("encerrado")
            data = m.data.strftime("%d/%m/%y") if hasattr(m.data, "strftime") else (m.data or "")
            self.tabela.insert("", "end", iid=str(i), tags=tags, values=(
                m.id, m.tipo, m.objeto, m.quantidade, m.referencia, data, m.status))
        self._mostrar_detalhe()

    def _selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            avisar(self.msg_consulta, "Clique em uma reserva ou bloqueio da lista primeiro.", erro=True)
            return None
        return self.visiveis[int(selecao[0])]

    def _executar(self, funcao, movimento):
        try:
            msg = funcao(movimento.id)
        except banco.ErroEstoque as erro:
            return avisar(self.msg_consulta, str(erro), erro=True)
        self.recarregar()
        avisar(self.msg_consulta, msg)

    def liberar(self):
        m = self._selecionado()
        if m:
            self._executar(banco.liberar, m)

    def dar_baixa(self):
        m = self._selecionado()
        if m and messagebox.askyesno(
                "Dar baixa", f"Dar baixa em {m.id}?\n\n{m.quantidade} unidade(s) de '{m.objeto}' "
                             "vão sair do estoque de vez.", parent=self):
            self._executar(banco.dar_baixa, m)


class TelaHistorico(TelaComTitulo):
    """Histórico de movimentações (aba "Movimentações" do Excel), com filtros."""

    titulo = "Movimentações"
    TIPOS = ["Todos os tipos", banco.ENTRADA, banco.SAIDA, banco.IMPORTACAO, banco.RESERVA, banco.BLOQUEIO,
             banco.LIBERACAO, banco.BAIXA, banco.EDICAO, banco.EXCLUSAO]
    LIMITE_LINHAS = 300

    def __init__(self, master, app):
        super().__init__(master, app)

        # ---- filtros
        self.busca = ctk.CTkEntry(self, height=36, font=fonte(14), border_color="#C9D2E8",
                                  placeholder_text="🔍  Buscar por produto ou observação")
        self.busca.pack(fill="x", pady=(0, 6))
        filtros = ctk.CTkFrame(self, fg_color="transparent")
        filtros.pack(fill="x", pady=(0, 8))
        self.f_tipo = ctk.CTkOptionMenu(filtros, values=self.TIPOS, width=150, height=34, font=fonte(13),
                                        dropdown_font=fonte(13), fg_color=AZUL_CLARO, button_color="#CBD6F0",
                                        button_hover_color="#B5C4EA", text_color=TEXTO,
                                        command=lambda _v: self._preencher())
        self.f_tipo.pack(side="left")
        self.f_de = ctk.CTkEntry(filtros, width=110, height=34, font=fonte(13), border_color="#C9D2E8",
                                 placeholder_text="Data inicial")
        self.f_ate = ctk.CTkEntry(filtros, width=110, height=34, font=fonte(13), border_color="#C9D2E8",
                                  placeholder_text="Data final")
        self.f_de.pack(side="left", padx=6)
        self.f_ate.pack(side="left")
        botao_claro(filtros, "Limpar", self._limpar, width=70, height=34).pack(side="left", padx=6)
        for campo in (self.busca, self.f_de, self.f_ate):
            campo.bind("<KeyRelease>", lambda _e: self._preencher())

        # ---- parte de baixo antes da tabela (para não ser espremida)
        self.mensagem.pack(side="bottom", fill="x")
        self.detalhe = ctk.CTkLabel(self, text="", font=fonte(13), text_color=CINZA, anchor="w",
                                    justify="left", wraplength=600)
        self.detalhe.pack(side="bottom", fill="x", pady=(8, 0), padx=4)

        moldura, self.tabela = criar_tabela(self, [
            ("data", "Data", 108, "center"), ("tipo", "Tipo", 82, "center"), ("objeto", "Objeto", 120, "w"),
            ("qtd", "Qtd", 50, "center"), ("saldo", "Saldo", 52, "center"), ("obs", "Observação", 150, "w"),
        ], app.escala)
        moldura.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", lambda _e: self._mostrar_detalhe())

        self.registros = banco.listar_historico()
        self.visiveis = []
        self._preencher()
        if not self.registros:
            self.avisar("Ainda não há movimentações. Elas aparecem aqui conforme você usa o estoque.")

    def _limpar(self):
        self.f_tipo.set("Todos os tipos")
        for campo in (self.busca, self.f_de, self.f_ate):
            campo.delete(0, "end")
        self.focus()
        self._preencher()

    def _preencher(self):
        termo = self.busca.get().strip().lower()
        tipo = None if self.f_tipo.get() == "Todos os tipos" else self.f_tipo.get()
        de, ate = ler_data_campo(self.f_de), ler_data_campo(self.f_ate)

        def passa(r):
            if termo and termo not in f"{r.objeto} {r.observacao}".lower():
                return False
            if tipo and r.tipo != tipo:
                return False
            if de or ate:
                if not hasattr(r.data, "date"):
                    return False
                if (de and r.data.date() < de) or (ate and r.data.date() > ate):
                    return False
            return True

        encontrados = [r for r in self.registros if passa(r)]
        self.total_encontrado = len(encontrados)
        self.visiveis = encontrados[:self.LIMITE_LINHAS]
        self.tabela.delete(*self.tabela.get_children())
        for i, r in enumerate(self.visiveis):
            data = r.data.strftime("%d/%m/%y %H:%M") if hasattr(r.data, "strftime") else (r.data or "")
            self.tabela.insert("", "end", iid=str(i), tags=("par",) if i % 2 else (), values=(
                data, r.tipo, r.objeto, banco.quantidade_com_sinal(r), r.saldo, r.observacao))
        self._mostrar_detalhe()

    def _mostrar_detalhe(self):
        selecao = self.tabela.selection()
        if not selecao:
            n = self.total_encontrado
            extra = f" (mostrando as {self.LIMITE_LINHAS} mais recentes — use os filtros)" \
                if n > self.LIMITE_LINHAS else ""
            self.detalhe.configure(text_color=CINZA, text=f"{n} movimentação(ões){extra}. "
                                                          "Clique em uma linha para ver os detalhes.")
            return
        r = self.visiveis[int(selecao[0])]
        self.detalhe.configure(
            text_color=TEXTO,
            text=f"{banco.data_curta(r.data)}  •  {r.tipo}  •  {r.objeto}  •  {banco.quantidade_com_sinal(r)} un."
                 f"  •  saldo {r.saldo}  •  {banco.moeda(r.valor)}/un.\n{r.observacao or 'Sem observação.'}")


class TelaRelatorios(TelaComTitulo):
    titulo = "Relatórios"

    def __init__(self, master, app):
        super().__init__(master, app)
        abas = self.abas = criar_abas(self)
        self._montar_resumo(abas.add("Resumo"))
        self._montar_pdf(abas.add("Relatório em PDF"))

    # ---------------------------------------------------- aba "Resumo"
    def _montar_resumo(self, aba):
        itens = banco.listar_itens()
        ativos = banco.listar_movimentos()
        n_reservas = sum(1 for m in ativos if m.tipo == banco.RESERVA)
        n_bloqueios = len(ativos) - n_reservas
        if itens:
            maior = max(itens, key=lambda i: i.valor_total)
            maior_texto = (maior.objeto, banco.moeda(maior.valor_total))
        else:
            maior_texto = ("—", "")

        grade = ctk.CTkFrame(aba, fg_color="transparent")
        grade.pack(fill="x")
        grade.columnconfigure((0, 1, 2), weight=1, uniform="col")
        cartoes = [
            ("Valor total do estoque", banco.moeda(sum(i.valor_total for i in itens)), ""),
            ("Produtos cadastrados", str(len(itens)), ""),
            ("Unidades em estoque", str(sum(i.quantidade for i in itens)),
             f"{sum(i.disponivel for i in itens)} disponíveis"),
            ("Unidades reservadas", str(sum(i.reservado for i in itens)), f"{n_reservas} reserva(s) ativa(s)"),
            ("Unidades bloqueadas", str(sum(i.bloqueado for i in itens)), f"{n_bloqueios} bloqueio(s) ativo(s)"),
            ("Item de maior valor", *maior_texto),
        ]
        for i, (titulo, valor, detalhe) in enumerate(cartoes):
            self.cartao(grade, titulo, valor, detalhe).grid(row=i // 3, column=i % 3, sticky="nsew",
                                                           padx=4, pady=4)

        ctk.CTkLabel(aba, text=f"Estoque baixo (até {ESTOQUE_BAIXO} unidades disponíveis)",
                     font=fonte(16, True), text_color=TEXTO, anchor="w").pack(fill="x", pady=(10, 4), padx=5)
        lista = ctk.CTkScrollableFrame(aba, fg_color=FUNDO, corner_radius=12)
        lista.pack(fill="both", expand=True, padx=4)
        baixos = sorted((i for i in itens if i.disponivel <= ESTOQUE_BAIXO), key=lambda i: i.disponivel)
        if not baixos:
            ctk.CTkLabel(lista, text="Nenhum item com estoque baixo. 👍", font=fonte(15),
                         text_color=CINZA).pack(pady=14)
        for item in baixos:
            linha = ctk.CTkFrame(lista, fg_color="transparent")
            linha.pack(fill="x", pady=3, padx=6)
            ctk.CTkLabel(linha, text=item.objeto, font=fonte(15), text_color=TEXTO, anchor="w").pack(side="left")
            ctk.CTkLabel(linha, text=f"{item.disponivel} disp.", font=fonte(15, True),
                         text_color=VERMELHO if item.disponivel <= 2 else LARANJA).pack(side="right")

    @staticmethod
    def cartao(master, titulo, valor, detalhe):
        c = ctk.CTkFrame(master, fg_color=FUNDO, corner_radius=14)
        ctk.CTkLabel(c, text=titulo, font=fonte(13), text_color=CINZA, anchor="w").pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(c, text=valor, font=fonte(20, True), text_color=AZUL_BOTAO, anchor="w",
                     wraplength=165, justify="left").pack(fill="x", padx=14)
        ctk.CTkLabel(c, text=detalhe, font=fonte(12), text_color=CINZA, anchor="w").pack(fill="x", padx=14, pady=(0, 8))
        return c

    # ---------------------------------------------------- aba "Relatório em PDF"
    # O usuário escolhe UM produto (com busca, pois podem existir milhares) e o
    # período; o PDF sai com gráfico de entradas × saídas e a tabela detalhada.
    LIMITE_BUSCA = 50

    def _montar_pdf(self, aba):
        def rotulo(texto, pady=(8, 2)):
            r = ctk.CTkLabel(aba, text=texto, font=fonte(14, True), text_color=TEXTO, anchor="w")
            r.pack(fill="x", padx=4, pady=pady)
            return r

        # ---- produto (busca + lista curta de resultados)
        self.escolhido = rotulo("1. Produto  —  nenhum escolhido", pady=(0, 2))
        self.busca_produto = ctk.CTkEntry(aba, height=34, font=fonte(14), border_color="#C9D2E8",
                                          placeholder_text="🔍  Digite parte do nome do produto")
        self.busca_produto.pack(fill="x", padx=4)
        self.busca_produto.bind("<KeyRelease>", lambda _e: self._filtrar_produtos())
        moldura, self.lista_produtos = criar_tabela(aba, [("nome", "Produtos encontrados", 400, "w")], self.app.escala)
        self.lista_produtos.configure(height=3)
        moldura.configure(fg_color=FUNDO)
        moldura.pack(fill="x", padx=4, pady=(4, 0))
        self.lista_produtos.bind("<<TreeviewSelect>>", lambda _e: self._escolher_produto())

        # ---- período
        rotulo("2. Período")
        linha = ctk.CTkFrame(aba, fg_color="transparent")
        linha.pack(fill="x", padx=4)
        menu = dict(height=34, font=fonte(13), dropdown_font=fonte(13), fg_color=AZUL_CLARO,
                    button_color="#CBD6F0", button_hover_color="#B5C4EA", text_color=TEXTO)
        self.periodo = ctk.CTkOptionMenu(linha, values=banco.PERIODOS, width=160,
                                         command=lambda _v: self._aplicar_periodo(), **menu)
        self.periodo.set("Últimos 30 dias")
        self.periodo.pack(side="left")
        self.rel_de = ctk.CTkEntry(linha, width=110, height=34, font=fonte(13), border_color="#C9D2E8",
                                   placeholder_text="Data inicial")
        self.rel_ate = ctk.CTkEntry(linha, width=110, height=34, font=fonte(13), border_color="#C9D2E8",
                                    placeholder_text="Data final")
        self.rel_de.pack(side="left", padx=6)
        self.rel_ate.pack(side="left")
        for campo in (self.rel_de, self.rel_ate):  # digitou a data → vira "Personalizado"
            campo.bind("<KeyRelease>", lambda _e: self.periodo.set("Personalizado"))
        ctk.CTkLabel(linha, text="Agrupar:", font=fonte(13), text_color=CINZA).pack(side="left", padx=(12, 4))
        self.agrupamento = ctk.CTkOptionMenu(linha, values=list(banco.AGRUPAMENTOS), width=120, **menu)
        self.agrupamento.pack(side="left")

        # ---- gerar
        rotulo("3. Gerar")
        final = ctk.CTkFrame(aba, fg_color="transparent")
        final.pack(fill="x", padx=4)
        self.gerado_por = ctk.CTkEntry(final, height=40, font=fonte(13), border_color="#C9D2E8",
                                       placeholder_text="Gerado por (opcional)")
        self.gerado_por.pack(side="left", fill="x", expand=True)
        botao(final, "📄  Gerar PDF", self.gerar_pdf, width=170, height=40).pack(side="left", padx=(8, 0))
        self.msg_pdf = mensagem(aba)
        self.msg_pdf.pack(fill="x", padx=4, pady=(6, 0))

        self.nomes = banco.nomes_produtos()
        self.produto = None
        self._aplicar_periodo()
        self._filtrar_produtos()

    def _filtrar_produtos(self):
        termo = self.busca_produto.get().strip().lower()
        achados = [n for n in self.nomes if termo in n.lower()] if termo else list(self.nomes)
        if termo:  # quem começa com o termo aparece primeiro
            achados.sort(key=lambda n: (not n.lower().startswith(termo), n.lower()))
        self.achados = achados[:self.LIMITE_BUSCA]
        self.lista_produtos.delete(*self.lista_produtos.get_children())
        for i, nome in enumerate(self.achados):
            self.lista_produtos.insert("", "end", iid=str(i), values=(nome,), tags=("par",) if i % 2 else ())
        if len(achados) > self.LIMITE_BUSCA:
            self.lista_produtos.heading("nome", text=f"Produtos encontrados ({len(achados)}) — refine a busca")
        else:
            self.lista_produtos.heading("nome", text=f"Produtos encontrados ({len(achados)})")
        if len(self.achados) == 1:  # só um resultado: já escolhe
            self.lista_produtos.selection_set("0")

    def _escolher_produto(self):
        selecao = self.lista_produtos.selection()
        if selecao:
            self.produto = self.achados[int(selecao[0])]
            self.escolhido.configure(text=f"1. Produto  —  escolhido: {self.produto}", text_color=AZUL_BOTAO)

    def _aplicar_periodo(self):
        datas = banco.periodo_do_atalho(self.periodo.get())
        if datas:
            for campo, data in zip((self.rel_de, self.rel_ate), datas):
                campo.delete(0, "end")
                campo.insert(0, data.strftime("%d/%m/%Y"))
                campo.configure(border_color="#C9D2E8")

    def gerar_pdf(self):
        if not self.produto:
            return avisar(self.msg_pdf, "Escolha um produto na lista (passo 1).", erro=True)
        de, ate = ler_data_campo(self.rel_de), ler_data_campo(self.rel_ate)
        if not de or not ate:
            return avisar(self.msg_pdf, "Preencha as datas no formato dd/mm/aaaa (passo 2).", erro=True)
        nome_arquivo = "".join(c if c.isalnum() else "_" for c in self.produto).strip("_")
        caminho = filedialog.asksaveasfilename(
            parent=self, title="Salvar relatório", defaultextension=".pdf",
            initialfile=f"movimentacao_{nome_arquivo}_{de:%Y-%m-%d}_a_{ate:%Y-%m-%d}.pdf",
            filetypes=[("PDF", "*.pdf")])
        if not caminho:
            return
        avisar(self.msg_pdf, "Gerando o relatório…")
        self.update_idletasks()
        try:
            banco.gerar_pdf_movimentacao(caminho, self.produto, de, ate,
                                         banco.AGRUPAMENTOS[self.agrupamento.get()], self.gerado_por.get().strip())
        except banco.ErroEstoque as erro:
            return avisar(self.msg_pdf, str(erro), erro=True)
        avisar(self.msg_pdf, f"Relatório salvo: {Path(caminho).name} (pasta {Path(caminho).parent.name})")
        try:
            os.startfile(caminho)  # abre o PDF no leitor padrão do Windows
        except OSError:
            pass


class TelaRequisicoes(TelaComTitulo):
    """Pedidos de produtos. São baixados sozinhos quando o produto dá entrada."""

    titulo = "Requisições"
    FILTRO = {"Abertas (aguardando)": (banco.REQ_ABERTA, banco.REQ_PARCIAL), "Atendidas": (banco.REQ_ATENDIDA,),
              "Canceladas": (banco.REQ_CANCELADA,), "Todas": None}

    def __init__(self, master, app):
        super().__init__(master, app)
        abas = self.abas = criar_abas(self)
        self._montar_nova(abas.add("Nova requisição"))
        self._montar_consulta(abas.add("Consultar"))
        self.recarregar()
        self.after(100, self.campos["objeto"].focus)

    # ---------------------------------------------------- aba "Nova requisição"
    def _montar_nova(self, aba):
        self.campos = {}
        for chave, rotulo, dica in (("objeto", "Produto", "Pode ser um produto que ainda não existe no estoque"),
                                    ("qtd", "Quantidade", "Ex.: 50"),
                                    ("solicitante", "Solicitante / setor (opcional)", "Ex.: Ana — Financeiro"),
                                    ("obs", "Observação (opcional)", "Ex.: urgente, para o evento de sexta")):
            ctk.CTkLabel(aba, text=rotulo, font=fonte(14, True), text_color=TEXTO, anchor="w"
                         ).pack(fill="x", padx=10, pady=(5, 2))
            campo = ctk.CTkEntry(aba, height=36, font=fonte(15), placeholder_text=dica, border_color="#C9D2E8")
            campo.pack(fill="x", padx=10)
            campo.bind("<Return>", lambda _e: self.registrar())
            self.campos[chave] = campo
            if chave == "objeto":
                self.info_estoque = ctk.CTkLabel(aba, text="", font=fonte(12), text_color=CINZA, anchor="w",
                                                 height=16)
                self.info_estoque.pack(fill="x", padx=12)
                campo.bind("<KeyRelease>", lambda _e: self._mostrar_estoque())
        botao(aba, "Registrar requisição", self.registrar, height=42).pack(fill="x", padx=10, pady=(10, 4))
        self.msg_nova = mensagem(aba)
        self.msg_nova.pack(fill="x", padx=10)

    def _mostrar_estoque(self):
        item = self.itens.get(self.campos["objeto"].get().strip().lower())
        self.info_estoque.configure(
            text=f"Em estoque: {item.quantidade} (disponível {item.disponivel})" if item
            else ("Produto novo: será criado no estoque quando der entrada." if self.campos["objeto"].get().strip()
                  else ""))

    def registrar(self):
        try:
            quantidade = banco.converter_numero(self.campos["qtd"].get(), inteiro=True, nome="quantidade")
            id_req, _ = banco.criar_requisicao(self.campos["objeto"].get(), quantidade,
                                               self.campos["solicitante"].get(), self.campos["obs"].get())
        except banco.ErroEstoque as erro:
            return avisar(self.msg_nova, str(erro), erro=True)
        msg = f"Requisição {id_req} registrada. Baixa automática quando o produto der entrada."
        for campo in self.campos.values():
            campo.delete(0, "end")
        self.info_estoque.configure(text="")
        self.campos["objeto"].focus()
        self.recarregar()
        avisar(self.msg_nova, msg)

    # ---------------------------------------------------- aba "Consultar"
    def _montar_consulta(self, aba):
        topo = ctk.CTkFrame(aba, fg_color="transparent")
        topo.pack(fill="x", pady=(0, 6))
        self.busca = ctk.CTkEntry(topo, height=34, font=fonte(14), border_color="#C9D2E8",
                                  placeholder_text="🔍  Buscar por ID, produto, solicitante ou observação")
        self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<KeyRelease>", lambda _e: self._preencher())
        self.f_status = ctk.CTkOptionMenu(topo, values=list(self.FILTRO), width=170, height=34, font=fonte(13),
                                          dropdown_font=fonte(13), fg_color=AZUL_CLARO, button_color="#CBD6F0",
                                          button_hover_color="#B5C4EA", text_color=TEXTO,
                                          command=lambda _v: self._preencher())
        self.f_status.pack(side="left", padx=(6, 0))

        # parte de baixo antes da tabela (para não ser espremida)
        self.msg_consulta = mensagem(aba)
        self.msg_consulta.pack(side="bottom", fill="x", pady=(4, 0))
        acoes = ctk.CTkFrame(aba, fg_color="transparent")
        acoes.pack(side="bottom", fill="x", pady=(6, 0))
        self.motivo = ctk.CTkEntry(acoes, height=38, font=fonte(13), border_color="#C9D2E8",
                                   placeholder_text="Motivo do cancelamento (opcional)")
        self.motivo.pack(side="left", fill="x", expand=True)
        botao(acoes, "Cancelar requisição", self.cancelar, width=180, height=38, fg_color="#8A1C1C",
              hover_color=VERMELHO).pack(side="left", padx=(8, 0))
        self.detalhe = ctk.CTkLabel(aba, text="", font=fonte(13), text_color=CINZA, anchor="w",
                                    justify="left", wraplength=560)
        self.detalhe.pack(side="bottom", fill="x", pady=(6, 0), padx=4)

        moldura, self.tabela = criar_tabela(aba, [
            ("id", "ID", 64, "center"), ("objeto", "Produto", 120, "w"), ("qtd", "Pedido", 64, "center"),
            ("chegou", "Chegou", 66, "center"), ("solic", "Solicitante", 86, "w"),
            ("data", "Data", 72, "center"), ("status", "Status", 74, "center"),
        ], self.app.escala)
        moldura.configure(fg_color=FUNDO)
        moldura.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", lambda _e: self._mostrar_detalhe())
        self.requisicoes, self.visiveis = [], []

    def recarregar(self):
        self.itens = {i.objeto.lower(): i for i in banco.listar_itens()}
        self.requisicoes = banco.listar_requisicoes()
        self._preencher()

    def _preencher(self):
        termo = self.busca.get().strip().lower()
        status = self.FILTRO[self.f_status.get()]
        self.visiveis = [r for r in self.requisicoes
                         if (status is None or r.status in status)
                         and (not termo or termo in f"{r.id} {r.objeto} {r.solicitante} {r.observacao}".lower())]
        self.tabela.delete(*self.tabela.get_children())
        for i, r in enumerate(self.visiveis):
            tags = ["par"] if i % 2 else []
            if r.status in (banco.REQ_ATENDIDA, banco.REQ_CANCELADA):
                tags.append("encerrado")
            data = r.data.strftime("%d/%m/%y") if hasattr(r.data, "strftime") else (r.data or "")
            self.tabela.insert("", "end", iid=str(i), tags=tags, values=(
                r.id, r.objeto, r.quantidade, r.atendida, r.solicitante, data, r.status))
        self._mostrar_detalhe()

    def _mostrar_detalhe(self):
        selecao = self.tabela.selection()
        if not selecao:
            self.detalhe.configure(text_color=CINZA, text=f"{len(self.visiveis)} requisição(ões). "
                                   "Elas são baixadas sozinhas quando o produto dá entrada no estoque.")
            return
        r = self.visiveis[int(selecao[0])]
        fim = f"   |   {r.status} em {banco.data_curta(r.data_atendimento)}" if r.data_atendimento else ""
        self.detalhe.configure(
            text_color=TEXTO,
            text=f"{r.id}  •  {r.objeto}  •  pedido {r.quantidade}, chegou {r.atendida}, falta {r.falta}  •  {r.status}\n"
                 f"Solicitante: {r.solicitante or '—'}   |   Pedido em {banco.data_curta(r.data)}{fim}\n"
                 f"Obs.: {r.observacao or '—'}")

    def cancelar(self):
        selecao = self.tabela.selection()
        if not selecao:
            return avisar(self.msg_consulta, "Clique em uma requisição da lista primeiro.", erro=True)
        r = self.visiveis[int(selecao[0])]
        if not messagebox.askyesno("Cancelar requisição", f"Cancelar a requisição {r.id} "
                                   f"({r.quantidade} de '{r.objeto}')?", parent=self):
            return
        try:
            msg = banco.cancelar_requisicao(r.id, self.motivo.get())
        except banco.ErroEstoque as erro:
            return avisar(self.msg_consulta, str(erro), erro=True)
        self.motivo.delete(0, "end")
        self.recarregar()
        avisar(self.msg_consulta, msg)


# ---------------------------------------------------------------- janela principal

class App(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=FUNDO)
        ctk.set_appearance_mode("light")
        self.title("Controle de Estoque")
        self.geometry("680x700")
        self.minsize(620, 640)
        self.escala = ctk.ScalingTracker.get_window_scaling(self)
        estilo_tabelas(self.escala)

        Cabecalho(self, self.escala).pack(fill="x")
        self.area = ctk.CTkFrame(self, fg_color="transparent")
        self.area.pack(fill="both", expand=True, padx=30, pady=20)
        self.ir_inicio()

    def mostrar(self, tela):
        for widget in self.area.winfo_children():
            widget.destroy()
        try:
            tela(self.area, self).pack(fill="both", expand=True)
        except banco.ErroEstoque as erro:
            messagebox.showerror("Erro", str(erro))
            if tela is not TelaInicio:
                self.ir_inicio()

    def ir_inicio(self):
        self.mostrar(TelaInicio)


def main():
    try:
        banco.criar_banco()
    except banco.ErroEstoque as erro:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("Controle de Estoque", str(erro))
        return
    App().mainloop()


if __name__ == "__main__":
    main()
