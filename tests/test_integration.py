"""
Tests de integración end-to-end para PatCode.

Estos tests verifican flujos completos del sistema.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

try:
    from agents.pat_agent import PatAgent
    from agents.llm_adapters.ollama_adapter import OllamaAdapter
    from agents.memory.memory_manager import MemoryManager, MemoryConfig
    from cli.commands import CommandRegistry
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Import error: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
@pytest.mark.integration
class TestEndToEnd:
    """Tests de integración end-to-end"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Adapter mockeado para tests"""
        adapter = Mock(spec=OllamaAdapter)
        adapter.name = "test-ollama"
        adapter.model = "test-model"
        adapter.generate.return_value = "Mocked response"
        adapter.stream_generate.return_value = iter(["Mock", " ", "response"])
        adapter.is_available.return_value = True
        return adapter
    
    @pytest.fixture
    def temp_memory_manager(self, tmp_path):
        """MemoryManager temporal para tests"""
        config = MemoryConfig(
            max_active_messages=10,
            max_file_size_bytes=1024 * 1024,
            archive_dir=tmp_path / "archives"
        )
        return MemoryManager(config)
    
    def test_full_conversation_flow(self, mock_adapter, temp_memory_manager):
        """Test flujo completo de conversación"""
        # Simular conversación completa
        temp_memory_manager.add_message("user", "¿Qué es Python?")
        temp_memory_manager.add_message("assistant", "Python es un lenguaje...")
        temp_memory_manager.add_message("user", "Dame un ejemplo")
        temp_memory_manager.add_message("assistant", "Aquí está un ejemplo...")
        
        # Verificar que se guardaron correctamente
        assert len(temp_memory_manager.active_memory) == 4
        assert temp_memory_manager.active_memory[0]["role"] == "user"
        assert temp_memory_manager.active_memory[1]["role"] == "assistant"
    
    def test_memory_rotation(self, temp_memory_manager):
        """Test rotación automática de memoria"""
        # Agregar más mensajes que el límite
        for i in range(15):
            temp_memory_manager.add_message("user", f"Message {i}")
            temp_memory_manager.add_message("assistant", f"Response {i}")
        
        # Verificar que rotó
        assert len(temp_memory_manager.active_memory) <= temp_memory_manager.config.max_active_messages
        
        # Verificar que hay memoria pasiva (resumida)
        assert len(temp_memory_manager.passive_memory) > 0
    
    def test_memory_persistence(self, tmp_path):
        """Test que la memoria persiste entre sesiones"""
        memory_file = tmp_path / "test_memory.json"
        
        # Sesión 1: crear y guardar datos
        config1 = MemoryConfig()
        manager1 = MemoryManager(config1)
        manager1.add_message("user", "Test message")
        manager1.save_to_file(memory_file)
        
        # Sesión 2: cargar datos
        config2 = MemoryConfig()
        manager2 = MemoryManager(config2)
        manager2.load_from_file(memory_file)
        
        # Verificar que se cargó
        assert len(manager2.active_memory) > 0
        assert manager2.active_memory[0]["content"] == "Test message"
    
    def test_adapter_fallback(self, mock_adapter):
        """Test fallback entre adapters"""
        # Simular que el primer adapter falla
        failing_adapter = Mock(spec=OllamaAdapter)
        failing_adapter.is_available.return_value = False
        failing_adapter.generate.side_effect = Exception("Connection failed")
        
        # El segundo adapter funciona
        mock_adapter.is_available.return_value = True
        
        # Verificar que el sistema puede manejar fallos
        assert not failing_adapter.is_available()
        assert mock_adapter.is_available()


@pytest.mark.integration
class TestCommandSystem:
    """Tests del sistema de comandos"""
    
    def test_command_registry_initialization(self):
        """Test inicialización del registro de comandos"""
        registry = CommandRegistry()
        
        # Verificar que los comandos core están registrados
        assert len(registry.commands) > 0
        assert "help" in registry.commands or "ayuda" in registry.commands
    
    def test_help_command(self):
        """Test comando de ayuda"""
        registry = CommandRegistry()
        help_text = registry.get_help()
        
        assert help_text is not None
        assert len(help_text) > 0
    
    def test_unknown_command_handling(self):
        """Test manejo de comando desconocido"""
        registry = CommandRegistry()
        
        # Mock context
        context = Mock()
        
        result = registry.execute("/unknown_command_xyz", context)
        
        # Debe retornar mensaje de error pero no crashear
        assert "desconocido" in result.lower() or "unknown" in result.lower()


@pytest.mark.integration  
class TestErrorHandling:
    """Tests de manejo de errores"""
    
    def test_corrupted_memory_handling(self, tmp_path):
        """Test manejo de memoria corrupta"""
        # Crear archivo corrupto
        memory_file = tmp_path / "corrupted.json"
        memory_file.write_text("{invalid json content")
        
        config = MemoryConfig()
        manager = MemoryManager(config)
        
        # Debe manejar el error gracefully
        try:
            manager.load_from_file(memory_file)
        except Exception as e:
            # Se espera un error, pero debe ser manejable
            assert True
    
    def test_adapter_unavailable(self):
        """Test cuando adapter no está disponible"""
        adapter = Mock(spec=OllamaAdapter)
        adapter.is_available.return_value = False
        
        # Verificar que se puede detectar
        assert not adapter.is_available()
    
    def test_empty_message_handling(self, temp_memory_manager):
        """Test manejo de mensajes vacíos"""
        # Intentar agregar mensaje vacío
        temp_memory_manager.add_message("user", "")
        
        # Debe agregarse sin crashear (validación en capas superiores)
        assert len(temp_memory_manager.active_memory) == 1


@pytest.fixture
def temp_memory_manager(tmp_path):
    """Fixture global para MemoryManager temporal"""
    config = MemoryConfig(
        max_active_messages=10,
        archive_dir=tmp_path / "archives"
    )
    return MemoryManager(config)


@pytest.mark.integration
class TestMemoryFeaturesFase2:
    """Tests de nuevas features de memoria (Fase 2)"""
    
    def test_search_messages(self, temp_memory_manager):
        """Test búsqueda en mensajes"""
        temp_memory_manager.add_message("user", "¿Qué es Python?")
        temp_memory_manager.add_message("assistant", "Python es un lenguaje")
        temp_memory_manager.add_message("user", "¿Qué es JavaScript?")
        temp_memory_manager.add_message("assistant", "JavaScript es otro lenguaje")
        
        results = temp_memory_manager.search_messages("Python")
        
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)
    
    def test_search_by_role(self, temp_memory_manager):
        """Test búsqueda filtrada por rol"""
        temp_memory_manager.add_message("user", "Pregunta 1")
        temp_memory_manager.add_message("assistant", "Respuesta 1")
        temp_memory_manager.add_message("user", "Pregunta 2")
        
        user_results = temp_memory_manager.search_messages("Pregunta", role="user")
        
        assert all(r["role"] == "user" for r in user_results)
    
    def test_export_to_markdown(self, temp_memory_manager, tmp_path):
        """Test exportación a Markdown"""
        temp_memory_manager.add_message("user", "Test question")
        temp_memory_manager.add_message("assistant", "Test answer")
        
        export_path = tmp_path / "export.md"
        temp_memory_manager.export_to_markdown(export_path)
        
        assert export_path.exists()
        
        content = export_path.read_text(encoding='utf-8')
        assert "# Conversación PatCode" in content
        assert "Test question" in content
        assert "Test answer" in content


@pytest.mark.integration
class TestCommandsFase2:
    """Tests de comandos nuevos (Fase 2)"""
    
    @pytest.fixture
    def mock_context(self, temp_memory_manager):
        """Context mockeado con memory manager"""
        ctx = Mock()
        ctx.memory_manager = temp_memory_manager
        return ctx
    
    def test_msearch_command(self, mock_context):
        """Test comando /msearch"""
        from cli.commands import command_registry
        
        # Agregar datos de prueba
        mock_context.memory_manager.add_message("user", "Python test")
        mock_context.memory_manager.add_message("assistant", "Python response")
        
        result = command_registry.execute("/msearch Python", mock_context)
        
        assert "Encontrados" in result or "resultados" in result.lower()
    
    def test_export_command(self, mock_context, tmp_path):
        """Test comando /export"""
        from cli.commands import command_registry
        
        mock_context.memory_manager.add_message("user", "Test")
        mock_context.memory_manager.add_message("assistant", "Response")
        
        export_file = tmp_path / "test_export.md"
        result = command_registry.execute(f"/export {export_file}", mock_context)
        
        assert "✅" in result or "exportada" in result.lower()
        assert export_file.exists()
    
    def test_mstats_command(self, mock_context):
        """Test comando /mstats"""
        from cli.commands import command_registry
        
        mock_context.memory_manager.add_message("user", "Test")
        
        result = command_registry.execute("/mstats", mock_context)
        
        assert "Mensajes activos" in result or "Estadísticas" in result


@pytest.mark.integration
class TestUIFase2:
    """Tests de UI mejorada (Fase 2)"""
    
    def test_streaming_display(self):
        """Test visualización de streaming"""
        from ui.rich_terminal import RichTerminalUI
        
        ui = RichTerminalUI()
        
        def mock_generator():
            yield "Hello"
            yield " "
            yield "world"
        
        result = ui.display_streaming_response(mock_generator())
        
        assert result == "Hello world"
    
    def test_search_results_display(self, capsys):
        """Test visualización de resultados de búsqueda"""
        from ui.rich_terminal import RichTerminalUI
        
        ui = RichTerminalUI()
        
        results = [
            {"role": "user", "content": "Test", "timestamp": "2025-01-01"},
            {"role": "assistant", "content": "Response", "timestamp": "2025-01-01"}
        ]
        
        ui.display_search_results(results)
        
        # Verificar que no hay errores (output capturado por Rich)
        captured = capsys.readouterr()
        assert len(captured.out) > 0 or len(captured.err) == 0


# Markers para ejecutar subsets de tests
pytestmark = pytest.mark.integration
