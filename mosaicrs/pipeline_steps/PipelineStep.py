from abc import ABC, abstractmethod

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate


class PipelineStep(ABC):

    @abstractmethod
    def transform(self, data: PipelineIntermediate) -> PipelineIntermediate:
        pass

    @abstractmethod
    def get_info(self) -> dict:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
