"""
CONFIGURAÇÃO DOS TESTES (pytest)
================================
O pytest lê este arquivo automaticamente antes de rodar os testes.

A "fixture" abaixo roda ANTES DE CADA TESTE (autouse=True) e:
  1. troca o arquivo do banco por uma planilha nova, numa pasta temporária;
  2. cria essa planilha vazia.
Assim cada teste começa do zero e o estoque.xlsx REAL nunca é tocado.

Rodar todos os testes:   python -m pytest -v
"""
import sys
from pathlib import Path

import pytest

# permite "import banco" mesmo rodando o pytest de dentro da pasta tests/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import banco  # noqa: E402


@pytest.fixture(autouse=True)
def planilha_temporaria(tmp_path, monkeypatch):
    """Cada teste ganha a sua própria planilha vazia (tmp_path é criado pelo pytest)."""
    monkeypatch.setattr(banco.config, "ARQUIVO", tmp_path / "estoque_teste.xlsx")
    banco.criar_banco()
    return banco.config.ARQUIVO


def situacao(objeto):
    """Consulta a situação de um produto (total, reservado, bloqueado, disponível)."""
    for item in banco.listar_itens():
        if item.objeto.lower() == objeto.lower():
            return item
    return None
