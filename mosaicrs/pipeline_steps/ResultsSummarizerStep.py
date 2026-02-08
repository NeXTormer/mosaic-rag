import json
import os

import pandas as pd
import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep

class ResultsSummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = json.loads(os.environ.get('LITELLM_MODELS'))[0]):
        """
            Pipeline step: Summarizes all documents in the result set into a single unified summary. This step is query-aware: it takes the query from the PipelineIntermediate, concatenates all documents separated by <SEP>, and instructs the LLM to generate a coherent summary that directly answers the query. The output is stored as metadata in the pipeline state. 

            input_column: str -> Column name of the PipelineIntermediate column containing the full text to be summarized. \n
            output_column: str -> Name of the column under which the summary will be stored as metadata. \n
            model: str -> The LLM model used for summarization. Default: 'DeepSeekv3'. Supported: 'DeepSeekv3', 'gemma2', 'qwen2.5', 'llama3.1'. \n
            summarize_prompt: str -> Instruction prefix that guides the summarization process. Default: "summarize: ".
        """


        self.llm = LiteLLMLLMInterface()

        self.system_prompt = '''
        You are a search engine assistant. You will receive a Query and several Documents separated by <SEP>.

        CONSTRAINTS:
        1. OBJECTIVE: Synthesize the documents into a single, cohesive answer to the user query.
        2. LANGUAGE: The summary MUST be in the same language as the provided documents.
        3. NO HALLUCINATION: Use strictly the provided information. If the documents don't contain the answer, state that.
        4. FORMATTING: Maximum 5 sentences. No lists or bullet points. Use **Markdown bolding** for key facts.
        5. FLOW: Avoid citing documents by name (e.g., "Doc 1 says..."); create a natural, fluid summary.
        
        OUTPUT:
        A single, high-density paragraph.
        
        INPUT:
        '''

        self.model_name = model
        self.source_column_name = input_column
        self.target_column_name = output_column


    
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
        summary = self.llm.generate(self.system_prompt + "\nQuery: " + data.query + "<SEP>" + "<SEP>".join(full_texts), self.model_name)
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
                    'description': 'The LLM instance used for summarization.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': json.loads(os.environ.get('LITELLM_MODELS')),
                    'default': json.loads(os.environ.get('LITELLM_MODELS'))[0],
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
