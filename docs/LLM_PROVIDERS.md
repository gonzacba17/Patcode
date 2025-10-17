# Sistema Híbrido de LLM Providers - PatCode

## 📋 Introducción

PatCode ahora soporta múltiples proveedores de modelos de lenguaje (LLM) con fallback automático. Esto significa que puedes usar diferentes servicios según tus necesidades y disponibilidad, con cambio automático si uno falla.

## 🤖 Providers Disponibles

### 1. **Groq** (Recomendado para producción)

**Pros:**
- ⚡ Extremadamente rápido (inferencia acelerada por hardware)
- 🆓 Free tier generoso
- 🎯 Modelos optimizados (Llama 3.1, Mixtral)
- 📊 Rate limits razonables (30 req/min)

**Contras:**
- 🔑 Requiere API key
- 🌐 Requiere conexión a internet
- 💳 Límites en tier gratuito

**Modelos recomendados:**
- `llama-3.1-70b-versatile` (por defecto) - Balance perfecto
- `llama-3.1-8b-instant` - Más rápido, menos potente
- `mixtral-8x7b-32768` - Contexto muy largo

**Cómo obtener API key:**
1. Ve a [console.groq.com](https://console.groq.com)
2. Crea una cuenta gratis
3. Ve a "API Keys"
4. Crea una nueva key
5. Agrégala a tu `.env`: `GROQ_API_KEY=gsk_...`

### 2. **Ollama** (Recomendado para desarrollo local)

**Pros:**
- 🏠 100% local y privado
- 🆓 Completamente gratis
- 🔒 Sin límites de rate
- 📡 Funciona sin internet

**Contras:**
- 🐌 Más lento que Groq (especialmente sin GPU)
- 💾 Requiere RAM (2-8GB según modelo)
- ⚙️ Requiere instalación local

**Modelos recomendados:**
- `qwen2.5-coder:1.5b` (por defecto) - Rápido, poco RAM
- `qwen2.5-coder:7b` - Mejor calidad, más RAM
- `codellama:7b` - Especializado en código
- `deepseek-coder:6.7b` - Excelente para código

**Instalación:**
```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Descarga desde https://ollama.com/download

# Verificar instalación
ollama --version

# Descargar modelo
ollama pull qwen2.5-coder:1.5b

# Iniciar servidor
ollama serve
```

### 3. **OpenAI** (Opcional)

**Pros:**
- 🎯 GPT-4 y modelos de última generación
- 📚 Amplio conocimiento
- 🔧 API muy confiable

**Contras:**
- 💰 Requiere pago (no hay tier gratuito real)
- 🌐 Requiere internet
- 🔑 Requiere API key de pago

**Modelos recomendados:**
- `gpt-4o-mini` (por defecto) - Balance costo/calidad
- `gpt-4-turbo` - Máxima calidad
- `gpt-3.5-turbo` - Más económico

**Cómo obtener API key:**
1. Ve a [platform.openai.com](https://platform.openai.com)
2. Crea una cuenta
3. Configura método de pago
4. Ve a "API Keys"
5. Crea una nueva key
6. Agrégala a tu `.env`: `OPENAI_API_KEY=sk-...`

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# ========================================
# LLM PROVIDER CONFIGURATION
# ========================================

# Provider principal (groq | ollama | openai)
LLM_DEFAULT_PROVIDER=groq

# Fallback automático si falla el principal
LLM_AUTO_FALLBACK=true

# Orden de fallback (separado por comas)
LLM_FALLBACK_ORDER=groq,ollama

# ========================================
# GROQ SETTINGS
# ========================================
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TIMEOUT=30

# ========================================
# OLLAMA SETTINGS
# ========================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
OLLAMA_TIMEOUT=30

# ========================================
# OPENAI SETTINGS (Opcional)
# ========================================
OPENAI_API_KEY=sk_your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30

# ========================================
# GENERAL LLM SETTINGS
# ========================================
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
```

### Configuración Programática

```python
from config import settings

# Acceder a configuración LLM
print(settings.llm.default_provider)
print(settings.llm.groq_api_key)
print(settings.llm.auto_fallback)
```

## 🚀 Uso

### Comandos CLI

```bash
# Ver providers disponibles y estado
/llm providers

# Cambiar provider manualmente
/llm switch groq
/llm switch ollama

# Ver estadísticas de uso
/llm stats

# Probar un provider específico
/llm test groq
/llm test ollama
```

### Ejemplos de Uso

#### 1. Solo Ollama (sin API keys)

```bash
# .env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:1.5b

# Iniciar
ollama serve
python main.py
```

PatCode usará Ollama automáticamente.

#### 2. Groq con Ollama como fallback

```bash
# .env
LLM_DEFAULT_PROVIDER=groq
LLM_AUTO_FALLBACK=true
LLM_FALLBACK_ORDER=groq,ollama
GROQ_API_KEY=gsk_...

# Iniciar
python main.py
```

Si Groq falla (sin internet, rate limit, etc.), automáticamente usa Ollama.

#### 3. Múltiples providers con prioridad

```bash
# .env
LLM_DEFAULT_PROVIDER=groq
LLM_FALLBACK_ORDER=groq,openai,ollama
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
```

Prioridad: Groq → OpenAI → Ollama

## 🔄 Fallback Automático

El sistema de fallback funciona así:

1. **Intenta con provider principal**
   ```
   Usuario: Hola
   → Intenta con Groq...
   ```

2. **Si falla, loguea warning**
   ```
   [WARNING] Provider 'groq' falló: Connection timeout
   [INFO] Intentando fallback a 'ollama'...
   ```

3. **Intenta con siguiente en orden**
   ```
   → Intenta con Ollama...
   ✓ Fallback exitoso a 'ollama'
   ```

4. **Si todos fallan, retorna error explicativo**
   ```
   [ERROR] No hay providers de fallback disponibles
   Sugerencias:
   - Verifica tu GROQ_API_KEY
   - Asegúrate que Ollama esté corriendo: ollama serve
   ```

### Desactivar Fallback

Si quieres que falle en lugar de hacer fallback:

```bash
LLM_AUTO_FALLBACK=false
```

## 📊 Monitoreo

### Ver Provider Actual

```python
# En PatAgent
print(agent.llm_manager.get_current_provider())
# Output: "groq"
```

### Ver Estadísticas

```bash
/llm stats
```

Output:
```
📊 Estadísticas LLM:

  Provider actual: groq
  Providers disponibles: groq, ollama
  Auto-fallback: ✅

📈 Por Provider:

  GROQ:
    - Requests: 45
    - Exitosos: 43
    - Fallidos: 2
    - Tasa de éxito: 95.6%
    - Tiempo promedio: 1.23s

  OLLAMA:
    - Requests: 2
    - Exitosos: 2
    - Fallidos: 0
    - Tasa de éxito: 100%
    - Tiempo promedio: 4.56s
```

## 🛠️ Troubleshooting

### Groq: "API key inválida"

```bash
# Verificar que la key esté bien configurada
echo $GROQ_API_KEY

# Debe empezar con "gsk_"
# Si no funciona, genera una nueva en console.groq.com
```

### Ollama: "Connection refused"

```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, iniciar servidor
ollama serve

# Verificar modelos instalados
ollama list

# Si el modelo no está, descargarlo
ollama pull qwen2.5-coder:1.5b
```

### "No hay providers disponibles"

```bash
# Verificar configuración
/llm providers

# Debe mostrar al menos uno con ✅

# Si todos tienen ❌:
# 1. Verifica .env
# 2. Verifica que Ollama esté corriendo
# 3. Verifica tus API keys
```

### Rate Limit en Groq

Groq tiene límite de 30 requests/minuto en tier gratuito.

Si ves: `Rate limit alcanzado, esperando X.Xs...`

El sistema automáticamente:
- Espera el tiempo necesario
- O hace fallback a Ollama si está habilitado

### Modelo no encontrado en Ollama

```bash
# Error: "Modelo 'xxx' no encontrado"
# Solución:
ollama pull qwen2.5-coder:1.5b

# Ver modelos disponibles
ollama list
```

## 🎯 Casos de Uso Recomendados

### Desarrollo Local (sin internet)

```bash
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:1.5b
```

### Producción (máxima velocidad)

```bash
LLM_DEFAULT_PROVIDER=groq
LLM_FALLBACK_ORDER=groq,ollama
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-70b-versatile
```

### Máxima disponibilidad

```bash
LLM_DEFAULT_PROVIDER=groq
LLM_AUTO_FALLBACK=true
LLM_FALLBACK_ORDER=groq,openai,ollama
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
```

### Solo OpenAI (alta calidad)

```bash
LLM_DEFAULT_PROVIDER=openai
LLM_AUTO_FALLBACK=false
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## 📈 Comparación de Performance

| Provider | Velocidad | Calidad | Costo | Internet | Privacidad |
|----------|-----------|---------|-------|----------|------------|
| **Groq** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Gratis* | ✅ | ⚠️ |
| **Ollama** | ⭐⭐⭐ | ⭐⭐⭐ | Gratis | ❌ | ⭐⭐⭐⭐⭐ |
| **OpenAI** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 | ✅ | ⚠️ |

*Free tier con límites

## 🔐 Seguridad

- **Nunca** compartas tus API keys
- **Nunca** commitees `.env` a git (ya está en `.gitignore`)
- Usa variables de entorno en producción
- Rota tus keys periódicamente
- Usa Ollama si trabajas con código sensible

## 🆘 Soporte

Si tienes problemas:

1. Revisa esta documentación
2. Ejecuta `/llm providers` para ver el estado
3. Revisa los logs de PatCode
4. Verifica tu configuración en `.env`
5. Abre un issue en GitHub con los logs

## 🚀 Próximas Mejoras

- [ ] Soporte para Anthropic Claude
- [ ] Soporte para Google Gemini
- [ ] Sistema de caché por provider
- [ ] Balance de carga entre providers
- [ ] Métricas de costo por provider
- [ ] UI web para gestión de providers
