from abc import ABC, abstractmethod
import pandas as pd

class Transformer(ABC):

    @abstractmethod
    def transform(self, data: pd.DataFrame, query: str) -> pd.DataFrame:
        pass