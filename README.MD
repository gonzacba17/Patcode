🧠 PatCode — Asistente de Programación Local con Ollama

PatCode es un asistente de programación local que replica las funcionalidades de Claude Code, pero completamente offline, utilizando modelos de Ollama (como Llama 3.2). Te permite interactuar con tu código, pedir explicaciones, recibir sugerencias o depurar errores directamente desde tu terminal, sin depender de la nube.

🚀 Características Principales

Interacción Natural: Escribe preguntas o instrucciones en lenguaje natural y recibe respuestas claras y útiles.

Análisis de Código: Detecta errores de sintaxis y ofrece sugerencias de mejora.

Refactorización Automática: Mejora la estructura y eficiencia de tu código.

Ejecución de Pruebas: Corre tus tests y muestra los resultados directamente en la terminal.

Integración con Git: Realiza commits y revisa el estado de tu repositorio sin salir de la terminal.

Memoria Persistente: Recuerda el contexto de tus interacciones anteriores para ofrecer respuestas más precisas.

🛠 Requisitos

Python 3.11 o superior

Ollama instalado y en funcionamiento

Modelos de Ollama descargados (por ejemplo, llama3.2:latest)

Git instalado y configurado


🧩 Estructura del Proyecto
PatCode/
│
├── main.py                          # Punto de entrada principal
├── requirements.txt                 # Dependencias Python
├── README.md                        # Documentación del proyecto
├── .gitignore                       # Archivos a ignorar en Git
│
├── config/                          # ⚙️ CONFIGURACIÓN
│   ├── __init__.py
│   ├── settings.py                  # Configuración general (URLs, paths, límites)
│   ├── prompts.py                   # System prompts y plantillas
│   └── models.py                    # Configuración de modelos Ollama
│
├── agents/                          # 🤖 AGENTES IA
│   ├── __init__.py
│   ├── pat_agent.py                 # Agente principal con herramientas
│   ├── agentic_loop.py              # Loop de razonamiento-acción
│   ├── tool_parser.py               # Parser de llamadas a herramientas
│   ├── planner.py                   # Planificador de tareas complejas
│   └── memory/
│       ├── memory.json              # Historial de conversaciones
│       └── context_cache.json       # Cache de contexto de proyecto
│
├── tools/                           # 🔧 HERRAMIENTAS
│   ├── __init__.py
│   ├── base_tool.py                 # Clase base abstracta
│   ├── file_tools.py                # Leer/escribir archivos
│   ├── directory_tools.py           # Navegación de directorios
│   ├── shell_tools.py               # Ejecución de comandos shell
│   ├── search_tools.py              # Búsqueda en código
│   ├── git_tools.py                 # Operaciones Git
│   └── analysis_tools.py            # Análisis estático de código
│
├── context/                         # 📊 ANÁLISIS DE CONTEXTO
│   ├── __init__.py
│   ├── project_analyzer.py          # Analiza estructura del proyecto
│   ├── code_indexer.py              # Indexa y mapea código
│   ├── dependency_mapper.py         # Mapea dependencias
│   └── semantic_search.py           # Búsqueda semántica en código
│
├── utils/                           # 🛠️ UTILIDADES
│   ├── __init__.py
│   ├── formatters.py                # Formateo de output
│   ├── diff_viewer.py               # Visualización de cambios
│   ├── validators.py                # Validaciones de seguridad
│   ├── logger.py                    # Sistema de logging
│   └── colors.py                    # Colores para terminal
│
├── ui/                              # 🎨 INTERFAZ (Opcional - Fase 4)
│   ├── __init__.py
│   ├── cli.py                       # Interfaz de línea de comandos mejorada
│   ├── tui.py                       # Terminal UI (con rich/textual)
│   └── web.py                       # Interfaz web (con Streamlit)
│
└── tests/                           # ✅ TESTS
    ├── __init__.py
    ├── test_tools.py                # Tests de herramientas
    ├── test_agent.py                # Tests del agente
    ├── test_parser.py               # Tests del parser
    └── fixtures/                    # Archivos de prueba
        └── sample_project/

📚 Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar PatCode, por favor sigue estos pasos:

Fork este repositorio.

Crea una nueva rama (git checkout -b feature/mi-mejora).

Realiza tus cambios y haz commit (git commit -am 'Añadir nueva característica').

Sube tus cambios a tu fork (git push origin feature/mi-mejora).

Abre un Pull Request en este repositorio.

📝 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE
 para más detalles.

💬 Contacto

Para preguntas o sugerencias, puedes abrir un issue
 en este repositorio o contactarme directamente.

¡Gracias por usar PatCode!