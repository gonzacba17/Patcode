"""
Interfaz web para PatCode usando Flask
Requiere: pip install flask flask-cors
"""

try:
    from flask import Flask, render_template_string, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠ Flask no está instalado. Usa: pip install flask flask-cors")

import os
import json
from datetime import datetime
from utils.logger import get_logger


class WebUI:
    """Interfaz web para PatCode"""
    
    def __init__(self, agent, host='127.0.0.1', port=5000):
        """
        Inicializa la interfaz web
        
        Args:
            agent: Instancia del agente PatAgent
            host (str): Host donde correr el servidor
            port (int): Puerto del servidor
        """
        if not FLASK_AVAILABLE:
            raise ImportError("WebUI requiere Flask. Instala con: pip install flask flask-cors")
        
        self.agent = agent
        self.host = host
        self.port = port
        self.logger = get_logger()
        
        # Crear aplicación Flask
        self.app = Flask(__name__)
        CORS(self.app)  # Habilitar CORS
        
        # Configurar rutas
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la aplicación"""
        
        @self.app.route('/')
        def index():
            """Página principal"""
            return render_template_string(self.get_html_template())
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            """Endpoint para enviar mensajes"""
            try:
                data = request.json
                user_message = data.get('message', '')
                
                if not user_message:
                    return jsonify({'error': 'Mensaje vacío'}), 400
                
                # Procesar mensaje
                response = self.agent.ask(user_message)
                
                return jsonify({
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error en /api/chat: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/history', methods=['GET'])
        def get_history():
            """Endpoint para obtener el historial"""
            try:
                return jsonify({
                    'history': self.agent.history,
                    'count': len(self.agent.history)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/clear', methods=['POST'])
        def clear_history():
            """Endpoint para limpiar el historial"""
            try:
                self.agent.history = []
                self.agent.save_memory()
                return jsonify({'message': 'Historial limpiado'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def status():
            """Endpoint de estado"""
            return jsonify({
                'status': 'online',
                'model': self.agent.model,
                'messages': len(self.agent.history)
            })
    
    def get_html_template(self):
        """Retorna el template HTML de la interfaz"""
        return '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PatCode - Interfaz Web</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 900px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 20px 20px 0 0;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 0.9em;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 15px;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 15px;
        }
        
        .message.bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #ddd;
            border-radius: 15px 15px 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message-avatar {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
            margin: 0 10px;
        }
        
        .message.user .message-avatar {
            background: #667eea;
            color: white;
        }
        
        .message.bot .message-avatar {
            background: #4CAF50;
            color: white;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
            display: flex;
            gap: 10px;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 1em;
            outline: none;
            transition: border-color 0.3s;
        }
        
        #messageInput:focus {
            border-color: #667eea;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .btn-send {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-send:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-send:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-clear {
            background: #f44336;
            color: white;
        }
        
        .btn-clear:hover {
            background: #d32f2f;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px;
            background: white;
            border-radius: 15px;
            width: 60px;
            margin: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .typing-indicator.active {
            display: block;
        }
        
        .typing-indicator span {
            height: 10px;
            width: 10px;
            background: #667eea;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        
        .status {
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            text-align: center;
            font-size: 0.9em;
        }
        
        .status.offline {
            background: #f44336;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
        }
        
        pre code {
            background: none;
            color: inherit;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 PatCode</h1>
            <p>Tu asistente de programación local con Ollama</p>
        </div>
        
        <div class="status" id="status">🟢 Conectado</div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message bot">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    ¡Hola! Soy PatCode, tu asistente de programación local. ¿En qué puedo ayudarte hoy?
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
        
        <div class="input-container">
            <button class="btn btn-clear" onclick="clearChat()">🗑️ Limpiar</button>
            <input 
                type="text" 
                id="messageInput" 
                placeholder="Escribe tu mensaje aquí..." 
                onkeypress="handleKeyPress(event)"
            />
            <button class="btn btn-send" id="sendButton" onclick="sendMessage()">
                ▶ Enviar
            </button>
        </div>
    </div>
    
    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        const statusDiv = document.getElementById('status');
        
        // Verificar estado del servidor
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                statusDiv.textContent = '🟢 Conectado';
                statusDiv.className = 'status';
            } catch (error) {
                statusDiv.textContent = '🔴 Desconectado';
                statusDiv.className = 'status offline';
            }
        }
        
        // Agregar mensaje al chat
        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = isUser ? '👤' : '🤖';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Procesar markdown básico
            content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
            content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
            content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
            
            contentDiv.innerHTML = content;
            
            if (isUser) {
                messageDiv.appendChild(contentDiv);
                messageDiv.appendChild(avatar);
            } else {
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(contentDiv);
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Enviar mensaje
        async function sendMessage() {
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            // Deshabilitar input
            sendButton.disabled = true;
            messageInput.disabled = true;
            
            // Agregar mensaje del usuario
            addMessage(message, true);
            messageInput.value = '';
            
            // Mostrar indicador de escritura
            typingIndicator.classList.add('active');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage('❌ Error: ' + data.error, false);
                } else {
                    addMessage(data.response, false);
                }
            } catch (error) {
                addMessage('❌ Error de conexión: ' + error.message, false);
            } finally {
                // Ocultar indicador y habilitar input
                typingIndicator.classList.remove('active');
                sendButton.disabled = false;
                messageInput.disabled = false;
                messageInput.focus();
            }
        }
        
        // Manejar Enter
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        // Limpiar chat
        async function clearChat() {
            if (!confirm('¿Estás seguro de que quieres limpiar el historial?')) {
                return;
            }
            
            try {
                await fetch('/api/clear', { method: 'POST' });
                chatContainer.innerHTML = '';
                addMessage('Historial limpiado. ¿En qué puedo ayudarte?', false);
            } catch (error) {
                alert('Error al limpiar el historial');
            }
        }
        
        // Verificar estado cada 30 segundos
        setInterval(checkStatus, 30000);
        checkStatus();
        
        // Focus en el input al cargar
        messageInput.focus();
    </script>
</body>
</html>
        '''
    
    def run(self, debug=False):
        """
        Inicia el servidor web
        
        Args:
            debug (bool): Modo debug de Flask
        """
        self.logger.info(f"🌐 Iniciando servidor web en http://{self.host}:{self.port}")
        self.logger.info("Presiona Ctrl+C para detener el servidor")
        
        try:
            self.app.run(host=self.host, port=self.port, debug=debug)
        except KeyboardInterrupt:
            self.logger.info("\n👋 Servidor web detenido")
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor: {str(e)}")


def main():
    """Función principal para ejecutar la interfaz web"""
    if not FLASK_AVAILABLE:
        print("❌ No se puede iniciar WebUI sin Flask")
        print("💡 Instala con: pip install flask flask-cors")
        return
    
    from agents.pat_agent import PatAgent
    
    # Crear agente
    agent = PatAgent()
    
    # Crear y ejecutar interfaz web
    web_ui = WebUI(agent, host='127.0.0.1', port=5000)
    web_ui.run(debug=True)


if __name__ == "__main__":
    main()