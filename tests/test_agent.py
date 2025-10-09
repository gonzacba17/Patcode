"""
Corrección para el método setUp en test_agent.py

Busca el método setUp y asegúrate de que cree self.agent
"""

import unittest
import tempfile
import os
from pathlib import Path

# Ajusta este import según la ubicación real de tu clase
from agents.pat_agent import PatAgent  # O el nombre correcto de tu agente


class TestPatAgent(unittest.TestCase):
    """Tests para la clase PatAgent"""
    
    def setUp(self):
        """Configuración antes de cada test"""
        # Crear archivo temporal para memoria
        self.temp_memory = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_memory.close()
        
        # ✅ CRÍTICO: Inicializar el agente aquí
        # Ajusta los parámetros según tu implementación real
        try:
            self.agent = PatAgent(memory_file=self.temp_memory.name)
        except TypeError:
            # Si PatAgent no acepta memory_file como parámetro, ajusta aquí
            self.agent = PatAgent()
            self.agent.memory_file = Path(self.temp_memory.name)
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if os.path.exists(self.temp_memory.name):
            os.unlink(self.temp_memory.name)
    
    def test_initialization(self):
        """Test de inicialización del agente"""
        # Verificar que el agente fue creado
        self.assertIsNotNone(self.agent)
        
        # Verificar el archivo de memoria
        self.assertEqual(str(self.agent.memory_file), str(self.temp_memory.name))
    
    # ... resto de tus tests


if __name__ == '__main__':
    unittest.main()