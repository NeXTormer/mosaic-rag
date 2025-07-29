from typing import Optional
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep


class WordCounterStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)

    def transform_row(self, data, handler) -> (str, Optional[str]):
        return str(len(str(data).split(' '))), 'chip'

    def get_cache_fingerprint(self) -> str:
        return ''

    @staticmethod
    def get_info() -> dict:
        return {
            "name": WordCounterStep.get_name(),
            "category": "Metadata Analysis",
            "description": "Count the number words, separated by spaces, in the text.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['wordCount', 'word_count'],
                    'default': 'wordCount',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return 'Word counter'