from abc import ABC, abstractmethod
import pandas as pd

#TODO: Namensgebung überdenken
#TODO: Parameter hinzufügen, ob Daten im gleichen Format bleiben oder nicht
#TODO: Aufsplitten zwischen Selection Operatoren und Veränderunge Operatoren?

class Transformer(ABC):

    @abstractmethod
    def transform(self, data: pd.DataFrame, query: str) -> pd.DataFrame:
        pass