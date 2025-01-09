from abc import ABC, abstractmethod
from typing import Any
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate


class DataSource(ABC):

    @abstractmethod
    def request_data(self, data: PipelineIntermediate) -> PipelineIntermediate:
        pass

    @abstractmethod
    def get_info(self) -> dict:
        pass