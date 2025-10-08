"""
Tests para el agente PatAgent
"""

import unittest
import os
import json
import tempfile
from agents.pat_agent import PatAgent


class TestPatAgent(unittest.TestCase):
    """Tests para la clase PatAgent"""
    
    def setUp(self):
        """Configuración antes de cada test"""
        # Crear un archivo temporal para memoria
        self.temp_memory = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_memory.write('[]')
        self.temp_memory.close()
        
        # Crear agente con memoria temporal
        self.agent = PatAgent(
            model="llama3.2:latest",
            memory_path=self.temp_memory.name
        )
    
    def tearDown(self):
        """Limpieza después de cada test"""
        # Eliminar archivo temporal
        if os.path.exists(self.temp_memory.name):
            os.unlink(self.temp_memory.name)
    
    def test_initialization(self):
        """Test de inicialización del agente"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.model, "llama3.2:latest")
        self.assertEqual(self.agent.memory_path, self.temp_memory.name)
        self.assertIsInstance(self.agent.history, list)
    
    def test_load_empty_memory(self):
        """Test de carga de memoria vacía"""
        history = self.agent.load_memory()
        self.assertEqual(history, [])
    
    def test_save_memory(self):
        """Test de guardado de memoria"""
        # Agregar mensajes al historial
        self.agent.history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "¡Hola! ¿Cómo puedo ayudarte?"}
        ]
        
        # Guardar memoria
        self.agent.save_memory()
        
        # Verificar que se guardó correctamente
        with open(self.temp_memory.name, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data), 2)
        self.assertEqual(saved_data[0]['role'], 'user')
        self.assertEqual(saved_data[1]['role'], 'assistant')
    
    def test_load_existing_memory(self):
        """Test de carga de memoria existente"""
        # Crear memoria con datos
        test_history = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"}
        ]
        
        with open(self.temp_memory.name, 'w', encoding='utf-8') as f:
            json.dump(test_history, f)
        
        # Crear nuevo agente que debería cargar la memoria
        new_agent = PatAgent(memory_path=self.temp_memory.name)
        
        self.assertEqual(len(new_agent.history), 2)
        self.assertEqual(new_agent.history[0]['content'], 'Test message')
    
    def test_build_context(self):
        """Test de construcción de contexto"""
        # Agregar mensajes al historial
        self.agent.history = [
            {"role": "user", "content": "Mensaje 1"},
            {"role": "assistant", "content": "Respuesta 1"},
            {"role": "user", "content": "Mensaje 2"},
            {"role": "assistant", "content": "Respuesta 2"},
        ]
        
        context = self.agent._build_context()
        
        # Verificar que el contexto contiene los mensajes
        self.assertIn("Mensaje 1", context)
        self.assertIn("Respuesta 1", context)
        self.assertIn("Mensaje 2", context)
        self.assertIn("Respuesta 2", context)
    
    def test_build_context_limit(self):
        """Test de límite de contexto"""
        # Agregar muchos mensajes
        for i in range(10):
            self.agent.history.append({"role": "user", "content": f"Mensaje {i}"})
            self.agent.history.append({"role": "assistant", "content": f"Respuesta {i}"})
        
        context = self.agent._build_context()
        
        # El contexto debe tener solo los últimos 5 mensajes
        self.assertIn("Mensaje 9", context)
        self.assertIn("Mensaje 8", context)
        self.assertNotIn("Mensaje 0", context)
    
    def test_clear_history(self):
        """Test de limpieza de historial"""
        # Agregar mensajes
        self.agent.history = [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Response"}
        ]
        
        # Limpiar historial
        self.agent.history = []
        self.agent.save_memory()
        
        # Verificar que está vacío
        self.assertEqual(len(self.agent.history), 0)
        
        # Verificar que se guardó vacío
        with open(self.temp_memory.name, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data), 0)
    
    def test_memory_persistence(self):
        """Test de persistencia de memoria"""
        # Agregar mensaje
        self.agent.history.append({"role": "user", "content": "Persistencia"})
        self.agent.save_memory()
        
        # Crear nuevo agente
        new_agent = PatAgent(memory_path=self.temp_memory.name)
        
        # Verificar que cargó el mensaje
        self.assertEqual(len(new_agent.history), 1)
        self.assertEqual(new_agent.history[0]['content'], 'Persistencia')
    
    def test_invalid_memory_path(self):
        """Test con ruta de memoria inválida"""
        # Intentar cargar desde un directorio que no existe
        invalid_path = "/ruta/inexistente/memory.json"
        agent = PatAgent(memory_path=invalid_path)
        
        # Debería inicializar con historial vacío
        self.assertEqual(len(agent.history), 0)
    
    def test_corrupted_memory_file(self):
        """Test con archivo de memoria corrupto"""
        # Escribir JSON inválido
        with open(self.temp_memory.name, 'w') as f:
            f.write("esto no es json válido {{{")
        
        # Crear agente (debería manejar el error)
        agent = PatAgent(memory_path=self.temp_memory.name)
        
        # Debería inicializar con historial vacío
        self.assertEqual(len(agent.history), 0)
    
    def test_message_format(self):
        """Test de formato de mensajes"""
        message = {"role": "user", "content": "Test"}
        
        self.assertIn('role', message)
        self.assertIn('content', message)
        self.assertIn(message['role'], ['user', 'assistant', 'system'])


class TestPatAgentIntegration(unittest.TestCase):
    """Tests de integración para PatAgent"""
    
    def setUp(self):
        """Configuración antes de cada test"""
        self.temp_memory = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_memory.write('[]')
        self.temp_memory.close()
        
        self.agent = PatAgent(memory_path=self.temp_memory.name)
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if os.path.exists(self.temp_memory.name):
            os.unlink(self.temp_memory.name)
    
    def test_conversation_flow(self):
        """Test de flujo de conversación"""
        # Simular una conversación
        messages = [
            "Hola",
            "¿Qué es Python?",
            "Gracias"
        ]
        
        for msg in messages:
            self.agent.history.append({"role": "user", "content": msg})
            self.agent.history.append({"role": "assistant", "content": f"Respuesta a: {msg}"})
        
        # Verificar que se guardaron todos los mensajes
        self.assertEqual(len(self.agent.history), 6)
        
        # Verificar el orden
        self.assertEqual(self.agent.history[0]['content'], "Hola")
        self.assertEqual(self.agent.history[2]['content'], "¿Qué es Python?")
        self.assertEqual(self.agent.history[4]['content'], "Gracias")


def run_tests():
    """Ejecuta todos los tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()