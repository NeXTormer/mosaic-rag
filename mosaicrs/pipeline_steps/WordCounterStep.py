from typing import Optional
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep


class WordCounterStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        """
            Calculates the number of words in each document for a specified `input_column` in the PipelineIntermediate and stores ot in the respective `output_column`.

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the individual word counts should be stored in the PipelineIntermediate.
        """

        super().__init__(input_column, output_column)


    def transform_row(self, data, handler) -> (str, Optional[str]):
        """
            The 'transform_row()' method is the core function of each pipeline step how implements the 'RowProcessorPipelineStep' parent class. It applies the specific modifications to one data entry of the 'PipelineIntermediate' object and returns the modified version or new information.
            
            data: str -> The string values from a single row in the selected input_column of the PipelineIntermediate to be processed in this step. \n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns two things: First the modified input string/new information which should be saved in the output_column, and second a string indicating, if the output_column is a 'chip', 'rank', or 'text' column. In this case the output_column is a 'chip' column.
        """

        return str(len(str(data).split(' '))), 'chip'

 
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
    
    def get_cache_fingerprint(self) -> str:
        return ''
