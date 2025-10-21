#!/bin/bash
set -e

echo "🚀 Deployment de PatCode"
echo "========================"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar que estamos en la rama correcta
if command -v git &> /dev/null; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ] && [ "$BRANCH" != "unknown" ]; then
        echo -e "${YELLOW}⚠️  No estás en la rama main/master (actual: $BRANCH)${NC}"
        read -p "¿Continuar de todos modos? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Ejecutar tests si existen
if [ -d "tests" ]; then
    echo "🧪 Ejecutando tests..."
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short || {
            echo -e "${RED}❌ Tests fallaron${NC}"
            read -p "¿Continuar de todos modos? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        }
    else
        echo -e "${YELLOW}⚠️  pytest no disponible, saltando tests${NC}"
    fi
fi

echo -e "${GREEN}✓ Tests pasaron${NC}"

# Build de imágenes
echo "🔨 Construyendo imágenes..."
docker-compose build --no-cache

echo -e "${GREEN}✓ Build completado${NC}"

# Detener servicios actuales
echo "⏹️  Deteniendo servicios actuales..."
docker-compose down

# Iniciar nuevos servicios
echo "🚀 Iniciando servicios actualizados..."
docker-compose up -d

# Health check
echo "🏥 Verificando salud de servicios..."
sleep 10

if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Deployment exitoso!${NC}"
else
    echo -e "${RED}❌ Algunos servicios no están corriendo${NC}"
    docker-compose ps
    exit 1
fi

echo ""
echo "Logs en tiempo real:"
echo "  docker-compose logs -f"
