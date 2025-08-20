from abc import ABC, abstractmethod
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler

class PipelineStep(ABC):

    @abstractmethod
    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler) -> PipelineIntermediate:
        pass

    @staticmethod
    @abstractmethod
    def get_info() -> dict:
        pass

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass
