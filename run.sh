#!/bin/bash

# Run script for Finiquito Application
# Ensures proper setup and launches Streamlit

echo "═══════════════════════════════════════════════════════"
echo "    Sistema de Cálculo de Finiquitos - Bolivia"
echo "═══════════════════════════════════════════════════════"
echo ""

# Change to app directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instale Python 3.11+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Check if requirements are installed
echo "📚 Verificando dependencias..."
if ! pip show streamlit > /dev/null 2>&1; then
    echo "📥 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Initialize database if not exists
if [ ! -f "finiquito.db" ]; then
    echo "🗄️ Inicializando base de datos..."
    if [ -f "scripts/init_database.py" ]; then
        python scripts/init_database.py
    else
        echo "⚠️ Script de inicialización no encontrado, se creará DB al iniciar"
    fi
fi

# Check if templates exist
if [ ! -d "storage/templates" ] || [ -z "$(ls -A storage/templates 2>/dev/null)" ]; then
    echo "📄 Generando plantillas..."
    if [ -f "scripts/generate_templates.py" ]; then
        python scripts/generate_templates.py
    fi
fi

# Check if test data should be generated
if [ "$1" == "--test-data" ]; then
    echo "🧪 Generando datos de prueba..."
    if [ -f "scripts/generate_test_data.py" ]; then
        python scripts/generate_test_data.py
    fi
fi

# Clear Streamlit cache if requested
if [ "$1" == "--clear-cache" ]; then
    echo "🗑️ Limpiando caché de Streamlit..."
    rm -rf ~/.streamlit/cache
fi

# Launch Streamlit
echo ""
echo "🚀 Iniciando aplicación..."
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 La aplicación estará disponible en:"
echo "   http://localhost:8501"
echo ""
echo "📌 Usuarios de prueba:"
echo "   Admin:    admin / admin123"
echo "   Operador: operator / oper123"
echo "   Visor:    viewer / view123"
echo ""
echo "📌 Para detener: Presione Ctrl+C"
echo "═══════════════════════════════════════════════════════"
echo ""

# Run Streamlit
streamlit run main.py \
    --server.port=8501 \
    --server.address=localhost \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --theme.base="light" \
    --theme.primaryColor="#1f77b4"
