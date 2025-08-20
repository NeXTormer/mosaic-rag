import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler

class WordCounterStep2(PipelineStep):
    def __init__(self, input_column: str, output_column: str):
        """
            Calculates the number of words in each document for a specified `input_column` in the PipelineIntermediate and stores ot in the respective `output_column`.

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the individual word counts should be stored in the PipelineIntermediate.
        """
         
        self.input_column = input_column
        self.output_column = output_column


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. 
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """

        if self.input_column not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.input_column)

        
        input_texts = data.documents[self.input_column]
        text_word_counts = [len(text) for text in input_texts]

        data.documents[self.output_column] = text_word_counts
        data.set_chip_column(self.output_column)
        
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data


    @staticmethod
    def get_info() -> dict:
        return {
            "name": WordCounterStep2.get_name(),
            "category": "Metadata Analysis",
            "description": "Count the number words, separated by spaces, in the text. DISCLAIMER: This step is soley implemented for tutorial purposes. If needed please use the default WordCounterStep.",
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
        return 'Word counter - via PipelineStep'