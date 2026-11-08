@echo off
REM ==================================================================
REM  Gera o "Controle de Estoque.exe" nesta pasta.
REM  Basta dar dois cliques neste arquivo.
REM  (Feche o programa antes, se ele estiver aberto.)
REM ==================================================================
cd /d "%~dp0"

echo Instalando/atualizando as bibliotecas necessarias...
python -m pip install -r requirements.txt pyinstaller --quiet --disable-pip-version-check
if errorlevel 1 goto erro

echo Gerando o executavel (leva cerca de 1 minuto)...
python -m PyInstaller tela.py --onefile --noconsole --name "Controle de Estoque" ^
    --icon "%~dp0assets\estoque.ico" --collect-data customtkinter ^
    --distpath . --workpath build --specpath build --noconfirm --log-level WARN
if errorlevel 1 goto erro

echo.
echo Pronto! O programa esta em: "%~dp0Controle de Estoque.exe"
echo A planilha estoque.xlsx fica na mesma pasta do .exe.
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Confira se o Python esta instalado e se o programa esta fechado.
pause
exit /b 1
