from typing import Optional
import nltk
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from tqdm import tqdm
import hashlib
from mosaicrs.pipeline_steps.utils import process_data_punctuation_removal

class PunctuationRemovalStep(PipelineStep):
    def __init__(self, input_column: str, output_column: str, process_query: str):
        nltk.download('punkt_tab')
        self.input_column = input_column
        self.output_column = output_column
        self.process_query = True if process_query == "Yes" else False


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        if self.input_column not in data.documents:
            handler.log(f"PunctuationRemoval - InputColumn: {self.input_column} not in the PipelineIntermediate DataFrame.")
            return data

        inputs = [entry if entry is not None else "" for entry in data.documents[self.input_column].to_list()]
        outputs = []

        if self.process_query:
            handler.update_progress(0, len(inputs) + 1)
        else:
            handler.update_progress(0, len(inputs))

        for input in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1((self.get_cache_fingerprint() + str(input)).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None:
                output = process_data_punctuation_removal(input)
                handler.put_cache(input_hash, output)

            outputs.append(output)
            handler.increment_progress()

        if self.process_query:
            data.query = self.process_data_punctuation_removal(data.query)
            handler.increment_progress()

        data.documents[self.output_column] = outputs
        data.set_text_column(self.output_column)
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)

        return data
        

    @staticmethod
    def get_info() -> dict:
        return {
            "name": PunctuationRemovalStep.get_name(),
            "category": "Pre-Processing",
            "description": "Remove punctuation from this column text",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text','summary','cleaned-text'],
                    'default': 'cleaned-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['cleaned-text', 'full-text'],
                    'default': 'cleaned-text',
                },
                'process_query': {
                    'title': 'Query Pre-processing',
                    'description': 'Should the query be also pre-processed?',
                    'type': 'dropdown',
                    'enforce-limit': True,
                    'supported-values': ['Yes', 'No'],
                    'default': 'Yes',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "Punctuation Remover"

    def get_cache_fingerprint(self) -> str:
        return 'rule-based'
