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


class DocumentSummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = 'DeepSeekv3',
                 summarize_prompt: str = "summarize: "):

        # todo: find better way of using deepseek model
        if model == 'DeepSeekv3':
            self.llm = DeepSeekLLMInterface(system_prompt='You are a helpful assistant')
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

        total_steps = len(full_texts)
        current_step = 0

        progress_info['step_progress'] = '{}/{}'.format(current_step, total_steps)
        progress_info['step_percentage'] = current_step / total_steps


        for text in tqdm(full_texts):
            summary = self.llm.generate(self.summarize_prompt + text)
            summarized_texts.append(summary)

            current_step += 1
            progress_info['step_progress'] = '{}/{}'.format(current_step, total_steps)
            progress_info['step_percentage'] = current_step / total_steps

        data.documents[self.target_column_name] = summarized_texts

        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)

        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": DocumentSummarizerStep.get_name(),
            "parameters": {
                'model': {
                    'title': 'Summarizer model',
                    'description': 'LLM model instance to use for summarization. Can be any T5 transformer model.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['DeepSeekv3', 'google/flan-t5-base'],
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
                    'title': 'Output column name',
                    'description': 'The summarized text gets saved to this column..',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['summary'],
                    'default': 'summary',
                },
                'summarize_prompt': {
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
