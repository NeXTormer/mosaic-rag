import typing
from abc import ABC, abstractmethod

import pandas as pd


class Endpoint(ABC):

    @abstractmethod
    def process(self, data: pd.DataFrame, query: str) -> typing.Any:
        pass