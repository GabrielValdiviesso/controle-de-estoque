"""
PACOTE "banco" — tudo que lê e grava o estoque.xlsx
====================================================
Um "pacote" é só uma pasta com arquivos .py e este __init__.py. Ele permite
escrever `import banco` e usar `banco.inserir(...)`, `banco.reservar(...)` etc.,
sem precisar saber em qual arquivo cada função está.

Mapa dos módulos (do mais simples para o mais completo):

  config.py      Nome do arquivo, abas, colunas, tipos e status.     ← comece aqui
  modelos.py     Formato dos dados: Item, Movimento, ErroEstoque.
  utilidades.py  Formatar R$ e datas; converter o que foi digitado.
  planilha.py    Criar/abrir/salvar o Excel + ferramentas de busca e saldo.
  historico.py   Registrar e consultar o histórico de movimentações.
  produtos.py    Adicionar, retirar, editar, excluir e listar produtos.
  reservas.py    Reservar, bloquear, liberar, dar baixa e consultar.
  requisicoes.py Pedidos de produtos, com baixa automática na entrada.
  importacao.py  Importar lista de produtos de .xlsx ou .csv.
  relatorio.py   Relatório de movimentação de um produto em PDF (com gráficos).

Quem usa este pacote:
  estoque.py  (menu no terminal)   e   tela.py  (janela gráfica)
"""
from . import config
from .config import (ATIVO, BAIXA, BLOQUEIO, EDICAO, ENTRADA, EXCLUSAO, IMPORTACAO, LIBERACAO, LIBERADO,
                     REQ_ABERTA, REQ_ATENDIDA, REQ_CANCELADA, REQ_PARCIAL, RESERVA, SAIDA)
from .historico import TIPOS_ENTRADA, TIPOS_SAIDA, listar_historico, quantidade_com_sinal
from .importacao import criar_modelo, inserir_lista, ler_lista
from .modelos import ErroEstoque, Item, Movimento, Registro, Requisicao
from .planilha import criar_banco
from .produtos import consultar, editar, excluir, inserir, listar_itens, retirar
from .relatorio import AGRUPAMENTOS, PERIODOS, gerar_pdf_movimentacao, nomes_produtos, periodo_do_atalho
from .requisicoes import cancelar_requisicao, criar_requisicao, listar_requisicoes
from .reservas import bloquear, dar_baixa, liberar, listar_movimentos, reservar
from .utilidades import converter_numero, data_curta, moeda
