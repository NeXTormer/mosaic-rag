import json
import os

import pandas as pd
import hashlib
import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
from tqdm import tqdm
from mosaicrs.llm.LLMInterface import LLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum

document_summarizer_prompt = """
You are a high-efficiency information extraction assistant for a RAG system.

CONSTRAINTS:
1. EMPTY INPUT: If the document is empty or unreadable, output ONLY the phrase: "Empty document."
2. LANGUAGE: You MUST write the summary in the same language as the original document.
3. BREVITY: Provide only 2 to 4 sentences.
4. FORMATTING: Use **Markdown bolding** for critical entities, dates, or technical terms.
5. STYLE: Start directly with facts; no filler phrases (e.g., "This text is about...").
6. ACCURACY: Use only the provided text.

Summarize this document:
""".strip()

class DocumentSummarizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str,
                 model: str = json.loads(os.environ.get('LITELLM_MODELS'))[0]):
        """
             A pipeline step that summarizes text documents using a Large Language Model (LLM). This step takes an input column containing text (e.g., "full-text"), generates  summaries for each entry using the specified LLM, and stores the results in  an output column (e.g., "summary"). Summarization results are cached to avoid  recomputation on repeated runs with the same inputs and configuration.
        
            input_column: str -> Name of the column containing source text to summarize.\n
            output_column: str -> Name of the column where summaries will be stored.\n
            model: str, optional -> LLM model to use. Defaults to 'DeepSeekv3'. Can also be 'gemma2', 'qwen2.5', 'llama3.1', etc.\n
            summarize_prompt (str, optional): Prompt instruction prepended to input text before summarization. Defaults to "summarize: ".
        """
        
        self.model_name = model
        self.llm = LiteLLMLLMInterface()

        self.source_column_name = input_column
        self.target_column_name = output_column
        self.summarize_prompt = document_summarizer_prompt


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. Apply the summarization step to the given pipeline data.
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """
        
        if self.source_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.source_column_name)
        
        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        summarized_texts = []

        handler.update_progress(0, len(full_texts))

        for text in tqdm(full_texts):
            if handler.should_cancel:
                break

            text_hash = hashlib.sha1((text + self.model_name + self.summarize_prompt).encode()).hexdigest()
            summary = handler.get_cache(text_hash)

            if summary is None:
                summary = self.llm.generate(self.summarize_prompt + text, self.model_name)
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
                    'description': 'LLM model that exists on the lite-llm instance to use for summarization.',
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
                    'supported-values': ['summary'],
                    'default': 'summary',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "LLM Summarizer"
