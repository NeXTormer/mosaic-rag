import json
import threading
import time
import uuid
from typing import Any
import traceback

import pandas as pd

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.ContentExtractorStep import ContentExtractorStep
from mosaicrs.pipeline_steps.EmbeddingRerankerStep import EmbeddingRerankerStep
from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.DocumentSummarizerStep import DocumentSummarizerStep
from mosaicrs.pipeline_steps.ResultsSummarizerStep import ResultsSummarizerStep
from mosaicrs.pipeline_steps.WordCounterStep import WordCounterStep
from mosaicrs.pipeline_steps.TFIDFRerankerStep import TFIDFRerankerStep
from mosaicrs.pipeline_steps.PunctuationRemovalStep import PunctuationRemovalStep
from mosaicrs.pipeline_steps.StopwordRemovalStep import StopWordRemovalStep
from mosaicrs.pipeline_steps.TextStemmerStep import TextStemmerStep
from mosaicrs.pipeline_steps.BasicSentimentAnalysisStep import BasicSentimentAnalysisStep
# from mosaicrs.pipeline_steps.TextLemmatizationStep import TextLemmatizerStep

pipeline_steps_mapping = {
    "mosaic_datasource": MosaicDataSource,
    "llm_summarizer": DocumentSummarizerStep,
    "all_results_summarizer": ResultsSummarizerStep,
    "content_extractor": ContentExtractorStep,
    "embedding_reranker": EmbeddingRerankerStep,
    "word_counter": WordCounterStep,
    "tf_idf_reranker": TFIDFRerankerStep,
    "punctuation_removal": PunctuationRemovalStep,
    "stopword_removal": StopWordRemovalStep,
    "text_stemmer": TextStemmerStep,
    "basic_sentiment_analysis": BasicSentimentAnalysisStep,
    # "text_lemmatization": TextLemmatizerStep
}

class PipelineTask:
    def __init__(self, pipeline):
        self.start_time = None
        self.end_time = None
        self.pipeline = pipeline
        self.pipeline_handler = PipelineStepHandler()
        self.thread_args = {
            'current_step': '',
            'pipeline_step_handler': self.pipeline_handler,
            'pipeline_progress': '0',
            'pipeline_percentage': 0,
            'result': None,
        }

        self.uuid = uuid.uuid4().hex
        self.thread = threading.Thread(target=_run_pipeline, args=(self.pipeline, self.thread_args))

        self.final_df: pd.DataFrame = pd.DataFrame()


    def start(self):
        self.pipeline_handler.log('Executing pipeline with ID: ' + str(self.uuid))
        self.start_time = time.time()
        self.thread.start()

    def join(self):
        self.thread.join()


    def cancel(self):
        self.pipeline_handler.should_cancel = True
        self.thread.join()


    def get_status(self) -> dict[str, Any]:
        progress = {
            'current_step': self.thread_args['current_step'],
            'current_step_index': self.thread_args['current_step_index'],
            'pipeline_progress': self.thread_args['pipeline_progress'],
            'pipeline_percentage': self.thread_args['pipeline_percentage'],
            'log': [],
            'step_output': {
                '1': {
                    'log': 'Getting 1000 documents',
                }
            }
        }
        progress.update(self.pipeline_handler.get_status())

        result = None
        if self.thread_args['has_finished']:
            intermediate: PipelineIntermediate = self.thread_args['intermediate_data']

            self.final_df = intermediate.documents

            result = {
                'data': intermediate.documents.to_json(orient='records'),
                'result_description': f"Retrieved {len(intermediate.documents)} documents in {_format_seconds(self.thread_args['elapsed_time'])} seconds. {int(self.thread_args['cache_hit_ratio'] * 100)}% cache hits.",
                'aggregated_data': intermediate.aggregated_data.to_json(orient='records'),
                'metadata': intermediate.metadata.to_json(orient='records'),
            }


        data =  {
            'has_finished': self.thread_args['has_finished'],
            'progress': progress,
            'result': result,
        }



        return data


def _run_pipeline(pipeline, args):
    _start_time = time.time()

    steps = pipeline['pipeline']
    query = ''
    parameters = {}

    handler: PipelineStepHandler = args['pipeline_step_handler']

    if 'query' in steps:
        query = steps['query']
        del steps['query']

    if 'parameters' in steps:
        parameters = steps['parameters']
        del steps['parameters']

    current_step_index = 0
    total_steps = len(steps)

    args['current_step'] = 'Starting...'
    args['step_progress'] = ''
    args['step_percentage'] = 0
    args['pipeline_progress'] = str(current_step_index) + '/' + str(total_steps)
    args['pipeline_percentage'] = 0

    args['intermediate_data'] = None

    args['has_finished'] = False


    handler.log("Running pipeline. Query: " + query)

    keys = sorted([int(x) for x in steps.keys()])

    data = PipelineIntermediate(query=query, arguments=parameters)

    for key in keys:
        step_id = steps[str(key)]['id']
        step_parameters = steps[str(key)]['parameters']

        handler.log("Processing " + step_id)

        step = _get_class_from_id_and_parameters(step_id, step_parameters)


        args['current_step'] = step.get_name()
        args['current_step_index'] = key
        args['pipeline_progress'] = str(current_step_index) + '/' + str(total_steps)
        args['pipeline_percentage'] = current_step_index / total_steps

        handler.reset(step_id)
        try:
            data = step.transform(data, handler=handler)
        except Exception as e:
            handler.log('{}: {}'.format(type(e).__name__, e))
            handler.log(traceback.format_exc())
            break

        current_step_index += 1

    args['pipeline_progress'] = str(current_step_index) + '/' + str(total_steps)
    args['step_percentage'] = 1
    args['pipeline_percentage'] = 1

    _end_time = time.time()

    handler.log_cache_statistics()
    handler.log(f'Finished task in {_end_time - _start_time} seconds.')


    args['elapsed_time'] = _end_time - _start_time
    args['cache_hit_ratio'] = handler.get_cache_hit_ratio()

    args['intermediate_data'] = data
    args['has_finished'] = True


def _get_class_from_id_and_parameters(step_id: str, step_parameters: dict) -> PipelineStep:
    cls = pipeline_steps_mapping[step_id]

    instance = cls(**step_parameters)

    return instance

def get_pipeline_info():
    all_steps = {}
    for k, v in pipeline_steps_mapping.items():
        info = v.get_info()

        all_steps[k] = info

    return json.dumps(all_steps)


def _format_seconds(seconds):
    if seconds < 1:
        return f"{seconds:.3f}"
    elif seconds < 10:
        return f"{seconds:.2f}"
    else:
        return f"{seconds:.1f}"
