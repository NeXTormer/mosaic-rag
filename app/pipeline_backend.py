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

    query = ''
    parameters = {}

    if 'query' in steps:
        query = steps['query']
        del steps['query']

    if 'parameters' in steps:
        parameters = steps['parameters']
        del steps['parameters']

    keys = sorted([int(x) for x in steps.keys()])

    data = PipelineIntermediate(query=query, arguments=parameters)

    for key in keys:
        step_id = steps[str(key)]['id']
        step_parameters = steps[str(key)]['parameters']

        print("Processing " + step_id)

        step = _get_class_from_id_and_parameters(step_id, step_parameters)


        data = step.transform(data)



    return data


def get_pipeline_info():
    for k, v in pipeline_steps_mapping.items():
        print(v.get_info())


def _get_class_from_id_and_parameters(step_id: str, step_parameters: dict) -> PipelineStep:
    cls = pipeline_steps_mapping[step_id]
    instance = cls(**step_parameters)

    return instance
