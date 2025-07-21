from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep
from typing import Optional
import resiliparse.extract.html2text


class ContentExtractorStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)


    def transform_row(self, data, handler) -> (any, Optional[str]):
        if data is None:
            return ''

        return resiliparse.extract.html2text.extract_plain_text(data,preserve_formatting=False, main_content=True, alt_texts=True, noscript=False, comments=False,links=False), "text" 

    

    @staticmethod
    def get_info() -> dict:
        return {
            "name": ContentExtractorStep.get_name(),
            "category": "Pre-Processing",
            "description": "Extract the content from the text using the Resiliparse python library, which implements a rule-based main content extraction, which removes elements such as navigation blocks, sidebars, footers, ads and as far as possible aslo invisible elements.",
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
