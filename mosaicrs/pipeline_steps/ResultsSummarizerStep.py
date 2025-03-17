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

class ResultsSummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = 'DeepSeekv3',
                 summarize_prompt: str = "summarize: "):

        # todo: find better way of using deepseek model
        if model == 'DeepSeekv3':
            self.llm = DeepSeekLLMInterface(system_prompt='You are a helpful assistant part of a search engine. You are given a query and documents separated by <SEP>. Please summarize the documents in order to answer the query. Do not use any additional information not available in the given documents. The summary should be a maximum of five sentences without any listings. Mark important passages as bold.')
        else:
            self.llm = T5Transformer(model)

        self.source_column_name = input_column
        self.target_column_name = output_column
        self.summarize_prompt = summarize_prompt

    # style note: most important class (in this case 'transform' should be at the top, below constructor)
    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        summarized_texts = []

        handler.log("Summarizing using model: {}".format(self.llm))

        handler.update_progress(0, 1)
        summary = self.llm.generate("Query: " + data.query + "<SEP>" + "<SEP>".join(full_texts))
        handler.increment_progress()


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
            "category": "Summarizers",
            "description": "Summarize all documents in the result set into one search result.",
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
                    'title': 'Output column name',
                    'description': 'The summarized text gets saved to this column..',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['Summary'],
                    'default': 'Summary',
                },

            }
        }

    @staticmethod
    def get_name() -> str:
        return "Query Summarizer"
