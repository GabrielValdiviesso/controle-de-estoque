"""
UTILIDADES
==========
Pequenas funções de formatação e conversão, usadas pelo menu e pela janela.
Não mexem na planilha.
"""
from datetime import datetime

from .modelos import ErroEstoque


def moeda(numero):
    """1234.5 → "R$ 1.234,50" (formato brasileiro).

    Truque: o Python formata no padrão americano (1,234.50). Trocamos
    "," por um marcador X, "." por "," e depois X por ".".
    """
    texto = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def data_curta(data):
    """datetime → "07/11/2026 17:39". Se não for data (ex.: vazio), devolve como está."""
    return data.strftime("%d/%m/%Y %H:%M") if isinstance(data, datetime) else (data or "")


def converter_numero(texto, inteiro=False, nome="valor"):
    """Converte o que o usuário DIGITOU em número.

    - Aceita vírgula como decimal: "2,50" → 2.5
    - inteiro=True exige número inteiro (usado para quantidades)
    - O número precisa ser maior que zero
    - nome: usado na mensagem de erro ("Quantidade precisa ser...")
    """
    texto = str(texto).strip().replace(",", ".")
    try:
        numero = int(texto) if inteiro else float(texto)
    except ValueError:
        tipo = "um número inteiro" if inteiro else "um número"
        raise ErroEstoque(f"{nome.capitalize()} precisa ser {tipo}.")
    if numero <= 0:
        raise ErroEstoque(f"{nome.capitalize()} precisa ser maior que zero.")
    return numero


# ================================================================== validação (regra de negócio)
# A tela e o menu já conferem o que o usuário digita (converter_numero, acima).
# Estas funções são a ÚLTIMA barreira: ficam dentro das operações do banco,
# para que NENHUM caminho (tela, terminal, testes, uma futura API) consiga
# gravar uma quantidade inválida. Ex.: retirar(-5) aumentaria o estoque.

def validar_quantidade(quantidade, nome="quantidade"):
    """Garante que a quantidade é um número INTEIRO e MAIOR QUE ZERO.

    Aceita 3.0 (vira 3), mas recusa 2.5, 0, -5, "10" (texto) e True/False.
    Retorna a quantidade como int.
    """
    # bool é um tipo de int no Python (True == 1), por isso é recusado à parte
    if isinstance(quantidade, float) and quantidade.is_integer():
        quantidade = int(quantidade)
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise ErroEstoque(f"{nome.capitalize()} precisa ser um número inteiro.")
    if quantidade <= 0:
        raise ErroEstoque(f"{nome.capitalize()} precisa ser maior que zero.")
    return quantidade


def validar_valor(valor):
    """Garante que o valor unitário é um número e não é negativo (zero é aceito: brinde/amostra)."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErroEstoque("O valor precisa ser um número.")
    if valor < 0:
        raise ErroEstoque("O valor não pode ser negativo.")
    return valor
