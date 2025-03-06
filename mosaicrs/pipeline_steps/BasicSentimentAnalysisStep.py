from typing import Optional
import torch
from transformers import pipeline

from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep

class BasicSentimentAnalysisStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)
        self.model = pipeline("text-classification",model='bhadresh-savani/distilbert-base-uncased-emotion', top_k=None, device="cuda" if torch.cuda.is_available() else "cpu")
        
    def transform_row(self, data, handler: PipelineStepHandler):
        if data is None:
            return ''
        try:
            predictions = self.model(data)
            return max(predictions[0], key=lambda x: x['score'])["label"], 'chip'
        except Exception as e:
            handler.log(f"Prediction error: {type(e).__name__}: {e}")
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

