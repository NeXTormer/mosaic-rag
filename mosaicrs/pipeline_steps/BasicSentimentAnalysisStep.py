import torch
import mosaicrs.pipeline.PipelineErrorHandling as err

from typing import Optional
from transformers import pipeline
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep

class BasicSentimentAnalysisStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        """
            Uses the Hugging Face model `bhadresh-savani/distilbert-base-uncased-emotion` to return one of six emotions: sadness, joy, love, anger, fear, surprise. Works only on English texts and up to 512 tokens. It takes the text data from the `input_column` of the PipelineIntermediate and saves the sentiment in the `output_column`.

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the individual sentiment strings should be stored in the PipelineIntermediate.
        """
        
        super().__init__(input_column, output_column)
        self.model_name = 'bhadresh-savani/distilbert-base-uncased-emotion'
        self.model = pipeline("text-classification",model=self.model_name, top_k=None, device="cuda" if torch.cuda.is_available() else "cpu")
       

    def transform_row(self, data, handler: PipelineStepHandler):
        """
            The 'transform_row()' method is the core function of each pipeline step how implements the 'RowProcessorPipelineStep' parent class. It applies the specific modifications to one data entry of the 'PipelineIntermediate' object and returns the modified version or new information.
            
            data: str -> The string values from a single row in the selected input_column of the PipelineIntermediate to be processed in this step. \n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns two things: First the modified input string/new information which should be saved in the output_column, and second a string indicating, if the output_column is a 'chip', 'rank', or 'text' column. In this case the output_column is a 'text' column.
        """

        if data is None:
            return "", "chip"
        try:
            predictions = self.model(data)
            return max(predictions[0], key=lambda x: x["score"])["label"], "chip"
        except Exception as e:
            handler.warning(err.PipelineStepWarning(err.WarningMessages.SentimentPredictionNotPossible, model=self.model_name, exception_name=type(e).__name__, input=data))
            return "Not available", "chip"


    @staticmethod
    def get_info() -> dict:
        return {
            "name": BasicSentimentAnalysisStep.get_name(),
            "category": "Metadata Analysis",
            "description": "Make a sentiment analysis on a selected column and get the associated feeling.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'Column to use for sentiment analysis.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text', 'summary'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': 'The analysed sentiment gets saved to this column.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['sentiment'],
                    'default': 'sentiment',
                },
            }
        }


    @staticmethod
    def get_name() -> str:
        return "Basic Sentiment Analyser"
    

    def get_cache_fingerprint(self) -> str:
        return 'rule-based'

