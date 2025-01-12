from abc import ABC, abstractmethod

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate


class PipelineStep(ABC):

    @abstractmethod
    def transform(self, data: PipelineIntermediate) -> PipelineIntermediate:
        pass

    @staticmethod
    @abstractmethod
    def get_info() -> dict:
        pass

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass
