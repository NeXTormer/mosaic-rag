import resiliparse.extract.html2text
import regex as re

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep
from typing import Optional


class ContentExtractorStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        """
            Extracts the main content from full-text documents, removing non-essential elements like navigation menus or filler content. It extracts these elements from the text using the Resiliparse python library, which implements a rule-based main content extraction, which removes elements such as navigation blocks, sidebars, footers, ads and as far as possible aslo invisible elements. It used the text data from the `input_column` and saves the cleaned text data in the `output_column` of the PipelineIntermediate.

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the cleaned input strings  should be stored in the PipelineIntermediate.
        """

        super().__init__(input_column, output_column)


    def transform_row(self, data, handler) -> (any, Optional[str]):
        """
            The 'transform_row()' method is the core function of each pipeline step how implements the 'RowProcessorPipelineStep' parent class. It applies the specific modifications to one data entry of the 'PipelineIntermediate' object and returns the modified version or new information.
            
            data: str -> The string values from a single row in the selected input_column of the PipelineIntermediate to be processed in this step. \n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns two things: First the modified input string/new information which should be saved in the output_column, and second a string indicating, if the output_column is a 'chip', 'rank', or 'text' column. In this case the output_column is a 'text' column.
        """

        if data is None:
            return "", "text"
        
        data_paragraphs = data.split("\n")
        cleaned_paragraphs = []

        for paragraph in data_paragraphs:
            cleaned_paragraph = resiliparse.extract.html2text.extract_plain_text(paragraph,preserve_formatting=False, main_content=True, alt_texts=False, noscript=False, comments=False,links=False)
            if paragraph.strip() == "" or cleaned_paragraph.strip() != "":
                cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_text = "\n".join(cleaned_paragraphs)

        return re.sub(r"\n(\n)+",r"\n\n",cleaned_text), "text" 


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
