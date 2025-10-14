# 🧠 PatCode

### Tu asistente de programación local impulsado por Ollama

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Ollama](https://img.shields.io/badge/ollama-compatible-green)

---

## 📖 Índice

1. [Introducción](#-introducción)
2. [Características principales](#-características-principales)
3. [Instalación](#-instalación)
4. [Uso](#-uso)
5. [Estructura del código](#-estructura-del-código)
6. [Pruebas](#-pruebas)
7. [Contribuciones](#-contribuciones)
8. [Licencia](#-licencia)

---

## 🎯 Introducción

**PatCode** es un asistente de programación local que replica las funcionalidades de Claude Code de Anthropic, pero completamente **offline**, utilizando modelos de lenguaje de [Ollama](https://ollama.ai/) (como Llama 3.2, Mistral, CodeLlama, entre otros).

### ¿Por qué PatCode?

La motivación detrás de PatCode surge de la necesidad de contar con un asistente de programación que:

- **No dependa de la nube**: Funciona completamente offline, ideal para desarrolladores que trabajan en ambientes sin conexión o con restricciones de seguridad.
- **Preserve la privacidad**: Todo el código y las conversaciones permanecen en tu máquina local, sin enviar datos a servicios externos.
- **Sea accesible**: No requiere suscripciones ni cuotas de uso, solo necesitas hardware local suficiente para ejecutar modelos de Ollama.
- **Esté disponible 24/7**: Sin límites de rate-limiting ni dependencias de servicios remotos.

PatCode te permite interactuar con tu código de manera natural, pedir explicaciones, recibir sugerencias de mejora, depurar errores y aprender nuevos conceptos, todo desde la comodidad de tu terminal.

---

## ✨ Características principales

### 💬 Interacción Natural
Escribe preguntas o instrucciones como si hablaras con otro programador. PatCode entiende contexto y puede mantener conversaciones técnicas fluidas.

**Ejemplo:**
```
Tú: ¿Cómo puedo leer un archivo JSON en Python?
PatCode: Puedes usar el módulo 'json'...
```

### 🧠 Memoria Persistente
PatCode recuerda el contexto de tus últimas conversaciones, permitiendo mantener diálogos coherentes a lo largo de múltiples sesiones. La memoria se almacena en `agents/memory/memory.json`.

### 🔍 Análisis de Código
Copia fragmentos de código o describe tu problema, y PatCode te ofrecerá:
- Explicaciones detalladas de cómo funciona el código
- Sugerencias de mejora y optimización
- Identificación de errores y bugs potenciales
- Refactorización de código

### ⚙️ 100% Local
Funciona completamente offline usando tu modelo Ollama preferido (por ejemplo, `llama3.2:latest`, `codellama`, `mistral`). No requiere conexión a internet para funcionar.

### 🔒 Privado y Seguro
Ningún dato, código o conversación sale de tu equipo. Ideal para trabajar con código propietario o confidencial sin preocupaciones de seguridad.

### 🎨 Personalizable
Puedes cambiar el modelo de lenguaje según tus necesidades, ajustar la cantidad de contexto histórico y personalizar el comportamiento del asistente.

---

## 🚀 Instalación

### Requisitos previos

Antes de instalar PatCode, asegúrate de tener:

1. **Python 3.9 o superior**
   - Descarga desde [python.org](https://www.python.org/downloads/)
   - Verifica la instalación:
     ```bash
     python --version
     ```

2. **Ollama instalado y en ejecución**
   - Descarga desde [ollama.ai](https://ollama.ai/)
   - Verifica que Ollama esté funcionando:
     ```bash
     ollama list
     ```
   - Deberías ver una lista de modelos disponibles:
     ```
     NAME              ID              SIZE      MODIFIED
     llama3.2:latest   a80c4f17acd5    2.0 GB    5 days ago
     ```

3. **Git** (opcional, para clonar el repositorio)

---

### Instalación en Windows

1. **Clonar el repositorio:**
   ```cmd
   git clone https://github.com/gonzacba17/Patcode.git
   cd Patcode
   ```

2. **Crear un entorno virtual:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Crear estructura de directorios (si no existe):**
   ```cmd
   mkdir agents\memory
   ```

5. **Ejecutar PatCode:**
   ```cmd
   python main.py
   ```

---

### Instalación en macOS / Linux

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/gonzacba17/Patcode.git
   cd Patcode
   ```

2. **Crear un entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Crear estructura de directorios (si no existe):**
   ```bash
   mkdir -p agents/memory
   ```

5. **Ejecutar PatCode:**
   ```bash
   python main.py
   ```

---

### Configuración de Ollama

Si no tienes un modelo descargado, puedes obtener uno con:

```bash
# Para uso general de código
ollama pull llama3.2

# O para tareas específicas de programación
ollama pull codellama

# O Mistral para español
ollama pull mistral
```

Para verificar que el servicio de Ollama está activo:

```bash
curl http://localhost:11434/api/tags
```

---

## 💻 Uso

### Iniciar el asistente

Ejecuta el archivo principal desde tu terminal:

```bash
python main.py
```

Verás el mensaje de bienvenida:

```
🤖 Bienvenido a PatCode (versión local con Ollama)

Tú: 
```

### Ejemplos de interacción

#### Ejemplo 1: Explicar conceptos
```
Tú: ¿Qué son los decoradores en Python?
PatCode: Los decoradores en Python son funciones que modifican el comportamiento 
de otras funciones o métodos. Se utilizan con la sintaxis @decorator...
```

#### Ejemplo 2: Análisis de código
```
Tú: Explicame este código:
def factorial(n):
    return 1 if n == 0 else n * factorial(n-1)

PatCode: Este código implementa una función recursiva para calcular el factorial 
de un número. Si n es 0, retorna 1 (caso base). En caso contrario, multiplica 
n por el factorial de n-1...
```

#### Ejemplo 3: Depuración
```
Tú: Mi código da error "IndexError: list index out of range". ¿Qué significa?

PatCode: Este error significa que estás intentando acceder a una posición en 
una lista que no existe. Por ejemplo, si tienes una lista de 3 elementos e 
intentas acceder al índice 5...
```

#### Ejemplo 4: Sugerencias de mejora
```
Tú: ¿Cómo puedo hacer este código más eficiente?
for i in range(len(lista)):
    print(lista[i])

PatCode: Puedes simplificar este código usando iteración directa sobre la lista:
for elemento in lista:
    print(elemento)
Esto es más Pythonic y eficiente...
```

### Comandos disponibles

- **Salir del asistente:** Escribe `salir`, `exit` o `quit`
- **Nueva conversación:** Simplemente comienza a escribir, el contexto se mantiene automáticamente
- **Código multilínea:** Puedes pegar código directamente en la terminal

---

## 📁 Estructura del código

```
PatCode/
│
├── main.py                      # Punto de entrada principal
├── requirements.txt             # Dependencias del proyecto
├── README.md                    # Documentación (este archivo)
│
├── agents/                      # Módulos de agentes IA
│   ├── __init__.py
│   ├── pat_agent.py            # Lógica principal del asistente
│   └── memory/
│       └── memory.json         # Memoria persistente de conversaciones
│
├── config/                      # Configuraciones del proyecto
│   ├── __init__.py
│   └── settings.py             # Configuraciones generales
│
├── context/                     # Manejo del contexto de conversación
│   ├── __init__.py
│   └── context_manager.py      # Gestión del contexto histórico
│
├── tests/                       # Pruebas unitarias e integración
│   ├── __init__.py
│   ├── test_agent.py           # Tests del agente principal
│   └── test_memory.py          # Tests de memoria persistente
│
├── tools/                       # Herramientas auxiliares
│   ├── __init__.py
│   └── code_analyzer.py        # Analizador de código
│
├── ui/                          # Interfaz de usuario
│   ├── __init__.py
│   └── terminal_ui.py          # Interfaz de terminal
│
└── utils/                       # Funciones utilitarias
    ├── __init__.py
    ├── logger.py               # Sistema de logging
    └── validators.py           # Validadores de entrada
```

### Descripción de módulos principales

#### `main.py`
Punto de entrada de la aplicación. Inicializa el agente PatCode y maneja el bucle principal de interacción con el usuario.

#### `agents/pat_agent.py`
Contiene la clase `PatAgent`, que gestiona:
- Comunicación con la API de Ollama
- Carga y guardado de memoria persistente
- Construcción del contexto de conversación
- Procesamiento de respuestas del modelo

#### `agents/memory/memory.json`
Almacena el historial de conversaciones en formato JSON para mantener el contexto entre sesiones.

#### `config/settings.py`
Define configuraciones globales como:
- Modelo de Ollama a utilizar
- Ruta de memoria
- Parámetros de la API
- Límites de contexto

#### `context/context_manager.py`
Gestiona el contexto de la conversación, incluyendo:
- Límite de mensajes históricos
- Formateo del contexto
- Resumen de sesiones largas

#### `tools/code_analyzer.py`
Proporciona herramientas para analizar código, detectar patrones y ofrecer sugerencias específicas.

#### `utils/logger.py`
Sistema de logging para debug y seguimiento de errores.

---

## 🧪 Pruebas

PatCode utiliza `pytest` como framework de pruebas. Las pruebas están organizadas en el directorio `tests/`.

### Ejecutar todas las pruebas

```bash
# Activar el entorno virtual primero
source venv/bin/activate  # En Linux/macOS
# o
venv\Scripts\activate     # En Windows

# Ejecutar pruebas
pytest tests/
```

### Ejecutar pruebas específicas

```bash
# Pruebas del agente
pytest tests/test_agent.py

# Pruebas de memoria
pytest tests/test_memory.py

# Ejecutar con verbose
pytest -v tests/
```

### Cobertura de código

Para generar un reporte de cobertura:

```bash
pip install pytest-cov
pytest --cov=agents --cov=utils tests/
```

### Estructura de pruebas

```python
# tests/test_agent.py
import pytest
from agents.pat_agent import PatAgent

def test_agent_initialization():
    """Verifica que el agente se inicialice correctamente"""
    agent = PatAgent()
    assert agent.model == "llama3.2:latest"
    assert agent.history == []

def test_memory_persistence():
    """Verifica que la memoria se guarde correctamente"""
    agent = PatAgent()
    agent.ask("Hola")
    assert len(agent.history) > 0
```

### Agregar nuevas pruebas

1. Crea un nuevo archivo en `tests/` con el prefijo `test_`
2. Importa los módulos necesarios
3. Define funciones de prueba con el prefijo `test_`
4. Usa `assert` para verificar comportamientos esperados

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! PatCode es un proyecto de código abierto y estamos encantados de recibir mejoras de la comunidad.

### Cómo contribuir

1. **Fork del repositorio**
   - Haz clic en "Fork" en la parte superior derecha de la página del repositorio

2. **Clona tu fork**
   ```bash
   git clone https://github.com/TU_USUARIO/Patcode.git
   cd Patcode
   ```

3. **Crea una rama para tu feature**
   ```bash
   git checkout -b feature/mi-nueva-funcionalidad
   ```

4. **Realiza tus cambios**
   - Asegúrate de seguir las convenciones de código
   - Añade pruebas para nuevas funcionalidades
   - Actualiza la documentación si es necesario

5. **Commit de tus cambios**
   ```bash
   git add .
   git commit -m "feat: descripción clara de los cambios"
   ```

6. **Push a tu fork**
   ```bash
   git push origin feature/mi-nueva-funcionalidad
   ```

7. **Crea un Pull Request**
   - Ve a tu fork en GitHub
   - Haz clic en "New Pull Request"
   - Describe tus cambios detalladamente

### Convenciones de código

- **Estilo:** Seguimos [PEP 8](https://pep8.org/) para código Python
- **Docstrings:** Utiliza docstrings para documentar funciones y clases
- **Type hints:** Preferimos el uso de type hints cuando sea posible
- **Commits:** Utiliza [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` para nuevas funcionalidades
  - `fix:` para corrección de bugs
  - `docs:` para cambios en documentación
  - `test:` para añadir o modificar pruebas
  - `refactor:` para refactorización de código

### Reportar issues

Si encuentras un bug o tienes una sugerencia:

1. Verifica que no exista un issue similar
2. Crea un nuevo issue con:
   - Título descriptivo
   - Descripción detallada del problema
   - Pasos para reproducir (si aplica)
   - Versión de Python y Ollama
   - Sistema operativo

### Ideas para contribuir

- 🐛 Reportar y corregir bugs
- ✨ Proponer nuevas funcionalidades
- 📖 Mejorar la documentación
- 🌐 Añadir traducciones
- 🧪 Aumentar la cobertura de pruebas
- ⚡ Optimizar el rendimiento

---

## 📄 Licencia

Este proyecto está licenciado bajo la **MIT License**.

```
MIT License

Copyright (c) 2025 Gonza Cba

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### ¿Qué significa esto?

La licencia MIT te permite:

✅ Usar el código comercialmente  
✅ Modificar el código  
✅ Distribuir el código  
✅ Uso privado  
✅ Sublicenciar  

Con la única condición de incluir el aviso de copyright y la licencia en todas las copias.

---

## 🙏 Agradecimientos

- **Anthropic** por la inspiración con [Claude Code](https://claude.ai/)
- **Ollama** por proporcionar una plataforma excelente para ejecutar modelos localmente
- **La comunidad open-source** por las bibliotecas y herramientas que hacen posible este proyecto

---

## 🔮 Roadmap

### ✅ Versión actual (v1.0)
- Interacción en terminal
- Memoria básica persistente
- Soporte para múltiples modelos de Ollama

### 🚧 Próximas versiones

#### v1.1 - Análisis de proyectos
- Lectura y análisis de carpetas completas
- Navegación por estructura de archivos
- Búsqueda de código en proyectos

#### v1.2 - Herramientas de desarrollo
- Ejecución de comandos locales (compilar, testear)
- Integración con Git (commits automáticos, PRs)
- Linting y formateo automático

#### v1.3 - Mejoras de UX
- Interfaz visual opcional (Streamlit/Electron)
- Resumen automático de sesiones largas
- Exportación de conversaciones

#### v2.0 - Características avanzadas
- Soporte para múltiples lenguajes de programación
- Plantillas de código y snippets
- Integración con IDEs (VS Code extension)

---

## 📞 Contacto y soporte

- **GitHub Issues:** [github.com/gonzacba17/Patcode/issues](https://github.com/gonzacba17/Patcode/issues)
- **Autor:** Gonza Cba
- **Repositorio:** [github.com/gonzacba17/Patcode](https://github.com/gonzacba17/Patcode)

---

## 📚 Recursos adicionales

- [Documentación de Ollama](https://github.com/ollama/ollama)
- [Guía de Python](https://docs.python.org/3/)
- [Claude Code de Anthropic](https://claude.ai/code)
- [PEP 8 - Guía de estilo Python](https://pep8.org/)

**Creado con ❤️ por Gonza Cba**

Si te gusta PatCode, ¡no olvides darle una ⭐ en GitHub!