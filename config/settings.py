"""
Configuración general de PatCode

Este módulo centraliza toda la configuración del proyecto usando dataclasses.
Todas las configuraciones están accesibles a través de la instancia global 'settings'.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

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
WORKSPACE_DIR = Path(os.getcwd())

# Crear directorios si no existen
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DATACLASSES DE CONFIGURACIÓN
# ============================================================================

@dataclass
class OllamaSettings:
    """Configuración del servidor Ollama y modelo LLM"""
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))


@dataclass
class MemorySettings:
    """Configuración de persistencia y memoria del agente"""
    path: Path = MEMORY_FILE
    max_size: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    context_size: int = int(os.getenv("CONTEXT_WINDOW_SIZE", "10"))
    directory: Path = MEMORY_DIR
    context_cache_path: Path = CONTEXT_CACHE_FILE


@dataclass
class ValidationSettings:
    """Configuración de validaciones y límites"""
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "5000000"))  # 5MB
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
    max_files_to_analyze: int = int(os.getenv("MAX_FILES_TO_ANALYZE", "100"))
    max_directory_depth: int = int(os.getenv("MAX_DIRECTORY_DEPTH", "10"))
    # AGREGADO: Límites de longitud de prompt
    min_prompt_length: int = int(os.getenv("MIN_PROMPT_LENGTH", "1"))
    max_prompt_length: int = int(os.getenv("MAX_PROMPT_LENGTH", "10000"))


@dataclass
class LoggingSettings:
    """Configuración del sistema de logging"""
    file: bool = os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
    filename: str = os.getenv("LOG_FILE", str(BASE_DIR / "patcode.log"))
    level: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class PathSettings:
    """Rutas importantes del proyecto"""
    base_dir: Path = BASE_DIR
    memory_dir: Path = MEMORY_DIR
    memory_file: Path = MEMORY_FILE
    context_cache_file: Path = CONTEXT_CACHE_FILE
    workspace_dir: Path = WORKSPACE_DIR
    log_file: Path = BASE_DIR / "patcode.log"


@dataclass
class FileSettings:
    """Configuración de operaciones con archivos"""
    # Extensiones de archivo permitidas para operaciones de escritura
    allowed_extensions: List[str] = field(default_factory=lambda: [
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
    ])
    
    # Extensiones de archivos binarios (no leer como texto)
    binary_extensions: List[str] = field(default_factory=lambda: [
        '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
        '.mp3', '.mp4', '.avi', '.mov', '.wav',
        '.db', '.sqlite', '.sqlite3'
    ])
    
    # Directorios a ignorar al analizar proyectos
    ignored_directories: List[str] = field(default_factory=lambda: [
        '__pycache__', '.git', '.svn', '.hg',
        'node_modules', 'venv', 'env', '.venv', '.env',
        'dist', 'build', '.next', '.nuxt',
        'target', 'bin', 'obj',
        '.idea', '.vscode', '.vs',
        'coverage', '.coverage', '.pytest_cache',
        '.mypy_cache', '.tox', '.nox'
    ])
    
    # Archivos a ignorar
    ignored_files: List[str] = field(default_factory=lambda: [
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        '*.log', '*.tmp', '*.temp', '*.swp', '*.swo',
        '*.lock', 'package-lock.json', 'yarn.lock', 'poetry.lock'
    ])


@dataclass
class SecuritySettings:
    """Configuración de seguridad y restricciones"""
    # Rutas bloqueadas (nunca accesibles)
    blocked_paths: List[str] = field(default_factory=lambda: [
        '/etc/passwd', '/etc/shadow', '/etc/sudoers',
        '~/.ssh', '~/.aws', '~/.config',
        '/proc', '/sys', '/dev',
        'C:\\Windows\\System32', 'C:\\Windows\\SysWOW64'
    ])
    
    # Comandos bloqueados en ExecuteCommandTool
    blocked_commands: List[str] = field(default_factory=lambda: [
        'rm', 'rmdir', 'del', 'format', 'fdisk',
        'dd', 'mkfs', 'shutdown', 'reboot', 'halt',
        'kill', 'killall', 'pkill', 'sudo', 'su',
        'chmod +x /bin', 'chown root'
    ])
    
    # Comandos permitidos (whitelist)
    allowed_commands: List[str] = field(default_factory=lambda: [
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
    ])


@dataclass
class AnalysisSettings:
    """Configuración para análisis de código"""
    enable_cache: bool = os.getenv("ENABLE_ANALYSIS_CACHE", "true").lower() == "true"
    cache_expiration_time: int = int(os.getenv("CACHE_EXPIRATION_TIME", "3600"))  # 1 hora
    enable_semantic_search: bool = os.getenv("ENABLE_SEMANTIC_SEARCH", "false").lower() == "true"
    enable_static_analysis: bool = os.getenv("ENABLE_STATIC_ANALYSIS", "false").lower() == "true"


@dataclass
class UISettings:
    """Configuración de interfaz de usuario"""
    terminal_width: int = int(os.getenv("TERMINAL_WIDTH", "80"))
    enable_colors: bool = os.getenv("ENABLE_COLORS", "true").lower() == "true"
    show_banner: bool = os.getenv("SHOW_BANNER", "true").lower() == "true"
    stream_responses: bool = os.getenv("STREAM_RESPONSES", "true").lower() == "true"
    verbose_mode: bool = os.getenv("VERBOSE_MODE", "false").lower() == "true"
    enable_autocomplete: bool = os.getenv("ENABLE_AUTOCOMPLETE", "true").lower() == "true"


@dataclass
class Settings:
    """
    Configuración central de PatCode.
    
    Esta clase agrupa todas las configuraciones del proyecto en un solo objeto.
    Accede a las diferentes secciones como:
    - settings.ollama.model
    - settings.memory.path
    - settings.logging.level
    - settings.validation.max_file_size
    - settings.paths.base_dir
    - settings.files.allowed_extensions
    - settings.security.blocked_commands
    - settings.analysis.enable_cache
    - settings.ui.enable_colors
    """
    ollama: OllamaSettings = field(default_factory=OllamaSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    paths: PathSettings = field(default_factory=PathSettings)
    files: FileSettings = field(default_factory=FileSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    analysis: AnalysisSettings = field(default_factory=AnalysisSettings)
    ui: UISettings = field(default_factory=UISettings)


# ============================================================================
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# ============================================================================

# Esta es la instancia que se debe importar en todo el proyecto
settings = Settings()


# ============================================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================================

def validate_config():
    """
    Valida la configuración al inicio.
    
    Verifica que:
    - Los directorios necesarios existan o se puedan crear
    - Los permisos sean correctos
    - Los valores numéricos estén en rangos válidos
    
    Returns:
        Lista de errores encontrados (vacía si todo está OK)
    """
    errors = []
    
    # Verificar que existan los directorios necesarios
    if not settings.memory.directory.exists():
        try:
            settings.memory.directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"No se pudo crear el directorio de memoria: {e}")
    
    # Verificar permisos de escritura
    if not os.access(settings.memory.directory, os.W_OK):
        errors.append(f"Sin permisos de escritura en: {settings.memory.directory}")
    
    # Verificar valores numéricos
    if settings.validation.max_history_messages < 1:
        errors.append("MAX_HISTORY_MESSAGES debe ser mayor a 0")
    
    if settings.validation.request_timeout < 10:
        errors.append("REQUEST_TIMEOUT debe ser al menos 10 segundos")
    
    if settings.validation.max_file_size < 1000:
        errors.append("MAX_FILE_SIZE debe ser al menos 1000 bytes")
    
    return errors


# Validar al importar el módulo
_config_errors = validate_config()
if _config_errors:
    print("⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
    for error in _config_errors:
        print(f"  - {error}")


# ============================================================================
# EXPORTS PARA COMPATIBILIDAD
# ============================================================================

# Estas constantes se mantienen para compatibilidad con código legacy
# pero se recomienda usar settings.* en su lugar

OLLAMA_BASE_URL = settings.ollama.base_url
OLLAMA_MODEL = settings.ollama.model
REQUEST_TIMEOUT = settings.ollama.timeout

MAX_HISTORY_MESSAGES = settings.validation.max_history_messages
MAX_FILE_SIZE = settings.validation.max_file_size
MAX_FILES_TO_ANALYZE = settings.validation.max_files_to_analyze
MAX_DIRECTORY_DEPTH = settings.validation.max_directory_depth

LOG_LEVEL = settings.logging.level
LOG_FILE = settings.paths.log_file
ENABLE_FILE_LOGGING = settings.logging.file

STREAM_RESPONSES = settings.ui.stream_responses
VERBOSE_MODE = settings.ui.verbose_mode
TERMINAL_WIDTH = settings.ui.terminal_width
ENABLE_COLORS = settings.ui.enable_colors
SHOW_BANNER = settings.ui.show_banner
ENABLE_AUTOCOMPLETE = settings.ui.enable_autocomplete

ALLOWED_EXTENSIONS = settings.files.allowed_extensions
BINARY_EXTENSIONS = settings.files.binary_extensions
IGNORED_DIRECTORIES = settings.files.ignored_directories
IGNORED_FILES = settings.files.ignored_files

BLOCKED_PATHS = settings.security.blocked_paths
BLOCKED_COMMANDS = settings.security.blocked_commands
ALLOWED_COMMANDS = settings.security.allowed_commands

ENABLE_ANALYSIS_CACHE = settings.analysis.enable_cache
CACHE_EXPIRATION_TIME = settings.analysis.cache_expiration_time
ENABLE_SEMANTIC_SEARCH = settings.analysis.enable_semantic_search
ENABLE_STATIC_ANALYSIS = settings.analysis.enable_static_analysis