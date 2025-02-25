import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer
from mosaicrs.llm.DeepSeekLLMInterface import DeepSeekLLMInterface
from mosaicrs.llm.T5Transformer import T5Transformer
from tqdm import tqdm
from mosaicrs.llm.LLMInterface import LLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum
import hashlib

class DocumentSummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = 'DeepSeekv3',
                 summarize_prompt: str = "summarize: "):

        # todo: find better way of using deepseek model, but leave it like that now
        # just use deepseekv3 for all general purpose llm tasks
        self.model_name = model
        if model == 'DeepSeekv3':
            self.llm = DeepSeekLLMInterface(system_prompt='You are a helpful assistant')
        else:
            self.llm = T5Transformer(model)

        self.source_column_name = input_column
        self.target_column_name = output_column
        self.summarize_prompt = summarize_prompt


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        summarized_texts = []

        handler.log("Summarizing using model: {}".format(self.llm))


        handler.update_progress(0, len(full_texts))

        for text in tqdm(full_texts):
            if handler.should_cancel:
                break

            text_hash = hashlib.sha1((text + self.model_name + self.summarize_prompt).encode()).hexdigest()
            summary = handler.get_cache(text_hash)

            if summary is None:
                summary = self.llm.generate(self.summarize_prompt + text)
                handler.put_cache(text_hash, summary)

            summarized_texts.append(summary)
            handler.increment_progress()

        data.documents[self.target_column_name] = summarized_texts
        data.set_text_column(self.target_column_name)
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)

        return data


    @staticmethod
    def get_info() -> dict:
        return {
            "name": DocumentSummarizerStep.get_name(),
            "category": "Summarizers",
            "description": "Summarize each document in the result set using a LLM. Specify the input and output column names.",
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
