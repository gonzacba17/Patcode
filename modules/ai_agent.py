import subprocess
import json

def ask_ollama(prompt, model="llama3"):
    """Envía un prompt a Ollama y devuelve la respuesta del modelo."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=True
        )
        return result.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando Ollama: {e.stderr.decode('utf-8')}"
def parse_json_response(response):
    """Intenta parsear una respuesta JSON y maneja errores."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        return {"error": f"Error de parseo JSON: {str(e)}", "raw_response": response}                       