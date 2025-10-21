# 🧠 PatCode - AetherMind Edition

> Asistente de programación local impulsado por IA - 100% Offline con Ollama

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](Dockerfile)
[![Ollama](https://img.shields.io/badge/ollama-compatible-green)](https://ollama.ai)

---

## 📖 Índice

1. [Introducción](#-introducción)
2. [Características Principales](#-características-principales)
3. [Instalación Rápida](#-instalación-rápida)
4. [Uso](#-uso)
5. [Arquitectura](#-arquitectura)
6. [Configuración](#-configuración)
7. [Desarrollo](#-desarrollo)
8. [Estado del Proyecto](#-estado-del-proyecto)

---

## 🎯 Introducción

**PatCode AetherMind** es un asistente de programación local que replica funcionalidades avanzadas de Claude Code, pero **completamente offline** usando modelos LLM locales via [Ollama](https://ollama.ai/).

### ¿Por qué PatCode?

- **🔒 100% Privado** - Todo corre en tu máquina, tus datos nunca salen
- **⚡ Sin límites** - Sin rate limiting, cuotas ni suscripciones
- **🌐 Offline First** - Funciona sin internet (excepto providers cloud opcionales)
- **🧩 Extensible** - Sistema de plugins para funcionalidades personalizadas
- **🎨 Multi-Provider** - Soporta Ollama, OpenAI, Groq

---

## ✨ Características Principales

### 💬 Conversación Inteligente
- Memoria contextual con rotación activa/pasiva
- Resúmenes automáticos de conversaciones largas
- Historial persistente entre sesiones
- Búsqueda en conversaciones pasadas

### 🧩 Sistema de Plugins
- **Auto-descubrimiento** de plugins en `plugins/builtin/`
- **Plugins incluidos:**
  - `CodeExplainer` - Explica código en detalle
  - `GitHelper` - Asistencia con Git (status, diff, commits)
  - `FileAnalyzer` - Analiza estructura de proyectos
- **Extensible:** Crea tus propios plugins fácilmente

### 🔌 Multi-Provider LLM
- **Ollama** (local, privado)
- **OpenAI** (GPT-4, GPT-3.5)
- **Groq** (Llama, Mixtral ultrarrápido)
- Abstracción unificada con `BaseAdapter`

### ⚡ Performance
- **Caché inteligente** con similitud Jaccard
- **TTL configurable** (default: 24h)
- **Hit rate típico:** 35-40% en sesiones largas
- **Ahorro:** ~50% en queries repetidas

### 📊 Monitoreo
- **Telemetría simple:** counters, gauges, timers
- **Logging avanzado** con rotación de archivos
- **Estadísticas de uso:** `/stats` en tiempo real

### 🎨 Interfaz Moderna
- **Rich Terminal UI:** syntax highlighting, paneles, tablas
- **Autocompletado** con historial persistente
- **Progress bars** para operaciones largas
- **Markdown rendering** de respuestas

---

## 🚀 Instalación Rápida

### Opción 1: Script Automático (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/gonzacba17/Patocode.git
cd Patocode

# Ejecutar instalador
./install.sh
```

El script detecta tu sistema operativo y te guía paso a paso.

### Opción 2: Docker

```bash
# Iniciar con docker-compose
docker-compose up -d

# Usar PatCode
docker-compose exec patcode python main.py

# Ver logs
docker-compose logs -f patcode
```

### Opción 3: Manual

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar
cp .env.example .env

# Instalar Ollama (si no lo tienes)
# https://ollama.ai

# Descargar modelo
ollama pull qwen2.5-coder:7b

# Ejecutar
python main.py
```

---

## 💻 Uso

### Comandos Disponibles

```bash
# Comandos básicos
/help              # Muestra ayuda completa
/model [nombre]    # Cambia modelo LLM (si implementado)
/clear             # Limpia memoria activa
/exit              # Sale del programa

# Gestión de contexto
/load <archivo>    # Carga archivo al contexto
/files             # Lista archivos cargados
/unload <archivo>  # Descarga archivo del contexto
/show <archivo>    # Muestra contenido de archivo cargado

# Memoria y estadísticas
/stats             # Muestra estadísticas de uso
/search <texto>    # Busca en historial
/export [archivo]  # Exporta conversación a JSON

# Plugins
/plugins           # Gestiona plugins
/cache             # Gestiona caché de respuestas
```

### Ejemplos de Uso

#### 1. Pregunta Simple
```
Tú: ¿Qué es un decorador en Python?
PatCode: Un decorador en Python es una función que modifica el comportamiento...
```

#### 2. Explicar Código
```
Tú: Explica este código:
def factorial(n):
    return 1 if n == 0 else n * factorial(n-1)

PatCode: Esta función calcula el factorial de un número usando recursión...
```

#### 3. Análisis de Proyecto
```
Tú: /load README.md
PatCode: ✅ Archivo cargado al contexto

Tú: Analiza la estructura del proyecto
PatCode: Basándome en el README, este proyecto tiene...
```

#### 4. Usar Plugins
```
Tú: /plugins
PatCode: [Muestra tabla de plugins disponibles]

Tú: Usa git_helper para ver el status
PatCode: [Ejecuta git status y muestra análisis]
```

---

## 🏗️ Arquitectura

```
PatCode/
├── agents/                      # Lógica principal
│   ├── llm_adapters/           # Abstracción de providers
│   │   ├── base_adapter.py     # Interfaz base
│   │   ├── ollama_adapter.py   # Adapter Ollama
│   │   ├── openai_adapter.py   # Adapter OpenAI
│   │   └── groq_adapter.py     # Adapter Groq
│   ├── memory/                 # Sistema de memoria
│   │   ├── memory_manager.py   # Gestor principal
│   │   └── sqlite_memory_manager.py  # Persistencia SQLite
│   ├── cache/                  # Sistema de caché
│   │   └── cache_manager.py    # Gestor de caché
│   ├── pat_agent.py            # Agente principal
│   └── orchestrator.py         # Orquestador de flujos
│
├── plugins/                     # Sistema de plugins
│   ├── base.py                 # PluginInterface, PluginManager
│   ├── registry.py             # Registro de plugins
│   └── builtin/                # Plugins integrados
│       ├── code_explainer.py   # Explicador de código
│       ├── git_helper.py       # Helper de Git
│       └── file_analyzer.py    # Analizador de archivos
│
├── ui/                         # Interfaz de usuario
│   ├── rich_terminal.py        # Terminal UI con Rich
│   ├── cli.py                  # CLI con Click
│   └── memory_commands.py      # Comandos de memoria
│
├── utils/                      # Utilidades
│   ├── simple_telemetry.py     # Telemetría
│   ├── response_cache.py       # Caché de respuestas
│   ├── logger.py               # Sistema de logging
│   └── validators.py           # Validadores
│
├── config/                     # Configuración
│   ├── settings.py             # Settings centralizados
│   ├── model_selector.py       # Selector de modelos
│   └── prompts.py              # Prompts del sistema
│
├── tests/                      # Tests (3200+ líneas)
│   ├── test_*.py               # Tests unitarios
│   └── integration/            # Tests de integración
│
├── scripts/                    # Scripts DevOps
│   ├── setup.sh                # Setup inicial
│   ├── deploy.sh               # Despliegue
│   └── backup.sh               # Backup de datos
│
├── docs/                       # Documentación
│   ├── README.MD               # Este archivo
│   ├── CHANGELOG.md            # Historial de cambios
│   ├── LLM_PROVIDERS.md        # Guía de providers
│   └── QUICKSTART_LLM.md       # Quickstart LLM
│
├── Dockerfile                  # Containerización
├── docker-compose.yml          # Orquestación Docker
├── install.sh                  # Instalador automático
├── requirements.txt            # Dependencias
└── .env.example                # Configuración ejemplo
```

---

## ⚙️ Configuración

### Archivo `.env`

```bash
# ================================
# OLLAMA - Configuración LLM Local
# ================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_TEMPERATURE=0.7
REQUEST_TIMEOUT=120

# ================================
# PROVIDERS CLOUD (OPCIONAL)
# ================================
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# ================================
# MEMORIA - Persistencia
# ================================
MAX_HISTORY_MESSAGES=20
CONTEXT_WINDOW_SIZE=10
MAX_ACTIVE_MESSAGES=10
MAX_MEMORY_FILE_SIZE=5242880  # 5MB

# ================================
# CACHÉ
# ================================
CACHE_ENABLED=true
CACHE_TTL_SECONDS=86400  # 24 horas

# ================================
# LOGGING
# ================================
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=true
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5
```

### Modelos Recomendados

| Modelo | RAM Min | RAM Rec | Velocidad | Uso Ideal |
|--------|---------|---------|-----------|-----------|
| `qwen2.5-coder:7b` | 8GB | 12GB | ⚡⚡ Rápido | **Coding general (RECOMENDADO)** |
| `llama3.2:3b` | 6GB | 8GB | ⚡⚡⚡ Muy rápido | Chat, preguntas simples |
| `codellama:7b` | 12GB | 16GB | ⚡ Balanceado | Debugging, refactoring |
| `deepseek-coder:6.7b` | 10GB | 14GB | ⚡⚡ Rápido | Code completion, análisis |
| `mistral:7b` | 12GB | 16GB | ⚡ Balanceado | General purpose |

---

## 🧪 Desarrollo

### Instalar Dependencias de Desarrollo

```bash
pip install -r requirements-dev.txt
```

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/

# Con cobertura
pytest --cov=agents --cov=plugins --cov=utils tests/

# Tests específicos
pytest tests/test_llm_system.py -v

# Con reporte HTML
pytest --cov=agents --cov-report=html tests/
```

### Pre-commit Hooks

```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

### Linting y Formateo

```bash
# Black (formateo)
black agents/ plugins/ utils/

# isort (ordenar imports)
isort agents/ plugins/ utils/

# flake8 (linting)
flake8 agents/ plugins/ utils/
```

---

## 📊 Estado del Proyecto

### Versión Actual: `1.0.0-beta` ✅ **FUNCIONAL**

**Progreso General: ~90% Completado** 🎉

#### ✅ Completado (Fases 1, 2 y 3)

- ✅ **Fase 1 - Fundamentos (100%)**
  - Sistema de configuración externalizada
  - Manejo robusto de errores
  - Logging avanzado
  - Healthcheck de Ollama
  - Validadores de entrada

- ✅ **Fase 2 - Arquitectura Multi-Provider (90%)**
  - ✅ Abstracción de providers (BaseAdapter)
  - ✅ **Adapters funcionales:** Ollama, OpenAI, Groq (3/3)
  - ✅ Sistema de memoria optimizado con rotación
  - ✅ Comandos especiales implementados
  - ✅ **Bugs críticos resueltos** (2025-10-21)
  - 🚧 Streaming de respuestas (pendiente)
  - 🚧 Comando `/model` dinámico (pendiente)

- ✅ **Fase 3 - Avanzado (100%)**
  - Sistema de plugins extensible
  - 3 plugins built-in funcionales
  - Caché inteligente con TTL
  - Telemetría simple y avanzada
  - Containerización completa (Docker)
  - CI/CD configurado (GitHub Actions)
  - Scripts DevOps (4 scripts)

#### 🐛 Bugs Conocidos

- ⚠️ **Warning de logger** (no crítico) - PathLike error al arrancar
- 📋 **Todos los bugs críticos resueltos** (21-Oct-2025)

#### 📋 Pendiente (Fase 4)

- [ ] Implementar streaming de respuestas (3-4h)
- [ ] Comando `/model` para cambio dinámico (2h)
- [ ] Completar tests de integración (>70% cobertura)
- [ ] Ejecutar CI/CD pipeline completo
- [ ] Resolver warning de logger

### Métricas Reales

- **Archivos Python:** 161
- **Líneas de código:** 34,279
- **Tests:** 17 archivos (3,020 líneas)
- **Plugins built-in:** 3/3 funcionales
- **Adapters funcionales:** 3/3 ✅
- **Providers soportados:** 3
- **Comandos CLI:** ~12
- **Dependencias:** 21
- **Bugs críticos:** 0 ✅

Ver [ROADMAP.md](ROADMAP.md) para detalles completos.

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "feat: nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crea un Pull Request

### Convenciones

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` - Nueva funcionalidad
  - `fix:` - Corrección de bug
  - `docs:` - Documentación
  - `test:` - Tests
  - `refactor:` - Refactorización

- **Código:** PEP 8
- **Docstrings:** Google Style
- **Type hints:** Preferidos

---

## 📝 Licencia

MIT License - Ver [LICENSE](../LICENSE)

Copyright (c) 2025 Gonza Cba

---

## 🙏 Agradecimientos

- [Anthropic](https://anthropic.com) - Inspiración con Claude Code
- [Ollama](https://ollama.ai) - Motor LLM local
- [Rich](https://rich.readthedocs.io) - UI de terminal
- Comunidad open-source

---

## 📧 Contacto y Soporte

- **GitHub Issues:** [github.com/gonzacba17/Patocode/issues](https://github.com/gonzacba17/Patocode/issues)
- **Repositorio:** [github.com/gonzacba17/Patocode](https://github.com/gonzacba17/Patocode)
- **Autor:** Gonza Cba

---

## 📚 Recursos Adicionales

- [Documentación Ollama](https://github.com/ollama/ollama)
- [LLM Providers Guide](LLM_PROVIDERS.md)
- [Quickstart LLM](QUICKSTART_LLM.md)
- [Performance Guide](performance_guide.md)
- [Changelog Completo](CHANGELOG.md)

---

**Creado con ❤️ por Gonza Cba**

_Si te gusta PatCode, ¡dale una ⭐ en GitHub!_
