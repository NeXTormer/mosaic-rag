import numpy as np
import hashlib

from typing import Optional
from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep


class BasicContentExtractorStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        """
            Extracts the main content from full-text documents, removing non-essential elements like navigation menus or filler content. Uses a moving average based on sentence length. This step will eventually be deprecated once cleaner indexes are available. It used the text data from the `input_column` and saves the cleaned text data in the `output_column` of the PipelineIntermediate.

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the cleaned input strings should be stored in the PipelineIntermediate.
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
        
        single_lines = [line.strip() for line in str(data).split("\n")]
        blacklist_words = self.get_blacklist_for_filtering()
        single_lines = [line for line in single_lines if not any(blw.lower() in line.lower() for blw in blacklist_words)]

        avg_words_line_ngram = self.moving_avg_word_count(single_lines)
        overall_average_word_count = sum([len(sentence.split(" ")) for sentence in single_lines]) / len(single_lines)
        cleaned_lines = []

        for line, avg in zip(single_lines, avg_words_line_ngram):
            if avg >= overall_average_word_count*1.5:
                cleaned_lines.append(line)

        if len(cleaned_lines) == 0:
            return data, "text"
        else:
            return "\n".join(cleaned_lines), "text"

    
    @staticmethod
    def get_info() -> dict:
        return {
            "name": BasicContentExtractorStep.get_name(),
            "category": "Pre-Processing",
            "description": "Extract the content from the text passed on simple heuristics and a moving average word length threshold.",
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
        return "Basic Content Extractor"


    def get_cache_fingerprint(self) -> str:
        return 'rule-based'


    def moving_avg_word_count(self, lines, window_size=5):
        """
            It computes a moving average of the word counts per line, where each line’s average is based on itself and its neighboring lines within the given window size.

            lines: list(str) -> The base list of all string on which we should compute the moving average of word counts.
            window_size: int -> The window size for the moving average calculation: Default: 5
        """
        
        word_counts = [len(line.split(" ")) for line in lines]
        avg_counts = []

        for i in range(len(lines)):
            start = max(0, i - window_size)
            end = min(len(lines), i + window_size + 1)
            avg_count = sum(word_counts[start:end]) / (end - start)
            avg_counts.append(avg_count)

        return avg_counts
    
    
    def get_blacklist_for_filtering(self):
        """
            Returns a list of string containing blacklist words, which should be filtered out by the content extractor step. They indicate menu items or other non-informative parts of a web page.
        """
        
        return [
        "Home", "About", "Services", "Products", "Features", "Pricing", "Contact", "Blog",
        "FAQ", "Help", "Support", "Careers", "Testimonials", "Portfolio", "Gallery",
        "Login", "Register", "Sign Up", "Profile", "Dashboard", "Settings", "Logout",
        "News", "Events", "Shop", "Store", "Resources", "Community", "Forum",
        "Documentation", "Tutorials", "Guides", "Case Studies", "Partners", "Team",
        "Press", "Investors", "API", "Developers", "Downloads", "Legal",
        "Privacy Policy", "Terms of Service", "Sitemap", "Search", "Subscribe"
        ]

