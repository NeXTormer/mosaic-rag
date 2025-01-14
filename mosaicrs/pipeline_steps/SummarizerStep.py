import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer
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


class SummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = 'google/flan-t5-base',
                 system_prompt: str = "summarize: "):

        self.llm = T5Transformer(model)
        self.source_column_name = input_column
        self.target_column_name = output_column
        self.system_prompt = system_prompt

    # style note: most important class (in this case 'transform' should be at the top, below constructor)
    def transform(self, data: PipelineIntermediate):
        full_texts = data.data[self.source_column_name].to_list()
        summarized_texts = []

        for text in tqdm(full_texts):
            summarized_texts.append(self.llm.generate(self.system_prompt + text))

        data.data[self.target_column_name] = summarized_texts

        data.history[str(len(data.history) + 1)] = data.data.copy(deep=True)

        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": SummarizerStep.get_name(),
            "parameters": {
                'model': {
                    'title': 'Summarizer model',
                    'description': 'LLM model instance to use for summarization. Can be any T5 transformer model.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['google/flan-t5-base'],
                    'default': 'google/flan-t5-base',
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
                    'title': 'Output column name',
                    'description': 'The summarized text gets saved to this column..',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['summary'],
                    'default': 'summary',
                },
                'system_prompt': {
                    'title': 'Summarizing instruction',
                    'description': 'This instruction is given to the LLM to summarize the text.',
                    'type': 'string',
                    'enforce-limit': False,
                    'default': 'Summarize: ',
                },

            }
        }

    @staticmethod
    def get_name() -> str:
        return "LLM Summarizer"
