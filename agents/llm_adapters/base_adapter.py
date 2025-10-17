from abc import ABC, abstractmethod
from typing import Dict, List, Generator, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LLMStats:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    last_request_time: Optional[datetime] = None
    average_response_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'total_tokens': self.total_tokens,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'average_response_time': self.average_response_time,
            'success_rate': self.successful_requests / self.total_requests if self.total_requests > 0 else 0
        }


class BaseLLMAdapter(ABC):
    
    def __init__(self, name: str):
        self.name = name
        self.stats = LLMStats()
    
    @abstractmethod
    def generate(self, messages: List[Dict], **kwargs) -> str:
        pass
    
    @abstractmethod
    def stream_generate(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    def get_stats(self) -> Dict:
        return {
            'provider': self.name,
            **self.stats.to_dict()
        }
    
    def _update_stats(self, success: bool, response_time: float = 0.0, tokens: int = 0):
        self.stats.total_requests += 1
        if success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
        
        self.stats.total_tokens += tokens
        self.stats.last_request_time = datetime.now()
        
        if success and response_time > 0:
            total_time = self.stats.average_response_time * (self.stats.successful_requests - 1) + response_time
            self.stats.average_response_time = total_time / self.stats.successful_requests
    
    def reset_stats(self):
        self.stats = LLMStats()
