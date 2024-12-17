from typing import List, Any, Dict

from mosaicrs.data_source import DataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps import PipelineStep


class Pipeline(object):

    def __init__(self, steps: List):
        self.steps = steps


    def run(self, data: PipelineIntermediate) -> PipelineIntermediate:
        for i, step in enumerate(self.steps):
            if i == 0:
                data = step.request_data(data)

            else:
                data = step.transform(data)


        return data

