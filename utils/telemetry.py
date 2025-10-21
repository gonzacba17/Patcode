"""module de OpenTelemetry para observabilidad avanzada de PatCode."""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None
    Resource = None
    TracerProvider = None
    MeterProvider = None

from utils.logger import setup_logger

logger = setup_logger(__name__)


class TelemetryManager:
    """
    Gestor de telemetría con OpenTelemetry.
    
    Proporciona tracing distribuido y métricas para PatCode.
    Soporta exportación a consola, OTLP (Jaeger/Tempo) y backends compatibles.
    """
    
    def __init__(
        self,
        service_name: str = "patcode",
        environment: str = "development",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        otlp_endpoint: Optional[str] = None
    ):
        """
        Inicializa el gestor de telemetría.
        
        Args:
            service_name: Nombre del servicio
            environment: Entorno (development, staging, production)
            enable_tracing: Habilitar tracing
            enable_metrics: Habilitar métricas
            otlp_endpoint: Endpoint OTLP (ej: http://localhost:4317)
        """
        self.service_name = service_name
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint or os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
        
        if not OTEL_AVAILABLE:
            logger.warning(
                "OpenTelemetry no está instalado. "
                "Ejecuta: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
            )
            self.enabled = False
            return
        
        self.enabled = True
        
        resource = Resource.create({
            "service.name": service_name,
            "service.environment": environment,
            "service.version": "0.5.0"
        })
        
        if enable_tracing:
            self._setup_tracing(resource)
        
        if enable_metrics:
            self._setup_metrics(resource)
        
        logger.info(f"Telemetría inicializada: {service_name} ({environment})")
    
    def _setup_tracing(self, resource: 'Resource'):
        """Configura el sistema de tracing."""
        provider = TracerProvider(resource=resource)
        
        if self.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP trace exporter configurado: {self.otlp_endpoint}")
        else:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.debug("Console trace exporter configurado")
        
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)
    
    def _setup_metrics(self, resource: 'Resource'):
        """Configura el sistema de métricas."""
        if self.otlp_endpoint:
            exporter = OTLPMetricExporter(endpoint=self.otlp_endpoint, insecure=True)
        else:
            exporter = ConsoleMetricExporter()
        
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        
        self.meter = metrics.get_meter(__name__)
        
        self.request_counter = self.meter.create_counter(
            "patcode.requests.total",
            description="Total de requests procesados"
        )
        
        self.latency_histogram = self.meter.create_histogram(
            "patcode.latency.ms",
            description="Latencia de operaciones en ms"
        )
        
        self.token_counter = self.meter.create_counter(
            "patcode.tokens.used",
            description="Tokens consumidos por LLM"
        )
        
        logger.info("Métricas configuradas")
    
    @contextmanager
    def trace_operation(self, operation_name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Context manager para tracing de operaciones.
        
        Args:
            operation_name: Nombre de la operación
            attributes: Atributos adicionales del span
        
        Example:
            with telemetry.trace_operation("llm.generate", {"model": "codellama"}):
                response = llm.generate(prompt)
        """
        if not self.enabled or not hasattr(self, 'tracer'):
            yield
            return
        
        with self.tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            start_time = time.time()
            try:
                yield span
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("duration.ms", duration_ms)
                
                if hasattr(self, 'latency_histogram'):
                    self.latency_histogram.record(
                        duration_ms,
                        {"operation": operation_name}
                    )
    
    def record_request(self, method: str, status: str = "success"):
        """Registra una request procesada."""
        if not self.enabled or not hasattr(self, 'request_counter'):
            return
        
        self.request_counter.add(1, {"method": method, "status": status})
    
    def record_tokens(self, count: int, provider: str, model: str):
        """Registra tokens consumidos."""
        if not self.enabled or not hasattr(self, 'token_counter'):
            return
        
        self.token_counter.add(count, {"provider": provider, "model": model})
    
    def shutdown(self):
        """Cierra los exportadores de telemetría."""
        if not self.enabled:
            return
        
        logger.info("Cerrando telemetría...")


_global_telemetry: Optional[TelemetryManager] = None


def get_telemetry() -> TelemetryManager:
    """
    Obtiene la instancia global de telemetría.
    
    Returns:
        TelemetryManager configurado
    """
    global _global_telemetry
    
    if _global_telemetry is None:
        _global_telemetry = TelemetryManager()
    
    return _global_telemetry


def init_telemetry(**kwargs) -> TelemetryManager:
    """
    Inicializa telemetría con configuración personalizada.
    
    Args:
        **kwargs: Argumentos para TelemetryManager
    
    Returns:
        TelemetryManager configurado
    """
    global _global_telemetry
    _global_telemetry = TelemetryManager(**kwargs)
    return _global_telemetry
