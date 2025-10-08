🧠 PatCode — Tu asistente de programación local impulsado por Ollama

PatCode es un asistente de programación local que replica las funcionalidades de Claude Code, pero completamente offline, utilizando modelos de Ollama (como Llama 3.2).
Te permite interactuar con tu código, pedir explicaciones, recibir sugerencias o depurar errores directamente desde tu terminal, sin depender de la nube.

🚀 Características principales

💬 Interacción natural: escribí preguntas o instrucciones como si hablaras con otro programador.

🧠 Memoria persistente: recuerda el contexto de las últimas conversaciones.

🔍 Análisis de código: podés copiar código o fragmentos y pedirle explicaciones o mejoras.

⚙️ 100% local: funciona sin conexión, usando tu modelo Ollama (ej. llama3.2:latest).

🔒 Privado y seguro: ningún dato sale de tu equipo.

📁 Estructura del proyecto
PatCode/
│
├── main.py                     # Punto de entrada
├── agents/
│   ├── __init__.py
│   ├── pat_agent.py            # Lógica del asistente IA
│
├── memory/
│   └── memory.json             # Memoria persistente (últimos diálogos)
│
└── requirements.txt            # Dependencias del proyecto

⚙️ Requisitos previos

Antes de comenzar, asegurate de tener instalado:

Python 3.9 o superior

Ollama (en ejecución en tu sistema)
👉 Descargar Ollama

Verificá que Ollama esté corriendo correctamente:

ollama list


Ejemplo de salida:

NAME               ID              SIZE      MODIFIED
llama3.2:latest    a80c4f17acd5    2.0 GB    5 days ago

🧩 Instalación

Cloná o creá el proyecto:

mkdir PatCode && cd PatCode


Crea un entorno virtual:

python -m venv venv
venv\Scripts\activate      # En Windows
# source venv/bin/activate # En Linux/Mac


Crea los archivos base:

Guardá los siguientes archivos en tu carpeta:

requirements.txt
requests

agents/pat_agent.py
import requests
import json

class PatAgent:
    def __init__(self, model="llama3.2:latest", memory_path="memory/memory.json"):
        self.model = model
        self.memory_path = memory_path
        self.history = self.load_memory()

    def load_memory(self):
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_memory(self):
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def ask(self, prompt):
        self.history.append({"role": "user", "content": prompt})

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": self.model,
                "prompt": self._build_context(),
                "stream": False
            }
        )

        data = response.json()
        answer = data.get("response", "").strip()

        self.history.append({"role": "assistant", "content": answer})
        self.save_memory()
        return answer

    def _build_context(self):
        context = ""
        for msg in self.history[-5:]:
            context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return context

main.py
from agents.pat_agent import PatAgent

def main():
    print("🤖 Bienvenido a PatCode (versión local con Ollama)\n")
    agent = PatAgent()

    while True:
        prompt = input("Tú: ")
        if prompt.lower() in ["salir", "exit", "quit"]:
            print("👋 Hasta luego.")
            break

        answer = agent.ask(prompt)
        print(f"PatCode: {answer}\n")

if __name__ == "__main__":
    main()


Instalá dependencias:

pip install -r requirements.txt


Ejecutá el asistente:

python main.py

💬 Ejemplo de uso
🤖 Bienvenido a PatCode (versión local con Ollama)

Tú: Explicame cómo usar listas en Python
PatCode: Las listas en Python son estructuras de datos mutables...

🧱 Arquitectura básica
Usuario  →  PatCode (Python)
         →  API de Ollama (localhost:11434)
         →  Modelo LLM (Llama3.2, etc.)


El flujo de comunicación es local:

main.py recibe tu entrada.

pat_agent.py envía la solicitud a http://localhost:11434/api/generate.

Ollama procesa con el modelo y devuelve la respuesta.

🌟 Próximas versiones (en desarrollo)

✅ Versión actual: interacción en terminal + memoria básica
🚧 Próximas mejoras:

Soporte para análisis de proyectos completos (lectura de carpetas)

Ejecución de comandos locales (compilar, testear, etc.)

Integración con Git (commits automáticos y PRs)

Resumen automático de sesiones largas

Interfaz visual (opcional con Streamlit o Electron)

🤝 Contribuciones

¡Toda mejora es bienvenida!
Podés:

Abrir un issue para sugerencias o errores

Crear un pull request con mejoras

🧾 Licencia

MIT License © 2025 — Creado por Gonza Cba
Inspirado en Claude Code
 de Anthropic.
Implementado con ❤️ sobre Ollama + Python.