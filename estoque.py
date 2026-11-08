"""
CONTROLE DE ESTOQUE — MENU NO TERMINAL
======================================
Rode com:  python estoque.py
(Para a janela com botões, rode:  python tela.py)

Este arquivo é só a "conversa" com o usuário no terminal: mostra o menu, pede
os dados e exibe o resultado. Toda a lógica (gravar no Excel, calcular saldo,
reservar...) fica no pacote "banco/". Isso permite que o menu e a janela usem
exatamente as mesmas regras.

Estrutura do projeto:

  estoque.py         ← você está aqui (menu do terminal)
  tela.py            ← janela gráfica
  estoque.xlsx       ← o banco de dados (abas Estoque, Reservas e Bloqueios,
                       Movimentações e Requisições)
  tests/             ← testes automatizados (python -m pytest -v)
  banco/             ← a lógica, dividida por assunto:
      config.py        nome do arquivo, colunas, status       (bom para começar)
      modelos.py       formato dos dados (Item, Movimento)
      utilidades.py    formatar R$/datas, converter e validar números
      planilha.py      abrir/salvar o Excel (gravação atômica)
      historico.py     registrar e consultar movimentações
      produtos.py      adicionar, retirar, editar, excluir, consultar
      reservas.py      reservar, bloquear, liberar, dar baixa
      requisicoes.py   pedidos de produtos (baixa automática na entrada)
      importacao.py    importar lista .xlsx/.csv
      relatorio.py     relatório de movimentação em PDF (com gráficos)

📚 Sugestão de estudo: leia este arquivo, depois banco/config.py,
   banco/modelos.py, banco/produtos.py e, por fim, banco/reservas.py.
"""
import banco
from banco import ErroEstoque, moeda


# ================================================================== mostrar tabelas

def listar():
    """Mostra a tabela de produtos com total, reservado, bloqueado e disponível."""
    itens = banco.listar_itens()
    if not itens:
        print("O estoque está vazio.")
        return
    # f"{texto:<24}" alinha à esquerda em 24 espaços; ":>7" alinha à direita em 7
    print(f"\n{'OBJETO':<24}{'TOTAL':>7}{'RESERV':>8}{'BLOQ':>6}{'DISP':>6}{'VALOR':>13}{'VALOR TOTAL':>15}")
    print("-" * 79)
    for i in itens:
        print(f"{i.objeto:<24}{i.quantidade:>7}{i.reservado:>8}{i.bloqueado:>6}{i.disponivel:>6}"
              f"{moeda(i.valor):>13}{moeda(i.valor_total):>15}")
    print("-" * 79)
    print(f"{'VALOR TOTAL DO ESTOQUE':<64}{moeda(sum(i.valor_total for i in itens)):>15}")


def consultar(objeto):
    """Mostra a situação atual de UM produto (total, reservado, bloqueado, disponível)."""
    i = banco.consultar(objeto)  # produto inexistente → ErroEstoque (mostrado pelo menu)
    print(f"\n{i.objeto}")
    print(f"  Total:      {i.quantidade}")
    print(f"  Reservado:  {i.reservado}")
    print(f"  Bloqueado:  {i.bloqueado}")
    print(f"  Disponível: {i.disponivel}")
    print(f"  Valor unitário: {moeda(i.valor)}   Valor total: {moeda(i.valor_total)}")


def listar_ativos():
    """Mostra as reservas e bloqueios que ainda estão ativos."""
    movimentos = banco.listar_movimentos()
    if not movimentos:
        print("Nenhuma reserva ou bloqueio ativo.")
        return
    print(f"\n{'ID':<7}{'TIPO':<10}{'OBJETO':<24}{'QTD':>5}  {'PEDIDO/MOTIVO':<20}{'DATA':<16}")
    print("-" * 82)
    for m in movimentos:
        print(f"{m.id:<7}{m.tipo:<10}{m.objeto:<24}{m.quantidade:>5}  "
              f"{m.referencia:<20}{banco.data_curta(m.data):<16}")


def listar_historico(quantos=30):
    """Mostra as últimas movimentações (as mais recentes primeiro)."""
    registros = banco.listar_historico()[:quantos]
    if not registros:
        print("Ainda não há movimentações.")
        return
    print(f"\n{'DATA':<17}{'TIPO':<12}{'OBJETO':<22}{'QTD':>6}{'SALDO':>7}  OBSERVAÇÃO")
    print("-" * 90)
    for r in registros:
        print(f"{banco.data_curta(r.data):<17}{r.tipo:<12}{r.objeto[:21]:<22}"
              f"{banco.quantidade_com_sinal(r):>6}{r.saldo:>7}  {r.observacao}")


def listar_requisicoes():
    """Mostra as requisições que ainda esperam produto (abertas e parciais)."""
    requisicoes = banco.listar_requisicoes(apenas_abertas=True)
    if not requisicoes:
        print("Nenhuma requisição aberta.")
        return
    print(f"\n{'ID':<8}{'PRODUTO':<24}{'PEDIDO':>7}{'CHEGOU':>8}  {'SOLICITANTE':<18}{'STATUS':<9}")
    print("-" * 76)
    for r in requisicoes:
        print(f"{r.id:<8}{r.objeto[:23]:<24}{r.quantidade:>7}{r.atendida:>8}  {r.solicitante[:17]:<18}{r.status:<9}")


# ================================================================== perguntar ao usuário

def pedir_texto(pergunta, obrigatorio=True):
    """Pergunta até receber um texto (ou aceita vazio se obrigatorio=False)."""
    while True:
        texto = input(pergunta).strip()
        if texto or not obrigatorio:
            return texto
        print("Não pode ficar vazio.")


def pedir_numero(pergunta, inteiro=False, nome="valor"):
    """Pergunta até receber um número válido (maior que zero)."""
    while True:
        try:
            return banco.converter_numero(input(pergunta), inteiro, nome)
        except ErroEstoque as erro:
            print(erro)  # mostra o motivo e pergunta de novo


# ================================================================== menu principal

def menu():
    banco.criar_banco()  # cria a planilha se ainda não existir
    while True:          # repete até o usuário escolher "0"
        print("\n===== ESTOQUE =====")
        print("1 - Inserir objeto")
        print("2 - Retirar objeto")
        print("3 - Consultar produto / ver estoque")
        print("4 - Reservar")
        print("5 - Bloquear")
        print("6 - Ver reservas e bloqueios ativos")
        print("7 - Liberar reserva/bloqueio (volta para o disponível)")
        print("8 - Dar baixa em reserva/bloqueio (sai do estoque)")
        print("9 - Ver histórico de movimentações")
        print("10 - Editar produto (nome, quantidade, valor)")
        print("11 - Excluir produto")
        print("12 - Nova requisição (pedido de produto)")
        print("13 - Ver requisições abertas")
        print("14 - Cancelar requisição")
        print("0 - Sair")
        opcao = input("Escolha: ").strip()

        # Qualquer ErroEstoque (ex.: "Só tem 3 unidades") cai no "except" lá
        # embaixo: a mensagem é mostrada e o menu continua funcionando.
        try:
            if opcao == "1":
                objeto = pedir_texto("Objeto: ")
                quantidade = pedir_numero("Quantidade: ", True, "quantidade")
                valor = pedir_numero("Valor unitário (R$): ")
                print(banco.inserir(objeto, quantidade, valor))
            elif opcao == "2":
                objeto = pedir_texto("Objeto: ")
                quantidade = pedir_numero("Quantidade a retirar: ", True, "quantidade")
                obs = pedir_texto("Observação (opcional): ", False)
                print(banco.retirar(objeto, quantidade, obs))
            elif opcao == "3":
                objeto = pedir_texto("Produto (Enter = ver todos): ", False)
                if objeto:
                    consultar(objeto)
                else:
                    listar()
            elif opcao in ("4", "5"):
                objeto = pedir_texto("Objeto: ")
                quantidade = pedir_numero("Quantidade: ", True, "quantidade")
                if opcao == "4":
                    pedido = pedir_texto("Pedido/solicitação (opcional): ", False)
                    _, msg = banco.reservar(objeto, quantidade, pedido)  # devolve (id, mensagem)
                else:
                    motivo = pedir_texto("Motivo (opcional): ", False)
                    _, msg = banco.bloquear(objeto, quantidade, motivo)
                print(msg)
            elif opcao == "6":
                listar_ativos()
            elif opcao == "7":
                print(banco.liberar(pedir_texto("ID (ex.: R0001): ")))
            elif opcao == "8":
                print(banco.dar_baixa(pedir_texto("ID (ex.: R0001): ")))
            elif opcao == "9":
                listar_historico()
            elif opcao == "10":
                objeto = pedir_texto("Produto a editar: ")
                print("(deixe em branco o que não quer mudar)")
                nome = pedir_texto("Novo nome: ", False) or None
                qtd = pedir_texto("Nova quantidade total: ", False)
                valor = pedir_texto("Novo valor unitário: ", False)
                obs = pedir_texto("Observação (opcional): ", False)
                print(banco.editar(
                    objeto, nome,
                    banco.converter_numero(qtd, True, "quantidade") if qtd else None,
                    banco.converter_numero(valor) if valor else None,
                    obs))
            elif opcao == "11":
                objeto = pedir_texto("Produto a excluir: ")
                if input(f"Confirma excluir '{objeto}'? (s/n): ").strip().lower() == "s":
                    print(banco.excluir(objeto, pedir_texto("Motivo (opcional): ", False)))
            elif opcao == "12":
                objeto = pedir_texto("Produto: ")
                quantidade = pedir_numero("Quantidade: ", True, "quantidade")
                solicitante = pedir_texto("Solicitante/setor (opcional): ", False)
                obs = pedir_texto("Observação (opcional): ", False)
                print(banco.criar_requisicao(objeto, quantidade, solicitante, obs)[1])
            elif opcao == "13":
                listar_requisicoes()
            elif opcao == "14":
                print(banco.cancelar_requisicao(pedir_texto("ID (ex.: RQ0001): "),
                                                pedir_texto("Motivo (opcional): ", False)))
            elif opcao == "0":
                print("Até mais!")
                break
            else:
                print("Opção inválida.")
        except ErroEstoque as erro:
            print(f"ERRO: {erro}")


# Este bloco só roda quando o arquivo é executado diretamente (python estoque.py),
# e não quando outro arquivo faz "import estoque".
if __name__ == "__main__":
    try:
        menu()
    except ErroEstoque as erro:
        print(f"ERRO: {erro}")
    except (KeyboardInterrupt, EOFError):  # Ctrl+C ou fim da entrada
        print("\nAté mais!")
