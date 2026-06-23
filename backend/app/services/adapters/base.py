from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator, Tuple
from decimal import Decimal

class BaseAdapter(ABC):
    @abstractmethod
    def get_base_url(self) -> str:
        pass

    @abstractmethod
    def prepare_request(self, body: Dict[str, Any], api_key: str) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """Returns (url, headers, body)"""
        pass

    @abstractmethod
    def extract_tokens(self, response_body: Dict[str, Any]) -> Tuple[int, int]:
        """Returns (input_tokens, output_tokens)"""
        pass

    @abstractmethod
    def detect_tool_use(self, response_body: Dict[str, Any]) -> Tuple[bool, str]:
        """Returns (is_tool_call, tool_name)"""
        pass

    @abstractmethod
    def get_pricing(self, model: str) -> Dict[str, float]:
        """Returns {'input': price_per_m, 'output': price_per_m}"""
        pass

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        pricing = self.get_pricing(model)
        in_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * Decimal(pricing['input'])
        out_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * Decimal(pricing['output'])
        return in_cost + out_cost
