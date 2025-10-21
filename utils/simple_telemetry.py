"""Sistema de telemetría simple sin dependencias externas"""

import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict, deque
from contextlib import contextmanager
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class Metric:
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class Event:
    type: str
    message: str
    timestamp: float
    level: str = "info"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SimpleTelemetry:
    
    def __init__(self, storage_path: Optional[Path] = None, max_metrics: int = 10000):
        self.storage_path = storage_path
        self.max_metrics = max_metrics
        
        self.metrics: deque = deque(maxlen=max_metrics)
        self.events: deque = deque(maxlen=max_metrics)
        
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = {}
        
        logger.info("SimpleTelemetry inicializado")
    
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] = None,
        unit: str = ""
    ):
        metric = Metric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            unit=unit
        )
        
        self.metrics.append(metric)
        
        if name.startswith("count."):
            self.counters[name] += int(value)
        elif name.startswith("gauge."):
            self.gauges[name] = value
        elif name.startswith("timer."):
            self.timers[name].append(value)
    
    def record_event(
        self,
        event_type: str,
        message: str,
        level: str = "info",
        metadata: Dict[str, Any] = None
    ):
        event = Event(
            type=event_type,
            message=message,
            timestamp=time.time(),
            level=level,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        
        if level == "error":
            logger.error(f"[{event_type}] {message}")
        elif level == "warning":
            logger.warning(f"[{event_type}] {message}")
        else:
            logger.debug(f"[{event_type}] {message}")
    
    def increment(self, counter_name: str, value: int = 1, tags: Dict[str, str] = None):
        self.record_metric(f"count.{counter_name}", value, tags)
    
    def gauge(self, gauge_name: str, value: float, tags: Dict[str, str] = None):
        self.record_metric(f"gauge.{gauge_name}", value, tags)
    
    @contextmanager
    def timer(self, timer_name: str, tags: Dict[str, str] = None):
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.record_metric(f"timer.{timer_name}", duration, tags, unit="seconds")
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "total_metrics": len(self.metrics),
            "total_events": len(self.events),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {}
        }
        
        for name, values in self.timers.items():
            if values:
                stats["timers"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "total": sum(values)
                }
        
        return stats
    
    def get_recent_events(self, limit: int = 50, level: str = None) -> List[Event]:
        events = list(self.events)
        
        if level:
            events = [e for e in events if e.level == level]
        
        return events[-limit:]
    
    def get_metrics_by_name(self, metric_name: str, limit: int = 100) -> List[Metric]:
        return [
            m for m in list(self.metrics)[-limit:]
            if m.name == metric_name
        ]
    
    def export_to_json(self, output_path: Path):
        data = {
            "stats": self.get_stats(),
            "metrics": [m.to_dict() for m in self.metrics],
            "events": [e.to_dict() for e in self.events],
            "exported_at": datetime.now().isoformat()
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Telemetría exportada a {output_path}")
    
    def clear(self):
        self.metrics.clear()
        self.events.clear()
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()
        logger.info("Telemetría limpiada")

telemetry = SimpleTelemetry()
