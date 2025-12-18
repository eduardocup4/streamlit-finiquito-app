@echo off
REM Run script for Finiquito Application (Windows)
REM Ensures proper setup and launches Streamlit

echo ═══════════════════════════════════════════════════════
echo     Sistema de Calculo de Finiquitos - Bolivia
echo ═══════════════════════════════════════════════════════
echo.

REM Change to app directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no esta instalado. Por favor instale Python 3.11+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creando entorno virtual...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activando entorno virtual...
call venv\Scripts\activate

REM Check if requirements are installed
echo 📚 Verificando dependencias...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo 📥 Instalando dependencias...
    pip install -r requirements.txt
)

REM Initialize database if not exists
if not exist "finiquito.db" (
    echo 🗄️ Inicializando base de datos...
    if exist "scripts\init_database.py" (
        python scripts\init_database.py
    ) else (
        echo ⚠️ Script de inicializacion no encontrado, se creara DB al iniciar
    )
)

REM Check if templates exist
if not exist "storage\templates\*.xlsx" (
    echo 📄 Generando plantillas...
    if exist "scripts\generate_templates.py" (
        python scripts\generate_templates.py
    )
)

REM Check for command line arguments
if "%1"=="--test-data" (
    echo 🧪 Generando datos de prueba...
    if exist "scripts\generate_test_data.py" (
        python scripts\generate_test_data.py
    )
)

if "%1"=="--clear-cache" (
    echo 🗑️ Limpiando cache de Streamlit...
    rmdir /s /q "%USERPROFILE%\.streamlit\cache" 2>nul
)

REM Launch Streamlit
echo.
echo 🚀 Iniciando aplicacion...
echo ═══════════════════════════════════════════════════════
echo.
echo 📌 La aplicacion estara disponible en:
echo    http://localhost:8501
echo.
echo 📌 Usuarios de prueba:
echo    Admin:    admin / admin123
echo    Operador: operator / oper123
echo    Visor:    viewer / view123
echo.
echo 📌 Para detener: Presione Ctrl+C
echo ═══════════════════════════════════════════════════════
echo.

REM Run Streamlit
streamlit run main.py ^
    --server.port=8501 ^
    --server.address=localhost ^
    --server.headless=true ^
    --browser.gatherUsageStats=false ^
    --theme.base="light" ^
    --theme.primaryColor="#1f77b4"
