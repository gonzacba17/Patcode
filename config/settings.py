"""
Configuración general de PatCode
"""
import os
from pathlib import Path

# ============================================================================
# RUTAS DEL PROYECTO
# ============================================================================

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Directorio de memoria
MEMORY_DIR = BASE_DIR / "agents" / "memory"
MEMORY_FILE = MEMORY_DIR / "memory.json"
CONTEXT_CACHE_FILE = MEMORY_DIR / "context_cache.json"

# Directorio de trabajo actual (donde se ejecutan las operaciones)
WORKSPACE_DIR = os.getcwd()

# Crear directorios si no existen
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONFIGURACIÓN DE OLLAMA
# ============================================================================

# URL base de Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Modelo por defecto
# Opciones recomendadas:
# - llama3.2:latest (general, 3B parámetros)
# - qwen2.5-coder:7b (mejor para código)
# - qwen2.5-coder:32b (óptimo para coding, requiere más RAM)
# - deepseek-coder-v2:latest (excelente para coding)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# Timeout para requests a Ollama (en segundos)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

# ============================================================================
# CONFIGURACIÓN DEL AGENTE
# ============================================================================

# Número máximo de mensajes a mantener en el historial
# Nota: El system prompt siempre se conserva
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

# Habilitar streaming de respuestas (mostrar en tiempo real)
STREAM_RESPONSES = os.getenv("STREAM_RESPONSES", "true").lower() == "true"

# Modo verbose (mostrar logs detallados)
VERBOSE_MODE = os.getenv("VERBOSE_MODE", "false").lower() == "true"

# ============================================================================
# CONFIGURACIÓN DE HERRAMIENTAS
# ============================================================================

# Tamaño máximo de archivo a leer (en bytes)
# 1 MB = 1_000_000 bytes
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "5000000"))  # 5MB

# Extensiones de archivo permitidas para operaciones de escritura
ALLOWED_EXTENSIONS = [
    # Código
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.rb', '.php', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
    
    # Web
    '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
    
    # Configuración y datos
    '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.config',
    '.xml', '.env', '.properties',
    
    # Documentación
    '.md', '.txt', '.rst', '.adoc',
    
    # Scripts
    '.sh', '.bash', '.zsh', '.fish', '.bat', '.ps1',
    
    # SQL y bases de datos
    '.sql', '.prisma',
    
    # Otros
    '.gitignore', '.dockerignore', 'Dockerfile', 'Makefile', '.editorconfig'
]

# Extensiones de archivos binarios (no leer como texto)
BINARY_EXTENSIONS = [
    '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
    '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.db', '.sqlite', '.sqlite3'
]

# Directorios a ignorar al analizar proyectos
IGNORED_DIRECTORIES = [
    '__pycache__', '.git', '.svn', '.hg',
    'node_modules', 'venv', 'env', '.venv', '.env',
    'dist', 'build', '.next', '.nuxt',
    'target', 'bin', 'obj',
    '.idea', '.vscode', '.vs',
    'coverage', '.coverage', '.pytest_cache',
    '.mypy_cache', '.tox', '.nox'
]

# Archivos a ignorar
IGNORED_FILES = [
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    '*.log', '*.tmp', '*.temp', '*.swp', '*.swo',
    '*.lock', 'package-lock.json', 'yarn.lock', 'poetry.lock'
]

# ============================================================================
# SEGURIDAD
# ============================================================================

# Rutas bloqueadas (nunca accesibles)
BLOCKED_PATHS = [
    '/etc/passwd', '/etc/shadow', '/etc/sudoers',
    '~/.ssh', '~/.aws', '~/.config',
    '/proc', '/sys', '/dev',
    'C:\\Windows\\System32', 'C:\\Windows\\SysWOW64'
]

# Comandos bloqueados en ExecuteCommandTool
BLOCKED_COMMANDS = [
    'rm', 'rmdir', 'del', 'format', 'fdisk',
    'dd', 'mkfs', 'shutdown', 'reboot', 'halt',
    'kill', 'killall', 'pkill', 'sudo', 'su',
    'chmod +x /bin', 'chown root'
]

# Comandos permitidos (whitelist)
ALLOWED_COMMANDS = [
    # Navegación y exploración
    'ls', 'dir', 'pwd', 'cd', 'tree', 'find', 'which', 'whereis',
    
    # Lectura de archivos
    'cat', 'less', 'more', 'head', 'tail', 'grep', 'awk', 'sed',
    
    # Info del sistema
    'echo', 'date', 'whoami', 'hostname', 'uname', 'env',
    
    # Git
    'git',
    
    # Package managers y build tools
    'npm', 'yarn', 'pnpm', 'pip', 'pipenv', 'poetry',
    'cargo', 'go', 'mvn', 'gradle', 'make', 'cmake',
    
    # Compiladores y ejecutores
    'python', 'python3', 'node', 'deno', 'bun',
    'java', 'javac', 'gcc', 'g++', 'clang', 'rustc',
    
    # Testing
    'pytest', 'jest', 'mocha', 'vitest', 'cargo test',
    
    # Linters y formatters
    'eslint', 'prettier', 'black', 'flake8', 'pylint', 'mypy',
    'clippy', 'rustfmt',
    
    # Otros
    'wc', 'sort', 'uniq', 'diff', 'file', 'stat'
]

# ============================================================================
# ANÁLISIS DE CÓDIGO (Para Fase 3)
# ============================================================================

# Máximo de archivos a analizar en una sesión
MAX_FILES_TO_ANALYZE = int(os.getenv("MAX_FILES_TO_ANALYZE", "100"))

# Profundidad máxima de directorios a explorar
MAX_DIRECTORY_DEPTH = int(os.getenv("MAX_DIRECTORY_DEPTH", "10"))

# Habilitar caché de análisis
ENABLE_ANALYSIS_CACHE = os.getenv("ENABLE_ANALYSIS_CACHE", "true").lower() == "true"

# Tiempo de expiración del caché (en segundos)
CACHE_EXPIRATION_TIME = int(os.getenv("CACHE_EXPIRATION_TIME", "3600"))  # 1 hora

# ============================================================================
# UI Y PRESENTACIÓN
# ============================================================================

# Ancho de terminal para formateo
TERMINAL_WIDTH = int(os.getenv("TERMINAL_WIDTH", "80"))

# Colores habilitados
ENABLE_COLORS = os.getenv("ENABLE_COLORS", "true").lower() == "true"

# Mostrar banner de inicio
SHOW_BANNER = os.getenv("SHOW_BANNER", "true").lower() == "true"

# ============================================================================
# LOGGING
# ============================================================================

# Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Archivo de log
LOG_FILE = BASE_DIR / "patcode.log"

# Habilitar logging a archivo
ENABLE_FILE_LOGGING = os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"

# ============================================================================
# CARACTERÍSTICAS EXPERIMENTALES
# ============================================================================

# Habilitar búsqueda semántica (requiere embeddings)
ENABLE_SEMANTIC_SEARCH = os.getenv("ENABLE_SEMANTIC_SEARCH", "false").lower() == "true"

# Habilitar análisis estático de código
ENABLE_STATIC_ANALYSIS = os.getenv("ENABLE_STATIC_ANALYSIS", "false").lower() == "true"

# Habilitar auto-complete en CLI
ENABLE_AUTOCOMPLETE = os.getenv("ENABLE_AUTOCOMPLETE", "true").lower() == "true"

# ============================================================================
# VALIDACIÓN
# ============================================================================

def validate_config():
    """Valida la configuración al inicio"""
    errors = []
    
    # Verificar que existan los directorios necesarios
    if not MEMORY_DIR.exists():
        try:
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"No se pudo crear el directorio de memoria: {e}")
    
    # Verificar permisos de escritura
    if not os.access(MEMORY_DIR, os.W_OK):
        errors.append(f"Sin permisos de escritura en: {MEMORY_DIR}")
    
    # Verificar valores numéricos
    if MAX_HISTORY_MESSAGES < 1:
        errors.append("MAX_HISTORY_MESSAGES debe ser mayor a 0")
    
    if REQUEST_TIMEOUT < 10:
        errors.append("REQUEST_TIMEOUT debe ser al menos 10 segundos")
    
    if MAX_FILE_SIZE < 1000:
        errors.append("MAX_FILE_SIZE debe ser al menos 1000 bytes")
    
    return errors

# Validar al importar
_config_errors = validate_config()
if _config_errors:
    print("⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
    for error in _config_errors:
        print(f"  - {error}")