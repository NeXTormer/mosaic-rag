import json

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.EmbeddingRerankerStep import EmbeddingRerankerStep
from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.SummarizerStep import SummarizerStep

pipeline_steps_mapping = {
    "mosaic_datasource": MosaicDataSource,
    "llm_summarizer": SummarizerStep,
    "embedding_reranker": EmbeddingRerankerStep
}


def run(pipeline):
    steps = pipeline['pipeline']
    keys = sorted([int(x) for x in steps.keys()])

    data = PipelineIntermediate()

    for key in keys:
        step_id = steps[str(key)][id]
        step_parameters = steps[str(key)]['parameters']

        step = _get_class_from_id_and_parameters(step_id, step_parameters)

        #TODO: implement history
        data = step.transform(data)

    return data


def _get_class_from_id_and_parameters(step_id: str, step_parameters: dict) -> PipelineStep:
    cls = pipeline_steps_mapping[step_id]
    instance = cls(**step_parameters)

    return instance




# js = """
# {
#   "pipeline": {
#     "1": {
#       "id": "mosaic_datasource",
#       "parameters": {
#         "query": "werner",
#         "limit": 200
#       }
#     },
#      "2": {
#       "id": "llm_summarizer",
#       "parameters": {
#         "model": "t5-base",
#         "input_column": "full_text",
#         "output_column": "summary"
#       }
#     },
#      "3": {
#       "id": "embedding_reranker",
#       "parameters": {
#         "input_column": "summary",
#         "model": "llama3.1-8B"
#       }
#     }
#   }
# }
# """
#
#
#
# run(json.loads(js))
