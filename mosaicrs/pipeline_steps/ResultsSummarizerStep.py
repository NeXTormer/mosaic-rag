import pandas as pd
import mosaicrs.pipeline.PipelineErrorHandling as err

from transformers import T5ForConditionalGeneration, T5Tokenizer
from mosaicrs.llm.DeepSeekLLMInterface import DeepSeekLLMInterface
from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
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
        """
            Pipeline step: Summarizes all documents in the result set into a single unified summary. This step is query-aware: it takes the query from the PipelineIntermediate, concatenates all documents separated by <SEP>, and instructs the LLM to generate a coherent summary that directly answers the query. The output is stored as metadata in the pipeline state. 

            input_column: str -> Column name of the PipelineIntermediate column containing the full text to be summarized. \n
            output_column: str -> Name of the column under which the summary will be stored as metadata. \n
            model: str -> The LLM model used for summarization. Default: 'DeepSeekv3'. Supported: 'DeepSeekv3', 'gemma2', 'qwen2.5', 'llama3.1'. \n
            summarize_prompt: str -> Instruction prefix that guides the summarization process. Default: "summarize: ".
        """

        if model == 'DeepSeekv3':
            self.llm = DeepSeekLLMInterface(system_prompt='You are a helpful assistant part of a search engine. You are given a query and documents separated by <SEP>. Please summarize the documents in order to answer the query. Do not use any additional information not available in the given documents. The summary should be a maximum of five sentences without any listings. Mark important passages as bold.')
        else:
            self.llm = LiteLLMLLMInterface(model=model, system_prompt='You are a helpful assistant part of a search engine. You are given a query and documents separated by <SEP>. Please summarize the documents in order to answer the query. Do not use any additional information not available in the given documents. The summary should be a maximum of five sentences without any listings. Mark important passages as bold.')

        self.source_column_name = input_column
        self.target_column_name = output_column
        self.summarize_prompt = summarize_prompt

    
    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. The 'transform()' method performs the summarization task by combining the query and all retrieved documents, then generating a unified summary using the selected LLM.
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """

        if self.source_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.source_column_name)
        
        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]

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
                    'description': 'The LLM instance used for summarization. the following models are currently supported: DeepSeekv3,gemma2, qwen2.5, llama3.1.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['DeepSeekv3', 'gemma2', 'qwen2.5', 'llama3.1'],
                    'default': 'gemma2',
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
