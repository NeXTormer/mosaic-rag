import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer

from mosaicrs.llm.DeepSeekLLMInterface import DeepSeekLLMInterface
from mosaicrs.llm.T5Transformer import T5Transformer
from tqdm import tqdm
from mosaicrs.llm.LLMInterface import LLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum

# Don't think thats the best idea to limit models like this
# class SupportedSummarizerModels(Enum):
#     Flan_T5_Base = "google/flan-t5-base",
#     T5_Base = "google-t5/t5-base"


class ResultsSummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = 'DeepSeekv3',
                 summarize_prompt: str = "summarize: "):

        # todo: find better way of using deepseek model
        if model == 'DeepSeekv3':
            self.llm = DeepSeekLLMInterface(system_prompt='You are a helpful assistant part of a search engine. You are given a query and documents separated by <SEP>. Please summarize the documents in order to answer the query. Do not use any additional information not available in the given documents.')
        else:
            self.llm = T5Transformer(model)

        self.source_column_name = input_column
        self.target_column_name = output_column
        self.summarize_prompt = summarize_prompt

    # style note: most important class (in this case 'transform' should be at the top, below constructor)
    def transform(self, data: PipelineIntermediate, progress_info: dict = None):
        full_texts = data.documents[self.source_column_name].to_list()
        summarized_texts = []

        print("Summarizing using model: {}".format(self.llm))

        progress_info['step_progress'] = '{}/{}'.format(0, 0)
        progress_info['step_percentage'] = 0

        summary = self.llm.generate("Query: " + data.query + "<SEP>" + "<SEP>".join(full_texts))


        progress_info['step_progress'] = '{1}/{1}'
        progress_info['step_percentage'] = 1


        data.metadata = pd.concat([data.metadata, pd.DataFrame({
            'data': [summary],
            'title': [self.target_column_name],
        })], ignore_index=True)

        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)


        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": ResultsSummarizerStep.get_name(),
            "parameters": {
                'model': {
                    'title': 'Summarizer model',
                    'description': 'LLM model instance to use for summarization. Can be any T5 transformer model.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['DeepSeekv3'],
                    'default': 'DeepSeekv3',
                },
                'input_column': {
                    'title': 'Input column name',
                    'description': 'Column to use for summarization.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output metadata column name',
                    'description': 'The summarized text gets saved to this column..',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['summary'],
                    'default': 'summary',
                },

            }
        }

    @staticmethod
    def get_name() -> str:
        return "Query Summarizer"
