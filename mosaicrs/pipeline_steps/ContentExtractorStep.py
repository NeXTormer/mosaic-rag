from typing import Optional

from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
import hashlib

from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep


class ContentExtractorStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)


    def transform_row(self, data, handler) -> (any, Optional[str]):
        if data is None:
            return ''

        # credits to chatgpt
        lines = str(data).split("\n")

        filtered_lines = [line for line in lines if len(line.split()) > 5]

        nav_keywords = ["home", "contact", "menu", "privacy", "terms", "about"]
        filtered_lines = [line for line in filtered_lines if not any(nav in line.lower() for nav in nav_keywords)]

        cleaned_text = "\n".join(filtered_lines)

        return cleaned_text, 'text'


    @staticmethod
    def get_info() -> dict:
        return {
            "name": ContentExtractorStep.get_name(),
            "category": "Semantic Filtering",
            "description": "Extract the content from the text.",
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
                    'supported-values': ['filtered-text', 'full-text'],
                    'default': 'filtered-text',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "Content Extractor"

    def get_cache_fingerprint(self) -> str:
        return 'rule-based'
