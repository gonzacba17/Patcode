# 🚀 Guía Rápida: Sistema LLM en PatCode

## Instalación en 5 minutos

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `groq` - Cliente de Groq API
- `openai` - Cliente de OpenAI (opcional)

### 2. Configurar provider

**Opción A: Usar Ollama (100% local, sin API keys)**

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo
ollama pull qwen2.5-coder:1.5b

# Iniciar servidor
ollama serve
```

Archivo `.env`:
```bash
LLM_DEFAULT_PROVIDER=ollama
```

**Opción B: Usar Groq (gratis, rápido, requiere internet)**

1. Ve a [console.groq.com](https://console.groq.com)
2. Crea cuenta gratis
3. Genera API key

Archivo `.env`:
```bash
LLM_DEFAULT_PROVIDER=groq
GROQ_API_KEY=gsk_tu_key_aqui
```

**Opción C: Groq + Ollama (fallback automático)**

```bash
LLM_DEFAULT_PROVIDER=groq
LLM_AUTO_FALLBACK=true
LLM_FALLBACK_ORDER=groq,ollama
GROQ_API_KEY=gsk_tu_key_aqui
```

### 3. Iniciar PatCode

```bash
python main.py
```

## Comandos Básicos

```bash
# Ver providers disponibles
/llm providers

# Cambiar de provider
/llm switch groq
/llm switch ollama

# Ver estadísticas
/llm stats

# Probar un provider
/llm test groq
```

## Ejemplo de Sesión

```
$ python main.py

PatCode v0.4 🤖
LLM Provider: groq
Modelo: llama-3.1-70b-versatile

> Hola
¡Hola! Soy Pat, tu asistente de programación. ¿En qué puedo ayudarte?

> /llm providers
🤖 LLM Providers:

  ✅ groq ⬅ ACTUAL
  ✅ ollama

💡 Auto-fallback: ✅ Activado
📋 Orden de fallback: groq, ollama

> /llm switch ollama
✅ Provider cambiado a: ollama

> Hola de nuevo
¡Hola! Ahora estoy usando Ollama localmente. ¿Qué necesitas?
```

## Troubleshooting Rápido

### "No hay providers disponibles"

```bash
# Verificar Ollama
curl http://localhost:11434/api/tags

# Si falla, iniciar Ollama
ollama serve
```

### "Groq API key inválida"

```bash
# Verificar que esté configurada
echo $GROQ_API_KEY

# Debe empezar con "gsk_"
# Si no, genera una nueva en console.groq.com
```

### "Modelo no encontrado"

```bash
# Descargar modelo en Ollama
ollama pull qwen2.5-coder:1.5b

# Ver modelos instalados
ollama list
```

## Configuración Recomendada

Para la mejor experiencia:

```bash
# .env
LLM_DEFAULT_PROVIDER=groq
LLM_AUTO_FALLBACK=true
LLM_FALLBACK_ORDER=groq,ollama

GROQ_API_KEY=gsk_tu_key
GROQ_MODEL=llama-3.1-70b-versatile

OLLAMA_MODEL=qwen2.5-coder:1.5b

LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
```

Esto te da:
- ⚡ Velocidad de Groq cuando hay internet
- 🏠 Ollama como backup local
- 🔄 Cambio automático si Groq falla

## Siguiente Paso

Lee la [documentación completa](LLM_PROVIDERS.md) para:
- Configuración avanzada
- Comparación de providers
- Optimización de performance
- Manejo de errores
