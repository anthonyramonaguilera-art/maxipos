@echo off
echo ==========================================
echo    CONSTRUCTOR AUTOMATICO - MAXI POS v2.0
echo         Por: Varons Media
echo ==========================================
echo.

echo [1/3] Limpiando compilaciones previas...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] Compilando codigo Python a .exe...
python -m PyInstaller --noconsole --name "MaxiPOS" --icon="logo.png" main.py

echo [3/3] Copiando recursos base (Logo y Base de Datos)...
if exist "logo.png" copy "logo.png" "dist\MaxiPOS\"
if exist "sistema_pos.db" copy "sistema_pos.db" "dist\MaxiPOS\"

echo.
echo ==========================================
echo COMPILACION EXITOSA - VARONS MEDIA
echo ==========================================
pause