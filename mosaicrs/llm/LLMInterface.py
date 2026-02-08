from typing import Optional, List, Dict
from abc import ABC, abstractmethod

class LLMInterface(ABC):
    def __init__(self,
                 ) -> None:
        pass

    @abstractmethod
    def generate(self, prompt: str, model: str):
        pass


    @abstractmethod
    def chat(self, model: str, conversation: List[Dict[str, str]]) -> str:
        pass