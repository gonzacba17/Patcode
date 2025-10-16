"""
Decorator para reintentar funciones con backoff exponencial.
"""
import time
import functools
from typing import Callable, Tuple, Type
from utils.logger import setup_logger

logger = setup_logger(__name__)

def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator que reintenta una función si falla.
    
    Args:
        max_attempts: Número máximo de intentos
        initial_delay: Delay inicial en segundos
        backoff_factor: Multiplicador del delay en cada intento
        exceptions: Tupla de excepciones a capturar
    
    Example:
        @retry_with_backoff(max_attempts=3)
        def unstable_api_call():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Intento {attempt}/{max_attempts}: {func.__name__}")
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} falló (intento {attempt}): {str(e)}"
                    )
                    
                    if attempt < max_attempts:
                        logger.info(f"Reintentando en {delay:.1f}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"Todos los intentos fallaron para {func.__name__}",
                            exc_info=True
                        )
            
            raise last_exception
        
        return wrapper
    return decorator
