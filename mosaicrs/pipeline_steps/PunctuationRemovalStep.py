from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep
import string
from nltk.tokenize import word_tokenize

class PunctuationRemovalStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)


    def transform_row(self, data: str) -> str:
        if data is None:
            return ''

        #Tokenize words
        tokenized_words = word_tokenize(data) 
        #Remove punctuation
        tokenized_words = [word.translate(str.maketrans('','',string.punctuation)) for word in tokenized_words]

        cleaned_text = " ".join([word.strip() for word in tokenized_words if word != ''])
        return cleaned_text

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
            }
        }

    @staticmethod
    def get_name() -> str:
        return "Punctuation Remover"

    def get_cache_fingerprint(self) -> str:
        return 'rule-based'
