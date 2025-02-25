from typing import Optional
import numpy as np
from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
import hashlib
from mosaicrs.pipeline_steps.utils import get_blacklist_for_filtering
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep


class ContentExtractorStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)


    def transform_row(self, data, handler) -> (any, Optional[str]):
        if data is None:
            return ''
        
        single_lines = [line.strip() for line in str(data).split("\n")]
        blacklist_words = get_blacklist_for_filtering()
        single_lines = [line for line in single_lines if not any(blw.lower() in line.lower() for blw in blacklist_words)]


        avg_words_line_ngram = self.moving_avg_word_count(single_lines)
        overall_average_word_count = sum([len(sentence.split(" ")) for sentence in single_lines]) / len(single_lines)
        cleaned_lines = []

        for line, avg in zip(single_lines, avg_words_line_ngram):
            if avg >= overall_average_word_count*1.5:
                cleaned_lines.append(line)

        handler.log("\n".join(cleaned_lines))


        if len(cleaned_lines) == 0:
            #TODO: Potential Warning
            return data, "text"
        else:
            return "\n".join(cleaned_lines), "text"

    
    def moving_avg_word_count(self, lines, window_size=5):
        word_counts = [len(line.split(" ")) for line in lines]
        avg_counts = []

        for i in range(len(lines)):
            start = max(0, i - window_size)
            end = min(len(lines), i + window_size + 1)
            avg_count = sum(word_counts[start:end]) / (end - start)
            avg_counts.append(avg_count)

        return avg_counts

    @staticmethod
    def get_info() -> dict:
        return {
            "name": ContentExtractorStep.get_name(),
            "category": "Pre-Processing",
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
