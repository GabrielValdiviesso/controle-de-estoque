"""
CONFIGURAÇÕES DO BANCO DE DADOS
===============================
Aqui ficam os "valores fixos" do sistema: onde a planilha fica salva, o nome
das abas, o nome das colunas e os textos usados como tipo e status.

✏️  Quer mudar algo? Este é o arquivo mais seguro para começar.
    Exemplo: trocar o nome do arquivo de "estoque.xlsx" para "meu_estoque.xlsx".

⚠️  Cuidado: se você mudar nomes de colunas, abas ou status DEPOIS que a planilha
    já existe, o programa deixa de reconhecer a planilha antiga (ou os registros
    antigos). Nesse caso, ajuste a planilha no Excel para usar os nomes novos.
"""
import sys
from pathlib import Path

# ------------------------------------------------------------------ onde fica a planilha
# Quando o programa vira .exe (PyInstaller), "sys.frozen" existe e a planilha fica
# ao lado do .exe. Rodando com "python ...", fica na pasta do projeto — que é a
# pasta ACIMA desta pasta "banco" (por isso o .parent.parent).
if getattr(sys, "frozen", False):
    PASTA = Path(sys.executable).parent
else:
    PASTA = Path(__file__).resolve().parent.parent

ARQUIVO = PASTA / "estoque.xlsx"

# ------------------------------------------------------------------ aba 1: Estoque
# Uma linha por produto. "Quantidade" é o total FÍSICO (inclui o que está
# reservado ou bloqueado). "Valor" é o valor unitário em reais.
ABA_ESTOQUE = "Estoque"
COLUNAS = ["Objeto", "Quantidade", "Valor"]
LARGURAS = [30, 14, 14]  # largura das colunas no Excel (só aparência)

# ------------------------------------------------------------------ aba 2: Reservas e Bloqueios
# Histórico de reservas e bloqueios. Nada é apagado daqui: quando algo é
# liberado ou recebe baixa, só muda o "Status" e a "Data Fim" é preenchida.
ABA_MOV = "Reservas e Bloqueios"
COLUNAS_MOV = ["ID", "Tipo", "Objeto", "Quantidade", "Pedido/Motivo", "Data", "Status", "Data Fim"]
LARGURAS_MOV = [10, 12, 30, 12, 30, 18, 12, 18]

# Tipos de registro (a 1ª letra vira o prefixo do ID: R0001, B0001)
RESERVA = "Reserva"
BLOQUEIO = "Bloqueio"

# Situação de cada reserva/bloqueio
ATIVO = "Ativo"        # está segurando unidades (elas não estão disponíveis)
LIBERADO = "Liberado"  # foi cancelado: as unidades voltaram para o disponível
BAIXA = "Baixa"        # foi efetivado: as unidades saíram do estoque

# ------------------------------------------------------------------ aba 3: Movimentações
# Histórico de TUDO que acontece no estoque (uma linha por operação).
# Nunca é alterado nem apagado pelo programa — serve de auditoria.
#   Quantidade = quanto foi movimentado (na Edição: a diferença, ex.: -3)
#   Saldo      = total físico do produto DEPOIS da operação
ABA_HIST = "Movimentações"
COLUNAS_HIST = ["Data", "Tipo", "Objeto", "Quantidade", "Saldo", "Valor", "Observação"]
LARGURAS_HIST = [18, 13, 30, 12, 10, 12, 50]

# Tipos de movimentação (Reserva/Bloqueio/Baixa usam os nomes lá de cima)
ENTRADA = "Entrada"        # adicionou unidades (formulário)
IMPORTACAO = "Importação"  # adicionou unidades (lista .xlsx/.csv)
SAIDA = "Saída"            # retirou unidades
LIBERACAO = "Liberação"    # cancelou uma reserva/bloqueio
EDICAO = "Edição"          # mudou nome, quantidade ou valor do produto
EXCLUSAO = "Exclusão"      # apagou o produto

# ------------------------------------------------------------------ aba 4: Requisições
# Pedidos de compra/reposição de produtos. Quando o produto requisitado dá
# ENTRADA no estoque (formulário ou importação), a requisição é atendida sozinha
# (a mais antiga primeiro). Se chegar menos do que o pedido, fica "Parcial".
ABA_REQ = "Requisições"
COLUNAS_REQ = ["ID", "Objeto", "Quantidade", "Atendida", "Solicitante", "Observação",
               "Data", "Status", "Data Atendimento"]
LARGURAS_REQ = [10, 30, 12, 12, 22, 35, 18, 12, 18]

REQ_ABERTA = "Aberta"        # nada chegou ainda
REQ_PARCIAL = "Parcial"      # chegou parte do pedido
REQ_ATENDIDA = "Atendida"    # chegou tudo (baixa automática)
REQ_CANCELADA = "Cancelada"  # cancelada manualmente

# Como as datas aparecem quando você abre a planilha no Excel
FORMATO_DATA = "DD/MM/YYYY HH:MM"
