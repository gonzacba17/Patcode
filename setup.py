#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

def setup():
    print("🔧 Configurando PatCode...\n")
    
    # Crear .env si no existe
    env_file = Path('.env')
    if not env_file.exists():
        env_content = """LLM_DEFAULT_PROVIDER=groq
LLM_AUTO_FALLBACK=true

GROQ_API_KEY=
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TIMEOUT=30

OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
OLLAMA_TIMEOUT=30"""
        env_file.write_text(env_content, encoding='utf-8')
        print("✅ .env creado")
    
    # Pedir GROQ_API_KEY
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GROQ_API_KEY'):
        print("📋 Obtén tu API key gratis en: https://console.groq.com")
        key = input("🔑 Pega tu GROQ_API_KEY (o Enter para omitir): ").strip()
        
        if key:
            try:
                lines = env_file.read_text(encoding='utf-8').splitlines()
                new_lines = [f'GROQ_API_KEY={key}' if line.startswith('GROQ_API_KEY=') else line for line in lines]
                env_file.write_text('\n'.join(new_lines), encoding='utf-8')
                print("✅ GROQ_API_KEY guardada")
            except Exception as e:
                print(f"⚠️ Error guardando key: {e}")
                print("💡 Edita .env manualmente y agrega: GROQ_API_KEY=" + key)
    
    # Verificar Ollama
    try:
        import requests
        r = requests.get('http://localhost:11434/api/tags', timeout=2)
        print("✅ Ollama disponible" if r.status_code == 200 else "⚠️ Ollama no responde")
    except:
        print("❌ Ollama no encontrado. Instalar de: https://ollama.com/download")
    
    # Instalar dependencias
    print("\n📦 Instalando dependencias...")
    os.system('pip install groq python-dotenv requests')
    
    print("\n🚀 Setup completo. Ejecuta: python main.py")

if __name__ == '__main__':
    try:
        setup()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
