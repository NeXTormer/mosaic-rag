from abc import ABC, abstractmethod
from typing import Any


class DataSource(ABC):

    @abstractmethod
    def request_data(self, query: str, arguments: dict[str, Any] | None):
        pass