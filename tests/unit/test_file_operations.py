import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from utils.file_manager import FileManager
from tools.base_tool import ToolResult


class TestFileManager:
    
    @pytest.fixture
    def file_manager(self):
        return FileManager()
    
    def test_file_manager_initialization(self, file_manager):
        assert len(file_manager.loaded_files) == 0
        assert file_manager.max_total_size_kb > 0
    
    def test_get_stats(self, file_manager):
        stats = file_manager.get_stats()
        assert "total_files" in stats
        assert "total_size_kb" in stats
        assert "usage_percent" in stats
        assert stats["total_files"] == 0


class TestToolResult:
    
    def test_tool_result_success(self):
        result = ToolResult(
            success=True,
            data="test data",
            metadata={"time": 100}
        )
        
        assert result.success is True
        assert result.data == "test data"
        assert result.error is None
        assert result.metadata["time"] == 100
    
    def test_tool_result_failure(self):
        result = ToolResult(
            success=False,
            error="test error"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "test error"
    
    def test_tool_result_to_dict(self):
        result = ToolResult(
            success=True,
            data="test",
            metadata={"key": "value"}
        )
        
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["data"] == "test"
        assert result_dict["metadata"]["key"] == "value"
