from typing import Optional

from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep
from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface

class TranslateStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str, target_language: str = "English"):
        """
        A pipeline step that translates text documents using a local Ollama instance with the "translategemma" model.
        """
        super().__init__(input_column, output_column)
        self.target_language = target_language
        self.model_name = "translategemma"
        self.llm = LiteLLMLLMInterface()
        self.prompt = f"Translate the following text into {self.target_language}:\n\n"

    def transform_row(self, data: str, handler: PipelineStepHandler) -> tuple[str, Optional[str]]:
        if not data:
            return "", "text"

        translated_text = self.llm.generate(self.prompt + data, self.model_name)
        return translated_text, "text"

    def get_cache_fingerprint(self) -> str:
        return self.target_language + self.model_name + self.prompt

    @staticmethod
    def get_info() -> dict:
        return {
            "name": TranslateStep.get_name(),
            "category": "Pre-Processing",
            "description": "Translate documents using a local Ollama instance with the translategemma model.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'The column containing text to translate.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': 'The column where translated text gets saved.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['translated_text'],
                    'default': 'translated_text',
                },
                'target_language': {
                    'title': 'Target language',
                    'description': 'The language to translate the text into.',
                    'type': 'text',
                    'enforce-limit': False,
                    'supported-values': [],
                    'default': 'English',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return 'Document Translator'
