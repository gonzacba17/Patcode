#!/bin/bash
set -e

echo "╔════════════════════════════════════════╗"
echo "║   PatCode - Instalación Rápida        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    echo "❌ Sistema operativo no soportado: $OSTYPE"
    exit 1
fi

echo "🖥️  Sistema detectado: $OS"
echo ""

# Función para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        echo "✅ $1 instalado"
        return 0
    else
        echo "❌ $1 no encontrado"
        return 1
    fi
}

# Verificar dependencias
echo "🔍 Verificando dependencias..."
echo ""

PYTHON_OK=false
DOCKER_OK=false

if check_command python3 || check_command python; then
    PYTHON_OK=true
fi

if check_command docker; then
    DOCKER_OK=true
fi

echo ""

# Opciones de instalación
echo "Selecciona método de instalación:"
echo ""
echo "1) 🐍 Instalación local (Python)"
echo "2) 🐳 Instalación con Docker"
echo "3) ❌ Salir"
echo ""

read -p "Opción (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📦 Instalación local"
        echo "===================="
        echo ""
        
        if [ "$PYTHON_OK" = false ]; then
            echo "❌ Python no está instalado"
            echo "Por favor instala Python 3.9+ desde https://python.org"
            exit 1
        fi
        
        # Crear entorno virtual
        echo "📦 Creando entorno virtual..."
        python3 -m venv venv || python -m venv venv
        
        # Activar entorno
        if [ "$OS" = "windows" ]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi
        
        # Instalar dependencias
        echo "📦 Instalando dependencias..."
        pip install -r requirements.txt
        
        # Configurar
        echo "⚙️  Configurando..."
        if [ ! -f .env ]; then
            cp config/.env.example .env 2>/dev/null || echo "Warning: .env.example not found"
        fi
        
        mkdir -p agents/memory logs agents/cache
        
        echo ""
        echo "✅ Instalación completada!"
        echo ""
        echo "Para ejecutar PatCode:"
        if [ "$OS" = "windows" ]; then
            echo "  venv\\Scripts\\activate"
        else
            echo "  source venv/bin/activate"
        fi
        echo "  python main.py"
        ;;
    
    2)
        echo ""
        echo "🐳 Instalación con Docker"
        echo "========================="
        echo ""
        
        if [ "$DOCKER_OK" = false ]; then
            echo "❌ Docker no está instalado"
            echo "Por favor instala Docker desde https://docker.com"
            exit 1
        fi
        
        # Ejecutar setup script
        chmod +x scripts/setup.sh
        ./scripts/setup.sh
        
        echo ""
        echo "✅ Instalación completada!"
        echo ""
        echo "Para ejecutar PatCode:"
        echo "  docker-compose up -d patcode"
        echo "  docker-compose exec patcode python main.py"
        ;;
    
    3)
        echo "👋 Saliendo..."
        exit 0
        ;;
    
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac
