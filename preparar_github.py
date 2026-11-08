"""
PREPARAR PASTA PARA O GITHUB
============================
Rode com:  python preparar_github.py

Copia SÓ os arquivos do projeto (sem a planilha com seus dados, sem o .exe e
sem arquivos temporários) para a pasta "controle-de-estoque-github", ao lado
desta pasta. É essa pasta que você arrasta para o GitHub.

Nada nesta pasta de trabalho é alterado: você continua usando o programa
normalmente aqui. Sempre que mudar o código, rode de novo para atualizar a cópia.
"""
import shutil
from pathlib import Path

PROJETO = Path(__file__).resolve().parent
DESTINO = PROJETO.parent / "controle-de-estoque-github"

# O que vai para o GitHub (arquivos e pastas)
ITENS = [
    "README.md", "requirements.txt", ".gitignore", "gerar_exe.bat", "preparar_github.py",
    "estoque.py", "tela.py", "banco", "tests", "assets", "docs",
]
# O que nunca é copiado de dentro das pastas
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", "*.xlsx", "*.exe", ".pytest_cache")


def main():
    DESTINO.mkdir(exist_ok=True)
    for nome in ITENS:
        origem = PROJETO / nome
        if not origem.exists():
            print(f"  (não encontrado, pulei: {nome})")
            continue
        if origem.is_dir():
            shutil.copytree(origem, DESTINO / nome, ignore=IGNORAR, dirs_exist_ok=True)
        else:
            shutil.copy2(origem, DESTINO / nome)
        print(f"  ok  {nome}")
    print(f"\nPronto! Pasta para o GitHub:\n  {DESTINO}")


if __name__ == "__main__":
    main()
