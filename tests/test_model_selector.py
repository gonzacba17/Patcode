import pytest
from unittest.mock import patch, MagicMock
from config.model_selector import ModelSelector, ModelProfile


@pytest.fixture
def selector():
    return ModelSelector()


def test_selector_init(selector):
    """Verifica inicialización"""
    assert selector.system_info is not None
    assert 'total_ram_gb' in selector.system_info
    assert 'available_ram_gb' in selector.system_info


def test_detect_hardware(selector):
    """Verifica detección de hardware"""
    info = selector.system_info
    assert info['total_ram_gb'] > 0
    assert info['available_ram_gb'] > 0
    assert info['cpu_count'] > 0


def test_recommend_model_general(selector):
    """Verifica recomendación para caso general"""
    model = selector.recommend_model(use_case='general')
    assert model in selector.MODELS


def test_recommend_model_fast(selector):
    """Verifica que con RAM baja recomiende modelo ligero"""
    selector.system_info['available_ram_gb'] = 4
    
    model = selector.recommend_model(use_case='general')
    profile = selector.get_model_info(model)
    
    assert profile.ram_min <= 4


def test_get_model_info(selector):
    """Verifica obtención de info de modelo"""
    info = selector.get_model_info('llama3.2:3b')
    assert isinstance(info, ModelProfile)
    assert info.name == 'llama3.2:3b'
    assert info.speed in ['fast', 'balanced', 'deep']


@patch('psutil.virtual_memory')
def test_list_compatible_models(mock_ram):
    """Test model selection with sufficient RAM (mocked)"""
    
    mock_ram.return_value = MagicMock(
        available=16 * 1024**3,
        total=32 * 1024**3,
        percent=50.0
    )
    
    selector = ModelSelector()
    compatible = selector.list_compatible_models()
    
    print(f"\n=== DEBUG ===")
    print(f"RAM available (mocked): 16 GB")
    print(f"System RAM detected: {selector.system_info['available_ram_gb']:.2f} GB")
    print(f"Compatible models: {compatible}")
    print(f"Number of models: {len(compatible)}")
    
    assert isinstance(compatible, list)
    assert len(compatible) > 0, f"Expected models but got empty list with 16 GB RAM (mocked)"


def test_speed_recommendation(selector):
    """Verifica recomendación de velocidad"""
    rec = selector.get_speed_recommendation('llama3.2:1b')
    assert isinstance(rec, str)
    assert any(emoji in rec for emoji in ['⚠️', '⚡', '✅'])


def test_should_use_cache(selector):
    """Verifica decisión de usar cache"""
    assert selector.should_use_cache('codellama:13b') == True
    
    assert selector.should_use_cache('unknown_model') == True


def test_model_profiles_valid(selector):
    """Verifica que todos los perfiles sean válidos"""
    for model_name, profile in selector.MODELS.items():
        assert profile.name == model_name
        assert profile.ram_min > 0
        assert profile.ram_recommended >= profile.ram_min
        assert profile.speed in ['fast', 'balanced', 'deep']
        assert len(profile.use_cases) > 0
        assert profile.parameters


def test_recommend_for_refactor(selector):
    """Verifica recomendación para refactoring"""
    model = selector.recommend_model(use_case='refactor')
    profile = selector.get_model_info(model)
    
    assert profile is not None
    if selector.system_info['available_ram_gb'] >= 8:
        assert profile.speed in ['balanced', 'deep']


def test_fallback_model(selector):
    """Verifica fallback cuando RAM es muy baja"""
    selector.system_info['available_ram_gb'] = 2
    
    model = selector.recommend_model(use_case='general')
    
    assert model == 'llama3.2:1b'
