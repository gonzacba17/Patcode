"""
Configuración general de PatCode
"""
import os
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "agents" / "memory"
MEMORY_FILE = MEMORY_DIR / "memory.json"

# Configuración de Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"  # Cambiar por qwen2.5-coder:32b o deepseek-coder-v2

# Configuración del agente
MAX_HISTORY_MESSAGES = 10  # Aumentado de 5 a 10
STREAM_RESPONSES = True     # Habilitar streaming
REQUEST_TIMEOUT = 120       # Timeout en segundos

# Configuración de herramientas
WORKSPACE_DIR = os.getcwd()  # Directorio de trabajo actual
MAX_FILE_SIZE = 1_000_000    # 1MB máximo por archivo
ALLOWED_EXTENSIONS = [
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h',
    '.css', '.html', '.json', '.yaml', '.yml', '.md', '.txt', '.rs',
    '.go', '.rb', '.php', '.sh', '.bash'
]

# Seguridad
BLOCKED_PATHS = [
    '/etc/passwd', '/etc/shadow', '~/.ssh', '~/.aws',
    '/proc', '/sys', '/dev'
]

# Crear directorio de memoria si no existe
MEMORY_DIR.mkdir(parents=True, exist_ok=True)