#!/bin/bash
set -e

echo "🚀 Setup de PatCode"
echo "==================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker y Docker Compose encontrados${NC}"

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Creando archivo .env desde .env.example${NC}"
    cp config/.env.example .env 2>/dev/null || cp .env.example .env 2>/dev/null || echo "Warning: No .env.example found"
fi

echo -e "${GREEN}✓ Archivo .env configurado${NC}"

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p agents/memory logs agents/cache

echo -e "${GREEN}✓ Directorios creados${NC}"

# Build de imágenes
echo "🔨 Construyendo imágenes Docker..."
docker-compose build

echo -e "${GREEN}✓ Imágenes construidas${NC}"

# Iniciar servicios
echo "🚀 Iniciando servicios..."
docker-compose up -d ollama

# Esperar a que Ollama esté listo
echo "⏳ Esperando a que Ollama esté disponible..."
max_retries=30
retry=0
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    retry=$((retry + 1))
    if [ $retry -gt $max_retries ]; then
        echo -e "${RED}❌ Timeout esperando a Ollama${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""

echo -e "${GREEN}✓ Ollama está disponible${NC}"

# Descargar modelo por defecto
echo "📦 Descargando modelo llama3.2..."
docker-compose exec -T ollama ollama pull llama3.2 || echo "Warning: Could not pull model"

echo ""
echo -e "${GREEN}✅ Setup completado!${NC}"
echo ""
echo "Para usar PatCode:"
echo "  docker-compose up -d patcode"
echo "  docker-compose exec patcode python main.py"
echo ""
echo "Para ver logs:"
echo "  docker-compose logs -f patcode"
echo ""
echo "Para detener:"
echo "  docker-compose down"
