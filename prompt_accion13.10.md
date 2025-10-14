# 🎯 PROMPT DE ACCIÓN - PATCODE SPRINT 1
## Plan de Estabilización y Fundamentos (Semanas 1-2)

---

## 📋 CONTEXTO DEL PROYECTO

### Estado Actual
**PatCode** es un asistente de programación local (alternativa offline a Claude Code) que usa Ollama. El proyecto está en fase **MVP funcional** con:

- ✅ Chat básico funcionando
- ✅ Integración con Ollama completada
- ✅ Sistema de memoria simple implementado
- ❌ **Sin tests** (0% coverage)
- ❌ **Sin manejo de errores robusto**
- ❌ **Sin arquitectura escalable**

**Score actual: 4.2/10** - Necesita maduración técnica urgente.

### Problemas Críticos Identificados

1. **Seguridad y Configuración**:
   - Sin `.gitignore` → Riesgo de exponer `memory.json`
   - URLs y rutas hardcoded
   - Sin variables de entorno
   - Sin validación de inputs

2. **Robustez**:
   - No maneja errores de red/Ollama
   - No maneja `Ctrl+C` gracefully
   - Sin timeouts en requests
   - Puede crashear fácilmente

3. **Calidad de Código**:
   - Magic numbers (`history[-5:]`)
   - Sin abstracción de servicios
   - Alto acoplamiento
   - Dependencias sin versionar

---

## 🎯 OBJETIVO DEL SPRINT 1

**Convertir el MVP en una herramienta estable y testeable en 10 días**

### Metas Medibles:
- ✅ 0 crashes con inputs válidos
- ✅ Manejo elegante de errores de red
- ✅ 40-50% test coverage
- ✅ Configuración con `.env`
- ✅ CI/CD básico funcionando

---

## 📅 PLAN DE EJECUCIÓN - 10 DÍAS

### 🔴 DÍA 1-2: SEGURIDAD Y CONFIGURACIÓN BÁSICA

#### Tareas:

**1. Crear estructura de configuración segura**

```bash
# Archivos a crear
touch .gitignore
touch .env.example
touch config.py
```

**`.gitignore`**:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Datos sensibles
data/
memory/
*.json
!**/example.json
*.log

# Configuración
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

**`.env.example`**:
```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
REQUEST_TIMEOUT=60

# Memory Configuration
MEMORY_PATH=./data/memory/memory.json
CONTEXT_WINDOW_SIZE=5
MAX_MEMORY_SIZE=1000

# Validation
MAX_PROMPT_LENGTH=10000
MIN_PROMPT_LENGTH=1

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/patcode.log
```

**2. Crear `config.py` para centralizar configuración**

```python
# config.py
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

@dataclass
class OllamaConfig:
    """Configuración de Ollama."""
    base_url: str
    model: str
    timeout: int
    
    @classmethod
    def from_env(cls):
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
            timeout=int(os.getenv("REQUEST_TIMEOUT", "60"))
        )

@dataclass
class MemoryConfig:
    """Configuración de memoria."""
    path: Path
    context_size: int
    max_size: int
    
    @classmethod
    def from_env(cls):
        return cls(
            path=Path(os.getenv("MEMORY_PATH", "./data/memory/memory.json")),
            context_size=int(os.getenv("CONTEXT_WINDOW_SIZE", "5")),
            max_size=int(os.getenv("MAX_MEMORY_SIZE", "1000"))
        )

@dataclass
class ValidationConfig:
    """Configuración de validación."""
    max_prompt_length: int
    min_prompt_length: int
    
    @classmethod
    def from_env(cls):
        return cls(
            max_prompt_length=int(os.getenv("MAX_PROMPT_LENGTH", "10000")),
            min_prompt_length=int(os.getenv("MIN_PROMPT_LENGTH", "1"))
        )

@dataclass
class LoggingConfig:
    """Configuración de logging."""
    level: str
    file: Optional[Path]
    
    @classmethod
    def from_env(cls):
        log_file = os.getenv("LOG_FILE")
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=Path(log_file) if log_file else None
        )

@dataclass
class Settings:
    """Configuración global de PatCode."""
    ollama: OllamaConfig
    memory: MemoryConfig
    validation: ValidationConfig
    logging: LoggingConfig
    
    @classmethod
    def load(cls):
        """Cargar configuración desde variables de entorno."""
        return cls(
            ollama=OllamaConfig.from_env(),
            memory=MemoryConfig.from_env(),
            validation=ValidationConfig.from_env(),
            logging=LoggingConfig.from_env()
        )

# Instancia global de configuración
settings = Settings.load()
```

**3. Actualizar `requirements.txt`**

```txt
# Core dependencies
requests>=2.31.0,<3.0.0
python-dotenv>=1.0.0,<2.0.0

# CLI improvements
rich>=13.7.0,<14.0.0

# Utils
pyyaml>=6.0.1,<7.0.0
```

**Verificación Día 1-2**:
```bash
# Debe funcionar sin crashes
python main.py  # Debe cargar config desde .env
cat .env.example  # Debe existir
git status  # memory.json no debe aparecer
```

---

### 🟠 DÍA 3-4: MANEJO ROBUSTO DE ERRORES

#### Tareas:

**1. Crear módulo de excepciones personalizadas**

```python
# src/exceptions.py
class PatCodeError(Exception):
    """Excepción base para PatCode."""
    pass

class OllamaConnectionError(PatCodeError):
    """Error al conectar con Ollama."""
    pass

class OllamaTimeoutError(PatCodeError):
    """Timeout al esperar respuesta de Ollama."""
    pass

class OllamaModelNotFoundError(PatCodeError):
    """Modelo no encontrado en Ollama."""
    pass

class InvalidPromptError(PatCodeError):
    """Prompt inválido o vacío."""
    pass

class MemoryError(PatCodeError):
    """Error al leer/escribir memoria."""
    pass

class ConfigurationError(PatCodeError):
    """Error en la configuración."""
    pass
```

**2. Crear validador de inputs**

```python
# src/validators.py
from config import settings
from exceptions import InvalidPromptError

class InputValidator:
    """Validador de inputs del usuario."""
    
    @staticmethod
    def validate_prompt(prompt: str) -> str:
        """
        Valida un prompt del usuario.
        
        Args:
            prompt: Texto ingresado por el usuario
            
        Returns:
            Prompt limpio y validado
            
        Raises:
            InvalidPromptError: Si el prompt es inválido
        """
        # Limpiar espacios
        prompt = prompt.strip()
        
        # Validar longitud mínima
        if len(prompt) < settings.validation.min_prompt_length:
            raise InvalidPromptError("El prompt no puede estar vacío")
        
        # Validar longitud máxima
        if len(prompt) > settings.validation.max_prompt_length:
            raise InvalidPromptError(
                f"El prompt excede el límite de {settings.validation.max_prompt_length} caracteres"
            )
        
        # Validar caracteres peligrosos (opcional)
        dangerous_chars = ['\x00', '\x1a']
        if any(char in prompt for char in dangerous_chars):
            raise InvalidPromptError("El prompt contiene caracteres no permitidos")
        
        return prompt
```

**3. Refactorizar `pat_agent.py` con manejo de errores**

```python
# agents/pat_agent.py (REFACTORIZADO)
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
import logging

from config import settings
from exceptions import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    MemoryError,
    InvalidPromptError
)
from validators import InputValidator

# Configurar logger
logger = logging.getLogger(__name__)

class PatAgent:
    """Agente de programación asistido por LLM."""
    
    def __init__(self):
        """Inicializa el agente."""
        self.history: List[Dict[str, str]] = []
        self.memory_path = settings.memory.path
        self.ollama_url = f"{settings.ollama.base_url}/api/generate"
        self.model = settings.ollama.model
        self.timeout = settings.ollama.timeout
        
        # Crear directorio de memoria si no existe
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar historial
        self._load_history()
        
        logger.info(f"PatAgent inicializado con modelo {self.model}")
    
    def _load_history(self) -> None:
        """Carga el historial desde el archivo de memoria."""
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                logger.info(f"Historial cargado: {len(self.history)} mensajes")
            else:
                self.history = []
                logger.info("Iniciando con historial vacío")
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON: {e}")
            raise MemoryError(f"Archivo de memoria corrupto: {e}")
        except Exception as e:
            logger.error(f"Error al cargar historial: {e}")
            raise MemoryError(f"No se pudo cargar la memoria: {e}")
    
    def _save_history(self) -> None:
        """Guarda el historial en el archivo de memoria."""
        try:
            # Limitar tamaño del historial
            if len(self.history) > settings.memory.max_size:
                self.history = self.history[-settings.memory.max_size:]
                logger.warning(f"Historial truncado a {settings.memory.max_size} mensajes")
            
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            logger.debug("Historial guardado exitosamente")
        except Exception as e:
            logger.error(f"Error al guardar historial: {e}")
            raise MemoryError(f"No se pudo guardar la memoria: {e}")
    
    def _build_context(self) -> str:
        """
        Construye el contexto para el LLM basándose en el historial reciente.
        
        Returns:
            String con el contexto formateado
        """
        context_size = settings.memory.context_size
        recent_history = self.history[-context_size:] if len(self.history) > 0 else []
        
        context = "Eres Pat, un asistente de programación experto.\n\n"
        
        if recent_history:
            context += "Conversación reciente:\n"
            for msg in recent_history:
                role = "Usuario" if msg["role"] == "user" else "Asistente"
                context += f"{role}: {msg['content']}\n"
        
        return context
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Llama a Ollama para generar una respuesta.
        
        Args:
            prompt: Prompt a enviar a Ollama
            
        Returns:
            Respuesta generada por el modelo
            
        Raises:
            OllamaConnectionError: Si no se puede conectar
            OllamaTimeoutError: Si se excede el timeout
            OllamaModelNotFoundError: Si el modelo no existe
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            logger.debug(f"Enviando request a Ollama: {self.ollama_url}")
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=self.timeout
            )
            
            # Verificar status code
            if response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Modelo '{self.model}' no encontrado. "
                    f"Ejecuta: ollama pull {self.model}"
                )
            
            response.raise_for_status()
            
            # Extraer respuesta
            result = response.json()
            answer = result.get("response", "")
            
            if not answer:
                logger.warning("Ollama devolvió respuesta vacía")
                return "Lo siento, no pude generar una respuesta."
            
            logger.debug(f"Respuesta recibida: {len(answer)} caracteres")
            return answer
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout después de {self.timeout}s")
            raise OllamaTimeoutError(
                f"Ollama no respondió en {self.timeout} segundos. "
                f"Aumenta REQUEST_TIMEOUT en .env"
            )
        except requests.exceptions.ConnectionError:
            logger.error("No se pudo conectar con Ollama")
            raise OllamaConnectionError(
                "No se pudo conectar con Ollama. "
                "Verifica que esté corriendo: ollama serve"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en request: {e}")
            raise OllamaConnectionError(f"Error al comunicarse con Ollama: {e}")
    
    def ask(self, prompt: str) -> str:
        """
        Procesa una pregunta del usuario y devuelve la respuesta.
        
        Args:
            prompt: Pregunta o comando del usuario
            
        Returns:
            Respuesta del asistente
            
        Raises:
            InvalidPromptError: Si el prompt es inválido
            OllamaConnectionError: Si hay problemas con Ollama
            MemoryError: Si hay problemas guardando la memoria
        """
        # Validar input
        try:
            prompt = InputValidator.validate_prompt(prompt)
        except InvalidPromptError as e:
            logger.warning(f"Prompt inválido: {e}")
            raise
        
        # Agregar pregunta al historial
        self.history.append({"role": "user", "content": prompt})
        
        try:
            # Construir contexto y llamar a Ollama
            context = self._build_context()
            full_prompt = f"{context}\nUsuario: {prompt}\nAsistente:"
            
            answer = self._call_ollama(full_prompt)
            
            # Agregar respuesta al historial
            self.history.append({"role": "assistant", "content": answer})
            
            # Guardar memoria
            self._save_history()
            
            return answer
            
        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError) as e:
            # Revertir el último mensaje del usuario si falló
            self.history.pop()
            logger.error(f"Error al procesar pregunta: {e}")
            raise
        except Exception as e:
            # Error inesperado
            self.history.pop()
            logger.exception("Error inesperado al procesar pregunta")
            raise PatCodeError(f"Error inesperado: {e}")
    
    def clear_history(self) -> None:
        """Limpia el historial de conversación."""
        self.history = []
        self._save_history()
        logger.info("Historial limpiado")
```

**4. Refactorizar `main.py` con manejo de errores**

```python
# main.py (REFACTORIZADO)
import sys
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from agents.pat_agent import PatAgent
from config import settings
from exceptions import (
    PatCodeError,
    OllamaConnectionError,
    OllamaTimeoutError,
    InvalidPromptError
)

# Configurar logging
def setup_logging():
    """Configura el sistema de logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Crear directorio de logs si no existe
    if settings.logging.file:
        settings.logging.file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=settings.logging.level,
            format=log_format,
            handlers=[
                logging.FileHandler(settings.logging.file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=settings.logging.level,
            format=log_format
        )

console = Console()
logger = logging.getLogger(__name__)

def print_welcome():
    """Muestra el mensaje de bienvenida."""
    welcome_text = """
    [bold cyan]PatCode - Asistente de Programación Local[/bold cyan]
    
    Comandos especiales:
    - [yellow]/clear[/yellow]: Limpiar historial
    - [yellow]/quit[/yellow] o [yellow]/exit[/yellow]: Salir
    - [yellow]Ctrl+C[/yellow]: Salir
    
    Modelo: [green]{model}[/green]
    """.format(model=settings.ollama.model)
    
    console.print(Panel(welcome_text, border_style="cyan"))

def main():
    """Función principal del CLI."""
    setup_logging()
    logger.info("Iniciando PatCode")
    
    try:
        # Inicializar agente
        agent = PatAgent()
        print_welcome()
        
        # Loop principal
        while True:
            try:
                # Obtener input del usuario
                prompt = Prompt.ask("\n[bold green]Tú[/bold green]")
                
                # Comandos especiales
                if prompt.lower() in ["/quit", "/exit"]:
                    console.print("[yellow]¡Hasta luego![/yellow]")
                    break
                
                if prompt.lower() == "/clear":
                    agent.clear_history()
                    console.print("[yellow]Historial limpiado[/yellow]")
                    continue
                
                # Procesar pregunta
                with console.status("[bold yellow]Pat está pensando...[/bold yellow]"):
                    answer = agent.ask(prompt)
                
                # Mostrar respuesta
                console.print(f"\n[bold cyan]Pat:[/bold cyan] {answer}")
                
            except InvalidPromptError as e:
                console.print(f"[yellow]⚠️  {e}[/yellow]")
            
            except OllamaTimeoutError as e:
                console.print(f"[red]⏱️  {e}[/red]")
                console.print("[yellow]Tip: Aumenta REQUEST_TIMEOUT en .env[/yellow]")
            
            except OllamaConnectionError as e:
                console.print(f"[red]🔌 {e}[/red]")
                console.print("[yellow]Tip: Verifica que Ollama esté corriendo[/yellow]")
                retry = Prompt.ask("¿Intentar de nuevo?", choices=["s", "n"], default="s")
                if retry == "n":
                    break
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrumpido por el usuario[/yellow]")
                save = Prompt.ask("¿Guardar historial antes de salir?", choices=["s", "n"], default="s")
                if save == "s":
                    try:
                        agent._save_history()
                        console.print("[green]✓ Historial guardado[/green]")
                    except Exception as e:
                        console.print(f"[red]✗ Error al guardar: {e}[/red]")
                break
            
            except PatCodeError as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                logger.exception("Error manejado en main loop")
            
            except Exception as e:
                console.print(f"[red]💥 Error inesperado: {e}[/red]")
                logger.exception("Error no manejado en main loop")
                console.print("[yellow]Por favor reporta este error en GitHub[/yellow]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Saliendo...[/yellow]")
        sys.exit(0)
    
    except Exception as e:
        console.print(f"[red]💥 Error fatal: {e}[/red]")
        logger.exception("Error fatal al inicializar")
        sys.exit(1)
    
    logger.info("PatCode finalizado")

if __name__ == "__main__":
    main()
```

**Verificación Día 3-4**:
```bash
# 1. Debe manejar Ollama apagado
python main.py
# > Input: "hola"
# > Debe mostrar: "No se pudo conectar con Ollama..."

# 2. Debe manejar Ctrl+C
python main.py
# > Presionar Ctrl+C
# > Debe preguntar si guardar historial

# 3. Debe validar inputs
python main.py
# > Input: "" (vacío)
# > Debe mostrar: "El prompt no puede estar vacío"

# 4. Debe funcionar normalmente
ollama serve  # En otra terminal
python main.py
# > Input: "Explica qué es Python"
# > Debe responder sin crashes
```

---

### 🟡 DÍA 5-6: SETUP DE TESTING

#### Tareas:

**1. Crear `requirements-dev.txt`**

```txt
# Testing
pytest>=7.4.3
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-timeout>=2.2.0

# Code quality
black>=23.12.0
isort>=5.13.2
flake8>=6.1.0
mypy>=1.7.1

# Security
bandit>=1.7.6

# Tools
pre-commit>=3.6.0
```

**2. Crear estructura de tests**

```bash
mkdir -p tests/{unit,integration}
touch tests/__init__.py
touch tests/conftest.py
touch tests/unit/__init__.py
touch tests/unit/test_pat_agent.py
touch tests/unit/test_validators.py
touch tests/unit/test_config.py
touch tests/integration/__init__.py
touch tests/integration/test_full_flow.py
```

**3. Crear fixtures en `conftest.py`**

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import json

from config import Settings, OllamaConfig, MemoryConfig, ValidationConfig, LoggingConfig

@pytest.fixture
def temp_memory_file(tmp_path):
    """Crea un archivo temporal de memoria para tests."""
    memory_file = tmp_path / "test_memory.json"
    return memory_file

@pytest.fixture
def mock_ollama_config():
    """Mock de configuración de Ollama."""
    return OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3.2:latest",
        timeout=30
    )

@pytest.fixture
def mock_memory_config(temp_memory_file):
    """Mock de configuración de memoria."""
    return MemoryConfig(
        path=temp_memory_file,
        context_size=5,
        max_size=100
    )

@pytest.fixture
def mock_validation_config():
    """Mock de configuración de validación."""
    return ValidationConfig(
        max_prompt_length=10000,
        min_prompt_length=1
    )

@pytest.fixture
def mock_logging_config(tmp_path):
    """Mock de configuración de logging."""
    log_file = tmp_path / "test.log"
    return LoggingConfig(
        level="DEBUG",
        file=log_file
    )

@pytest.fixture
def mock_settings(mock_ollama_config, mock_memory_config, mock_validation_config, mock_logging_config):
    """Mock de settings completo."""
    return Settings(
        ollama=mock_ollama_config,
        memory=mock_memory_config,
        validation=mock_validation_config,
        logging=mock_logging_config
    )

@pytest.fixture
def mock_requests_post(mocker):
    """Mock de requests.post para simular respuestas de Ollama."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "Esta es una respuesta de prueba"
    }
    mock_post = mocker.patch('requests.post', return_value=mock_response)
    return mock_post
```

**4. Crear primeros tests unitarios**

```python
# tests/unit/test_validators.py
import pytest
from validators import InputValidator
from exceptions import InvalidPromptError

class TestInputValidator:
    """Tests para el validador de inputs."""
    
    def test_validate_prompt_normal(self):
        """Test: prompt válido normal."""
        prompt = "Explica qué es Python"
        result = InputValidator.validate_prompt(prompt)
        assert result == "Explica qué es Python"
    
    def test_validate_prompt_with_whitespace(self):
        """Test: prompt con espacios al inicio y final."""
        prompt = "  Hola mundo  "
        result = InputValidator.validate_prompt(prompt)
        assert result == "Hola mundo"
    
    def test_validate_prompt_empty_raises_error(self):
        """Test: prompt vacío debe lanzar error."""
        with pytest.raises(InvalidPromptError, match="no puede estar vacío"):
            InputValidator.validate_prompt("")
    
    def test_validate_prompt_only_spaces_raises_error(self):
        """Test: prompt solo con espacios debe lanzar error."""
        with pytest.raises(InvalidPromptError):
            InputValidator.validate_prompt("   ")
    
    def test_validate_prompt_too_long_raises_error(self, monkeypatch):
        """Test: prompt muy largo debe lanzar error."""
        # Simular configuración con límite bajo
        from config import settings
        monkeypatch.setattr(settings.validation, 'max_prompt_length', 50)
        
        long_prompt = "a" * 100
        with pytest.raises(InvalidPromptError, match="excede el límite"):
            InputValidator.validate_prompt(long_prompt)
    
    def test_validate_prompt_dangerous_chars_raises_error(self):
        """Test: prompt con caracteres peligrosos debe lanzar error."""
        prompt = "Hola\x00mundo"
        with pytest.raises(InvalidPromptError, match="no permitidos"):
            InputValidator.validate_prompt(prompt)


# tests/unit/test_config.py
import os
import pytest
from config import OllamaConfig, MemoryConfig, Settings

class TestOllamaConfig:
    """Tests para configuración de Ollama."""
    
    def test_ollama_config_from_env_with_defaults(self, monkeypatch):
        """Test: carga config con valores por defecto."""
        # Limpiar variables de entorno
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        
        config = OllamaConfig.from_env()
        
        assert config.base_url == "http://localhost:11434"
        assert config.model == "llama3.2:latest"
        assert config.timeout == 60
    
    def test_ollama_config_from_env_with_custom(self, monkeypatch):
        """Test: carga config con valores custom."""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:8000")
        monkeypatch.setenv("OLLAMA_MODEL", "mistral:latest")
        monkeypatch.setenv("REQUEST_TIMEOUT", "120")
        
        config = OllamaConfig.from_env()
        
        assert config.base_url == "http://custom:8000"
        assert config.model == "mistral:latest"
        assert config.timeout == 120


# tests/unit/test_pat_agent.py
import pytest
import json
from unittest.mock import Mock, patch
from agents.pat_agent import PatAgent
from exceptions import (
    InvalidPromptError,
    OllamaConnectionError,
    OllamaTimeoutError,
    MemoryError
)

class TestPatAgent:
    """Tests para PatAgent."""
    
    @pytest.fixture
    def agent(self, mock_settings, monkeypatch):
        """Fixture que crea un agente para testing."""
        monkeypatch.setattr('config.settings', mock_settings)
        return PatAgent()
    
    def test_init_creates_memory_directory(self, agent, mock_settings):
        """Test: __init__ crea el directorio de memoria."""
        assert mock_settings.memory.path.parent.exists()
    
    def test_load_history_with_data(self, agent, mock_settings):
        """Test: cargar historial con datos existentes."""
        # Guardar datos de prueba
        test_history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola! ¿En qué puedo ayudarte?"}
        ]
        with open(mock_settings.memory.path, 'w') as f:
            json.dump(test_history, f)
        
        # Crear nuevo agente (debe cargar el historial)
        agent2 = PatAgent()
        assert len(agent2.history) == 2
        assert agent2.history[0]["content"] == "Hola"
    
    def test_save_history(self, agent, mock_settings):
        """Test: guardar historial correctamente."""
        agent.history = [{"role": "user", "content": "Test"}]
        agent._save_history()
        
        # Verificar que se guardó
        with open(mock_settings.memory.path, 'r') as f:
            saved = json.load(f)
        
        assert len(saved) == 1
        assert saved[0]["content"] == "Test"
    
    def test_save_history_truncates_when_too_large(self, agent, mock_settings):
        """Test: historial se trunca cuando excede max_size."""
        # Crear historial grande
        agent.history = [{"role": "user", "content": f"msg{i}"} for i in range(150)]
        agent._save_history()
        
        # Verificar que se truncó a max_size (100)
        assert len(agent.history) == 100
    
    def test_build_context_with_empty_history(self, agent):
        """Test: construir contexto con historial vacío."""
        context = agent._build_context()
        
        assert "Eres Pat" in context
        assert "Conversación reciente" not in context
    
    def test_build_context_with_history(self, agent):
        """Test: construir contexto con historial."""
        agent.history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola!"}
        ]
        
        context = agent._build_context()
        
        assert "Conversación reciente" in context
        assert "Usuario: Hola" in context
        assert "Asistente: Hola!" in context
    
    @patch('requests.post')
    def test_call_ollama_success(self, mock_post, agent):
        """Test: llamada exitosa a Ollama."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Respuesta de prueba"}
        mock_post.return_value = mock_response
        
        result = agent._call_ollama("Test prompt")
        
        assert result == "Respuesta de prueba"
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_call_ollama_timeout(self, mock_post, agent):
        """Test: timeout al llamar Ollama."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(OllamaTimeoutError, match="no respondió"):
            agent._call_ollama("Test")
    
    @patch('requests.post')
    def test_call_ollama_connection_error(self, mock_post, agent):
        """Test: error de conexión con Ollama."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(OllamaConnectionError, match="No se pudo conectar"):
            agent._call_ollama("Test")
    
    @patch('requests.post')
    def test_call_ollama_model_not_found(self, mock_post, agent):
        """Test: modelo no encontrado."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        from exceptions import OllamaModelNotFoundError
        with pytest.raises(OllamaModelNotFoundError, match="no encontrado"):
            agent._call_ollama("Test")
    
    @patch('requests.post')
    def test_ask_success(self, mock_post, agent):
        """Test: ask procesa correctamente una pregunta."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Respuesta"}
        mock_post.return_value = mock_response
        
        result = agent.ask("Hola")
        
        assert result == "Respuesta"
        assert len(agent.history) == 2
        assert agent.history[0]["role"] == "user"
        assert agent.history[1]["role"] == "assistant"
    
    def test_ask_empty_prompt_raises_error(self, agent):
        """Test: ask con prompt vacío lanza error."""
        with pytest.raises(InvalidPromptError):
            agent.ask("")
    
    @patch('requests.post')
    def test_ask_reverts_history_on_error(self, mock_post, agent):
        """Test: ask revierte historial si falla."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        initial_length = len(agent.history)
        
        with pytest.raises(OllamaConnectionError):
            agent.ask("Test")
        
        # El historial no debería haber cambiado
        assert len(agent.history) == initial_length
    
    def test_clear_history(self, agent):
        """Test: limpiar historial."""
        agent.history = [{"role": "user", "content": "Test"}]
        agent.clear_history()
        
        assert len(agent.history) == 0
```

**Verificación Día 5-6**:
```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar tests
pytest tests/ -v

# Verificar cobertura
pytest tests/ --cov=agents --cov=validators --cov=config --cov-report=html

# Debe mostrar ~40-50% coverage
```

---

### 🟢 DÍA 7-8: TESTS DE INTEGRACIÓN Y CI/CD

#### Tareas:

**1. Crear test de integración completo**

```python
# tests/integration/test_full_flow.py
import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock

from agents.pat_agent import PatAgent
from config import Settings

class TestFullFlow:
    """Tests de integración del flujo completo."""
    
    @pytest.fixture
    def integration_agent(self, tmp_path, monkeypatch):
        """Agente configurado para testing de integración."""
        # Configurar paths temporales
        memory_file = tmp_path / "integration_memory.json"
        log_file = tmp_path / "integration.log"
        
        # Mock de settings
        from config import Settings, OllamaConfig, MemoryConfig, ValidationConfig, LoggingConfig
        
        test_settings = Settings(
            ollama=OllamaConfig(
                base_url="http://localhost:11434",
                model="llama3.2:latest",
                timeout=30
            ),
            memory=MemoryConfig(
                path=memory_file,
                context_size=5,
                max_size=100
            ),
            validation=ValidationConfig(
                max_prompt_length=10000,
                min_prompt_length=1
            ),
            logging=LoggingConfig(
                level="DEBUG",
                file=log_file
            )
        )
        
        monkeypatch.setattr('config.settings', test_settings)
        return PatAgent()
    
    @patch('requests.post')
    def test_complete_conversation_flow(self, mock_post, integration_agent, tmp_path):
        """Test: flujo completo de conversación."""
        # Mock respuestas de Ollama
        responses = [
            {"response": "¡Hola! Soy Pat, tu asistente de programación."},
            {"response": "Python es un lenguaje de programación de alto nivel."},
            {"response": "Un diccionario es una estructura de datos clave-valor."}
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Simular conversación completa
        questions = [
            "Hola, ¿quién eres?",
            "¿Qué es Python?",
            "Explica qué es un diccionario"
        ]
        
        for i, question in enumerate(questions):
            mock_response.json.return_value = responses[i]
            answer = integration_agent.ask(question)
            assert answer == responses[i]["response"]
        
        # Verificar que el historial tiene 6 mensajes (3 preguntas + 3 respuestas)
        assert len(integration_agent.history) == 6
        
        # Verificar que se guardó en memoria
        memory_path = integration_agent.memory_path
        assert memory_path.exists()
        
        with open(memory_path, 'r') as f:
            saved_history = json.load(f)
        
        assert len(saved_history) == 6
    
    @patch('requests.post')
    def test_conversation_persistence(self, mock_post, tmp_path, monkeypatch):
        """Test: la conversación persiste entre sesiones."""
        # Primera sesión
        from config import settings
        memory_file = tmp_path / "persistence_test.json"
        monkeypatch.setattr(settings.memory, 'path', memory_file)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Primera respuesta"}
        mock_post.return_value = mock_response
        
        agent1 = PatAgent()
        agent1.ask("Primera pregunta")
        
        # Segunda sesión (nuevo agente, misma memoria)
        agent2 = PatAgent()
        
        # Debe cargar el historial de la sesión anterior
        assert len(agent2.history) == 2
        assert agent2.history[0]["content"] == "Primera pregunta"
    
    @patch('requests.post')
    def test_error_recovery(self, mock_post, integration_agent):
        """Test: recuperación de errores mantiene integridad."""
        # Primera pregunta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Respuesta exitosa"}
        mock_post.return_value = mock_response
        
        integration_agent.ask("Pregunta exitosa")
        assert len(integration_agent.history) == 2
        
        # Segunda pregunta falla
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        from exceptions import OllamaConnectionError
        with pytest.raises(OllamaConnectionError):
            integration_agent.ask("Pregunta que falla")
        
        # El historial debe seguir con 2 mensajes (no debe agregarse la pregunta fallida)
        assert len(integration_agent.history) == 2
    
    @patch('requests.post')
    def test_context_window_respects_limit(self, mock_post, integration_agent, monkeypatch):
        """Test: la ventana de contexto respeta el límite configurado."""
        from config import settings
        monkeypatch.setattr(settings.memory, 'context_size', 2)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Respuesta"}
        mock_post.return_value = mock_response
        
        # Agregar múltiples mensajes
        for i in range(5):
            integration_agent.ask(f"Pregunta {i}")
        
        # Construir contexto
        context = integration_agent._build_context()
        
        # Solo debe incluir los últimos 2 mensajes (context_size=2)
        assert "Pregunta 0" not in context
        assert "Pregunta 1" not in context
        assert "Pregunta 2" not in context
        assert "Pregunta 3" in context
        assert "Pregunta 4" in context
```

**2. Configurar GitHub Actions**

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check agents/ src/ tests/ main.py config.py validators.py exceptions.py || true
        flake8 agents/ src/ tests/ main.py config.py validators.py exceptions.py --max-line-length=100 || true
        isort --check-only agents/ src/ tests/ main.py config.py validators.py exceptions.py || true
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=agents --cov=config --cov=validators --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Security scan with Bandit
      run: |
        bandit -r agents/ src/ -ll || true

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install linting tools
      run: |
        pip install black flake8 isort mypy
    
    - name: Check formatting with Black
      run: black --check .
    
    - name: Check import order with isort
      run: isort --check-only .
    
    - name: Lint with flake8
      run: flake8 . --max-line-length=100 --exclude=venv,env
    
    - name: Type check with mypy
      run: mypy agents/ src/ config.py validators.py exceptions.py --ignore-missing-imports || true
```

**3. Configurar pre-commit hooks**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: detect-private-key

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: [-ll, -r, agents/, src/]
```

**4. Instalar pre-commit**

```bash
# Instalar pre-commit hooks
pre-commit install

# Ejecutar manualmente en todos los archivos
pre-commit run --all-files
```

**Verificación Día 7-8**:
```bash
# 1. Tests de integración deben pasar
pytest tests/integration/ -v

# 2. Pre-commit debe funcionar
git add .
git commit -m "test: add integration tests"
# Debe ejecutar todos los hooks automáticamente

# 3. Coverage debe estar en 40-50%
pytest tests/ --cov=agents --cov=config --cov=validators --cov-report=term

# 4. CI debe estar configurado
git push origin develop
# Verificar en GitHub Actions que el workflow se ejecute
```

---

### 🔵 DÍA 9-10: DOCUMENTACIÓN Y POLISH

#### Tareas:

**1. Mejorar README con badges y estructura clara**

```markdown
# 🤖 PatCode - Asistente de Programación Local

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/gonzacba17/Patcode/workflows/CI/badge.svg)](https://github.com/gonzacba17/Patcode/actions)
[![codecov](https://codecov.io/gh/gonzacba17/Patcode/graph/badge.svg)](https://codecov.io/gh/gonzacba17/Patcode)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Asistente de programación local con IA que respeta tu privacidad. Alternativa offline a Claude Code usando Ollama.

## ✨ Características

- 🔒 **100% Local**: Todo corre en tu máquina, sin enviar datos a la nube
- 🧠 **IA Avanzada**: Usa modelos LLM de última generación vía Ollama
- 💾 **Memoria Persistente**: Recuerda tus conversaciones anteriores
- ⚡ **Rápido y Ligero**: Respuestas en segundos
- 🛡️ **Robusto**: Manejo inteligente de errores
- 🧪 **Testeado**: >40% coverage con tests automatizados

## 📦 Instalación

### Prerrequisitos

1. **Python 3.9+**
   ```bash
   python --version  # Debe ser 3.9 o superior
   ```

2. **Ollama instalado y corriendo**
   ```bash
   # Instalar Ollama (https://ollama.ai)
   curl https://ollama.ai/install.sh | sh
   
   # Iniciar servicio
   ollama serve
   
   # Descargar modelo (en otra terminal)
   ollama pull llama3.2:latest
   ```

### Setup

```bash
# 1. Clonar repositorio
git clone https://github.com/gonzacba17/Patcode.git
cd Patcode

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar configuración de ejemplo
cp .env.example .env

# 5. (Opcional) Ajustar configuración en .env
nano .env

# 6. Ejecutar
python main.py
```

## 🚀 Uso

### Uso Básico

```bash
python main.py
```

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/clear` | Limpiar historial de conversación |
| `/quit` o `/exit` | Salir de PatCode |
| `Ctrl+C` | Salir (con opción de guardar) |

### Ejemplos

```
Tú: Explica qué es una función en Python

Pat: Una función en Python es un bloque de código reutilizable que realiza 
una tarea específica. Se define usando la palabra clave 'def'...

Tú: Dame un ejemplo

Pat: Claro, aquí un ejemplo simple:
```python
def saludar(nombre):
    return f"Hola, {nombre}!"

print(saludar("Juan"))  # Output: Hola, Juan!
```
```

## ⚙️ Configuración

PatCode se configura mediante variables de entorno en el archivo `.env`:

```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434  # URL del servidor Ollama
OLLAMA_MODEL=llama3.2:latest            # Modelo a usar
REQUEST_TIMEOUT=60                       # Timeout en segundos

# Memoria
MEMORY_PATH=./data/memory/memory.json   # Archivo de memoria
CONTEXT_WINDOW_SIZE=5                    # Mensajes en contexto
MAX_MEMORY_SIZE=1000                     # Máximo de mensajes

# Validación
MAX_PROMPT_LENGTH=10000                  # Longitud máxima de prompt
MIN_PROMPT_LENGTH=1                      # Longitud mínima

# Logging
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR
LOG_FILE=./logs/patcode.log             # Archivo de logs
```

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=agents --cov=config --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
```

## 🛠️ Desarrollo

### Setup para contribuir

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Instalar pre-commit hooks
pre-commit install

# Ejecutar linters manualmente
black .
isort .
flake8 .
```

### Estructura del Proyecto

```
PatCode/
├── agents/
│   └── pat_agent.py          # Lógica principal del agente
├── tests/
│   ├── unit/                 # Tests unitarios
│   └── integration/          # Tests de integración
├── config.py                 # Configuración
├── validators.py             # Validadores de input
├── exceptions.py             # Excepciones custom
├── main.py                   # Punto de entrada CLI
├── .env.example              # Configuración de ejemplo
├── .gitignore                # Archivos ignorados
├── requirements.txt          # Dependencias
└── requirements-dev.txt      # Dependencias de desarrollo
```

## 📚 Documentación Adicional

- [Guía de Contribución](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## 🐛 Troubleshooting

### Error: "No se pudo conectar con Ollama"

```bash
# Verificar que Ollama esté corriendo
ps aux | grep ollama

# Si no está corriendo, iniciarlo
ollama serve
```

### Error: "Modelo no encontrado"

```bash
# Descargar el modelo
ollama pull llama3.2:latest

# Verificar modelos disponibles
ollama list
```

### Tests fallan

```bash
# Verificar versión de Python
python --version  # Debe ser 3.9+

# Reinstalar dependencias
pip install -r requirements.txt -r requirements-dev.txt --force-reinstall

# Limpiar cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para detalles.

### Proceso

1. Fork el proyecto
2. Crea tu branch (`git checkout -b feature/AmazingFeature`)
3. Escribe tests para tu feature
4. Commit tus cambios (`git commit -m 'feat: Add AmazingFeature'`)
5. Push al branch (`git push origin feature/AmazingFeature`)
6. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [Ollama](https://ollama.ai) - Por la plataforma de LLMs local
- [Rich](https://github.com/Textualize/rich) - Por el hermoso CLI
- La comunidad open source

## 📧 Contacto

Gonzalo Cabrera - [@gonzacba17](https://github.com/gonzacba17)

Project Link: [https://github.com/gonzacba17/Patcode](https://github.com/gonzacba17/Patcode)

---

⭐ Si PatCode te resulta útil, considera darle una estrella en GitHub!
```

**2. Crear CONTRIBUTING.md**

```markdown
# Guía de Contribución

¡Gracias por tu interés en contribuir a PatCode! 🎉

## Código de Conducta

Este proyecto sigue un código de conducta. Al participar, te comprometes a mantener un ambiente respetuoso.

## ¿Cómo Contribuir?

### Reportar Bugs

1. Verifica que el bug no haya sido reportado ya en [Issues](https://github.com/gonzacba17/Patcode/issues)
2. Abre un nuevo issue con el template de bug
3. Incluye:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Logs relevantes
   - Versión de Python y sistema operativo

### Sugerir Features

1. Abre un issue con el template de feature request
2. Explica claramente:
   - El problema que resuelve
   - Cómo debería funcionar
   - Alternativas consideradas

### Pull Requests

#### Setup

```bash
# Fork y clone
git clone https://github.com/TU_USUARIO/Patcode.git
cd Patcode

# Crear entorno
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt -r requirements-dev.txt

# Instalar pre-commit hooks
pre-commit install
```

#### Workflow

1. **Crear branch desde `develop`**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/mi-feature
   ```

2. **Hacer cambios**:
   - Escribe código limpio y documentado
   - Sigue el estilo del proyecto (Black + isort)
   - Agrega tests para tu código

3. **Ejecutar tests**:
   ```bash
   # Tests
   pytest tests/ -v
   
   # Coverage (debe ser >40%)
   pytest tests/ --cov=agents --cov=config --cov-report=term
   
   # Linting
   black --check .
   isort --check-only .
   flake8 .
   ```

4. **Commit con Conventional Commits**:
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Tipos de commit:
   - `feat`: Nueva funcionalidad
   - `fix`: Corrección de bug
   - `docs`: Cambios en documentación
   - `style`: Formateo, sin cambios de código
   - `refactor`: Refactorización
   - `test`: Agregar o modificar tests
   - `chore`: Mantenimiento

5. **Push y crear PR**:
   ```bash
   git push origin feature/mi-feature
   ```
   
   - Abre PR hacia `develop` (no `main`)
   - Usa el template de PR
   - Asegúrate que pase CI

## Estándares de Código

### Python

- **Estilo**: Black (line length 100)
- **Imports**: isort con perfil black
- **Linting**: flake8
- **Type hints**: Usar donde sea posible
- **Docstrings**: Google style

Ejemplo:
```python
def calculate_something(value: int, multiplier: float = 1.0) -> float:
    """
    Calcula algo importante.
    
    Args:
        value: Valor base para el cálculo
        multiplier: Factor multiplicador (default: 1.0)
    
    Returns:
        Resultado del cálculo
    
    Raises:
        ValueError: Si value es negativo
    """
    if value < 0:
        raise ValueError("Value must be non-negative")
    return value * multiplier
```

### Tests

- **Cobertura mínima**: 40% (objetivo: 80%)
- **Naming**: `test_<función>_<escenario>`
- **Arrange-Act-Assert**: Estructura clara
- **Fixtures**: Reutilizar en `conftest.py`

Ejemplo:
```python
def test_validate_prompt_empty_raises_error():
    """Test: prompt vacío debe lanzar InvalidPromptError."""
    with pytest.raises(InvalidPromptError, match="no puede estar vacío"):
        InputValidator.validate_prompt("")
```

## Proceso de Review

1. **Automated checks**: CI debe pasar (tests, linting)
2. **Code review**: Al menos 1 approval requerido
3. **Changes requested**: Hacer ajustes si se solicitan
4. **Merge**: Un maintainer hará merge a `develop`

## Versionado

Seguimos [Semantic Versioning](https://semver.org/):
- **MAJOR**: Cambios incompatibles con versión anterior
- **MINOR**: Nueva funcionalidad compatible
- **PATCH**: Bug fixes compatibles

## Preguntas

¿Dudas? Abre un issue con la etiqueta `question` o contacta a los maintainers.

¡Gracias por contribuir! 🚀
```

**3. Crear CHANGELOG.md**

```markdown
# Changelog

Todos los cambios notables del proyecto serán documentados aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-d_history_empty_file(self, agent):
        """Test: cargar historial con archivo vacío."""
        assert agent.history == []
    
    def test_loa