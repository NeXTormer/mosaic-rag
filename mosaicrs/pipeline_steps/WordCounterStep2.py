from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler


class WordCounterStep2(PipelineStep):
    def __init__(self, input_column: str, output_column: str):
        self.input_column = input_column
        self.output_column = output_column

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        if self.input_column not in data.documents:
            handler.log("The selected input column does not exist in the PipelineIntermediate.")
            return data
        
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