from typing import Optional, List, Dict
from abc import ABC, abstractmethod

class LLMInterface(ABC):
    def __init__(self,
                 model: Optional[str] = None,
                 system_prompt: Optional[str] = None
                 ) -> None:
        self.model = model
        self.system_prompt = system_prompt


    @abstractmethod
    def generate(self, prompt: str):
        pass


    @abstractmethod
    def chat(
            self,
            conversation: List[Dict[str, str]],
    ) -> str:
        pass