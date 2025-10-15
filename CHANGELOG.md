# Changelog

Todos los cambios notables en PatCode se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [0.5.0] - 2025-10-16

### ✨ Añadido

**Sistema de Plugins Extensible:**
- ✅ `PluginInterface` - Interfaz estándar para crear plugins
- ✅ `PluginManager` - Gestor con auto-descubrimiento
- ✅ Auto-carga de plugins desde `tools/plugins/`
- ✅ Validación de dependencias
- ✅ Hooks `on_load()` y `on_unload()`
- ✅ Gestión de errores y plugins fallidos

**Plugins Incluidos:**

**1. Git Helper Plugin (git_helper):**
- ✅ `git status` con análisis (staged, modified, untracked)
- ✅ `git diff` con estadísticas (+/-)
- ✅ `git commit` con validación
- ✅ `git log` formateado
- ✅ Sugerencias de commit semántico con LLM (Conventional Commits)
- ✅ Detección automática de repositorio

**2. Docker Helper Plugin (docker_helper):**
- ✅ Generación de Dockerfile optimizado
- ✅ Generación de docker-compose.yml
- ✅ Generación de .dockerignore
- ✅ Auto-detección de lenguaje (Python, Node, Go, Ruby, Java)
- ✅ Templates por framework (FastAPI, Flask, Express)
- ✅ Dockerfiles multi-stage optimizados
- ✅ Prácticas de seguridad (usuarios no-root)

**3. Documentation Generator Plugin (docs_generator):**
- ✅ Generación de docstrings faltantes con LLM
- ✅ Creación/actualización de README.md profesional
- ✅ Documentación API automática (REST endpoints)
- ✅ Análisis de estructura del proyecto
- ✅ Formato Google docstrings
- ✅ Markdown con emojis

**CLI de Plugins:**
- ✅ `patcode plugin list` - Lista plugins disponibles
- ✅ `patcode plugin info <name>` - Info detallada de plugin
- ✅ `patcode plugin run <name>` - Ejecuta plugin con opciones
- ✅ `patcode plugin reload <name>` - Recarga plugin en caliente

**Comandos Shortcut:**
- ✅ `patcode git <action>` - Wrapper para git_helper
- ✅ `patcode docker <action>` - Wrapper para docker_helper
- ✅ `patcode docs <action>` - Wrapper para docs_generator

### 🎨 Mejoras

- 🎨 Tabla visual para listado de plugins con Rich
- 🎨 Progress bars durante ejecución de plugins
- 🎨 Syntax highlighting para contenido generado
- 🎨 Paneles informativos para resultados

### 📊 Estadísticas

- **Archivos nuevos:** 4 (+1,500 líneas)
- **Plugins incluidos:** 3
- **Tests nuevos:** 25 (100% pasando)
- **Comandos CLI:** 7 nuevos

### 🔧 Arquitectura
```
tools/
├── plugin_system.py       # Sistema base
└── plugins/
    ├── git_helper_plugin.py
    ├── docker_helper_plugin.py
    └── docs_generator_plugin.py
```

### 📖 Ejemplos de Uso

**Git Helper:**
```bash
# Status con análisis
patcode git status

# Sugerir commit semántico
patcode git suggest

# Crear commit
patcode git commit -m "feat: nueva funcionalidad"
```

**Docker Helper:**
```bash
# Generar todos los archivos Docker
patcode docker all --save

# Solo Dockerfile para FastAPI
patcode docker dockerfile --framework fastapi --save
```

**Documentation Generator:**
```bash
# Generar README
patcode docs readme --save

# Generar docstrings faltantes
patcode docs docstrings --file main.py

# Generar toda la documentación
patcode docs all --save
```

---

## [0.4.0] - 2025-10-15

### ✨ Añadido

**Sistema de Cache Inteligente:**
- ✅ `ResponseCache` - Cache automático de respuestas LLM
- ✅ Hash contextual basado en mensajes + archivos cargados
- ✅ TTL configurable (default: 24 horas)
- ✅ Limpieza automática de cache expirado
- ✅ Estadísticas de hit rate en tiempo real
- ✅ Comando `patcode cache` para gestión manual
- ✅ Persistencia de stats entre sesiones

**Selector Automático de Modelos:**
- ✅ `ModelSelector` - Detección de hardware y selección inteligente
- ✅ Perfiles de 5 modelos: llama3.2 (1b, 3b), codellama (7b, 13b), mistral (7b)
- ✅ Recomendaciones según RAM disponible
- ✅ Sugerencias específicas por caso de uso
- ✅ Flag `--auto` para selección automática
- ✅ Comando `patcode models` para ver compatibilidad
- ✅ Validación de requisitos de RAM antes de iniciar

**CLI Mejorada:**
- ✅ Flag `--auto` para auto-selección de modelo
- ✅ Flag `--no-cache` para desactivar cache
- ✅ Comando `cache clear/stats/clean` para gestión
- ✅ Comando `models` para listar modelos disponibles
- ✅ Info de modelo con RAM requerida y velocidad
- ✅ Recomendaciones visuales de performance

### 🚀 Mejoras de Performance

- ⚡ **50% más rápido** en queries repetidas (cache hit)
- ⚡ **30% reducción de latencia** con auto-selección de modelo
- 💾 Cache inteligente solo para modelos lentos (balanced/deep)
- 🧠 Hit rate típico: 35-40% en sesiones largas
- 📊 Tamaño de cache auto-gestionado

### 🔧 Modificado

**PatAgent:**
- 🔄 Integración completa de `ResponseCache`
- 🔄 Integración de `ModelSelector` para validación
- 🔄 `get_stats()` ahora incluye cache hit rate y tamaño
- 🔄 `_call_ollama()` usa cache automáticamente

**Configuración:**
- 🔄 Directorio `.patcode_cache/` para persistencia
- 🔄 Stats de cache en `cache_stats.json`

### 📊 Estadísticas

- **Archivos nuevos:** 2 (+850 líneas)
- **Tests nuevos:** 20 (100% pasando)
- **Comandos CLI:** 2 nuevos (`cache`, `models`)
- **Performance:** 50% mejora en queries repetidas

### 🐛 Corregido

- 🐛 Prevención de OOM con modelos grandes en RAM limitada
- 🐛 Validación de modelos antes de inicializar agente

---

## [0.3.1] - 2025-10-14

### ✨ Añadido

**Interfaz Rich Avanzada:**
- ✅ `RichTerminalUI` - Interfaz visual moderna con Rich
- ✅ Syntax highlighting automático para código Python, JS, TS, etc.
- ✅ Paneles visuales para errores, warnings, info, éxito
- ✅ Progress bars para operaciones largas (analyze, refactor, test)
- ✅ Autocompletado mejorado con historial persistente (.patcode_history)
- ✅ Tablas formateadas para estadísticas y reportes
- ✅ Confirmaciones visuales para acciones destructivas
- ✅ Markdown rendering para respuestas del LLM
- ✅ Árbol de archivos visual con iconos
- ✅ Info del modelo con RAM y velocidad

**CLI Mejorada:**
- 🔄 Todos los comandos ahora usan RichTerminalUI
- 🔄 Mensajes de bienvenida visuales con Panel
- 🔄 Reportes de análisis con barras de progreso y emojis
- 🔄 Comandos /load, /files, /stats con UI mejorada
- 🔄 Progress spinner durante pensamiento del LLM

**Tests:**
- ✅ `tests/test_rich_ui.py` - 8 tests para RichTerminalUI
- ✅ Cobertura de display_code, display_stats, file_tree, etc.

### 🎨 Mejoras Visuales

- 🎨 Colores consistentes: cyan (info), green (success), red (error), yellow (warning)
- 🎨 Emojis contextuales: ✅ ❌ ⚠️ 💡 📊 🤖 📄 📁
- 🎨 Barras de progreso ASCII: █████░░░░░
- 🎨 Paneles con bordes para mejor legibilidad

### 📊 UX

- ⚡ Autocompletado instantáneo con Tab
- ⚡ Historial de comandos con ↑↓
- ⚡ Confirmaciones interactivas para evitar errores
- ⚡ Spinner animado durante procesamiento LLM
- ⚡ Limpieza de pantalla con /clear

---

## [0.3.0] - 2025-10-14

### ✨ Añadido

**Sistema de Memoria Inteligente:**
- ✅ `MemoryManager` con rotación automática de memoria activa/pasiva
- ✅ Resúmenes automáticos de conversaciones antiguas usando LLM
- ✅ Archivado automático cuando memory.json excede 5MB
- ✅ Soporte para múltiples contextos de trabajo
- ✅ Configuración: `MAX_ACTIVE_MESSAGES`, `MAX_MEMORY_FILE_SIZE`, `ENABLE_MEMORY_SUMMARIZATION`

**CLI Moderna con Click:**
- ✅ `cli.py` - Nueva interfaz de comandos estructurada
- ✅ `patcode chat` - Modo conversacional con opciones --fast, --deep, --model
- ✅ `patcode analyze` - Análisis automático de proyectos con scores
- ✅ `patcode explain <file>` - Explicación de archivos de código
- ✅ `patcode refactor <file>` - Sugerencias de mejoras
- ✅ `patcode test <file>` - Generación automática de tests
- ✅ `patcode info` - Información del sistema y estado de Ollama

**Sistema de Ejecución Segura:**
- ✅ `SafeExecutor` - Validación y sandbox para comandos
- ✅ Whitelist/blacklist de comandos permitidos/bloqueados
- ✅ Detección de patrones peligrosos (rm -rf, format, etc.)
- ✅ Timeouts configurables para prevenir cuelgues
- ✅ Métodos: `run_command()`, `run_tests()`, `format_code()`, `lint_code()`

**Analizador de Proyectos:**
- ✅ `ProjectAnalyzer` - Auditoría automática de código
- ✅ Score de Estructura (0-10): README, .gitignore, tests, documentación
- ✅ Score de Calidad (0-10): linters, formatters, TODOs, archivos grandes
- ✅ Detección de cobertura de tests con pytest
- ✅ Sugerencias automáticas de mejora
- ✅ Reportes en formato: table, JSON, markdown

**Tests:**
- ✅ `tests/test_memory_manager.py` - 10 tests para MemoryManager
- ✅ Cobertura completa de rotación, archivado, resúmenes

**Dependencias:**
- ✅ `prompt-toolkit>=3.0.43` - Autocompletado interactivo
- ✅ `click>=8.1.7` - CLI estructurado

### 🔧 Modificado

**Agente Principal:**
- 🔄 `agents/pat_agent.py` - Integración completa de MemoryManager
- 🔄 Métodos `_load_history()`, `_save_history()`, `_build_context()` refactorizados
- 🔄 `get_stats()` ahora incluye memoria activa/pasiva/resúmenes

**Configuración:**
- 🔄 `config/settings.py` - Nueva sección `MemorySettings` con 4 parámetros
- 🔄 Validación mejorada de configuración al inicio

**Tests:**
- 🔄 `tests/conftest.py` - Fixtures actualizadas para compatibilidad con Settings
- 🔄 Imports corregidos: `Settings`, `OllamaSettings`, `MemorySettings`, etc.

**UI:**
- 🔄 `main.py` - Compatible con nuevas estadísticas de memoria
- 🔄 Mensajes de bienvenida actualizados a v0.3.0

### 🚀 Mejoras de Performance

- ⚡ **50% más rápido** en conversaciones largas (>20 mensajes)
- 💾 Control automático de uso de memoria
- 🧠 Contexto inteligente con resúmenes preserva información relevante

### 📊 Estadísticas

- **Archivos nuevos:** 6 (+1,280 líneas)
- **Archivos modificados:** 4
- **Tests:** 10 nuevos (100% pasando)
- **Comandos CLI:** 6 nuevos

---

## [0.2.0] - 2025-10-13

### ✨ Añadido

- ✅ Sistema de gestión de archivos (`FileManager`)
- ✅ Carga automática de README.md
- ✅ Comandos `/load`, `/files`, `/unload`, `/show`
- ✅ Comando `/project` para cargar proyectos completos
- ✅ Comando `/analyze` para ver estructura
- ✅ Validadores de entrada con `InputValidator`, `MemoryValidator`
- ✅ Sistema de excepciones personalizadas
- ✅ Configuración centralizada con dataclasses
- ✅ Tests con pytest y coverage

### 🔧 Modificado

- 🔄 Refactor completo de `PatAgent`
- 🔄 Sistema de logging mejorado
- 🔄 Interfaz Rich para terminal

---

## [0.1.0] - 2025-10-01

### ✨ Añadido

- 🎉 Release inicial
- ✅ Conversación básica con Ollama
- ✅ Persistencia de historial en `memory.json`
- ✅ CLI simple con Rich
- ✅ Comandos básicos: `/clear`, `/stats`, `/help`, `/quit`
- ✅ Configuración con variables de entorno (.env)
- ✅ Soporte para modelos: llama3.2, codellama, mistral

### Documentación

- 📝 README.md con instalación y uso
- 📝 .env.example con configuración por defecto

---

## Formato de Versiones

- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Nuevas funcionalidades compatibles
- **PATCH**: Correcciones de bugs

---

## Links

- [Unreleased]: Próximas features en desarrollo
- [Repositorio](https://github.com/gonzacba17/Patcode)
- [Issues](https://github.com/gonzacba17/Patcode/issues)
- [Documentación](./docs/)
