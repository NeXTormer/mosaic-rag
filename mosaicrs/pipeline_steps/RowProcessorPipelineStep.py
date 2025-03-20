import hashlib
from abc import abstractmethod
from typing import Optional

from tqdm import tqdm

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep


class RowProcessorPipelineStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str):
        super().__init__()
        self.input_column = input_column
        self.output_column = output_column


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler) -> PipelineIntermediate:
        inputs = [entry if entry is not None else "" for entry in data.documents[self.input_column].to_list()]
        outputs = []
        column_type = None

        handler.update_progress(0, len(inputs))

        # TODO: implement multithreading
        for input in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1((self.get_cache_fingerprint() + str(input)).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None:
                output, returned_column_type = self.transform_row(input, handler)

                handler.put_cache(input_hash, output)
                handler.put_cache(input_hash + 'column_type', returned_column_type)

                if returned_column_type is not column_type:
                    handler.log(self.get_name() + ": column type: " + returned_column_type)

                if returned_column_type is not None:
                    column_type = returned_column_type

            else:
                column_type = handler.get_cache(input_hash + 'column_type')

            outputs.append(output)
            handler.increment_progress()

        data.documents[self.output_column] = outputs
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)


        if column_type is not None:
            data.set_column_type(self.output_column, column_type)

        return data


    @abstractmethod
    def transform_row(self, data, handler: PipelineStepHandler) -> (any, Optional[str]):
        pass

    @abstractmethod
    def get_cache_fingerprint(self) -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_info() -> dict:
        pass

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass