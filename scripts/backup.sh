#!/bin/bash
set -e

echo "💾 Backup de PatCode"
echo "===================="

# Colores
GREEN='\033[0;32m'
NC='\033[0m'

# Crear directorio de backups
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Directorio de backup: $BACKUP_DIR"

# Backup de memoria
if [ -d "agents/memory" ]; then
    echo "💾 Respaldando memoria..."
    cp -r agents/memory "$BACKUP_DIR/"
fi

# Backup de caché
if [ -d "agents/cache" ]; then
    echo "💾 Respaldando caché..."
    cp -r agents/cache "$BACKUP_DIR/"
fi

# Backup de logs
if [ -d "logs" ]; then
    echo "💾 Respaldando logs..."
    cp -r logs "$BACKUP_DIR/"
fi

# Backup de configuración
if [ -f ".env" ]; then
    echo "💾 Respaldando configuración..."
    cp .env "$BACKUP_DIR/"
fi

# Comprimir backup
echo "📦 Comprimiendo backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C backups "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

SIZE=$(du -h "$BACKUP_DIR.tar.gz" | cut -f1)

echo -e "${GREEN}✅ Backup completado!${NC}"
echo "📦 Archivo: $BACKUP_DIR.tar.gz ($SIZE)"
echo ""
echo "Para restaurar:"
echo "  tar -xzf $BACKUP_DIR.tar.gz -C backups/"
echo "  cp -r backups/$(basename $BACKUP_DIR)/* ."
