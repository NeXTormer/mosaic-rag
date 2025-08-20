import nltk
import hashlib
import unicodedata
import contractions
import string
import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from tqdm import tqdm
from typing import Optional
from nltk.tokenize import word_tokenize


class PunctuationRemovalStep(PipelineStep):
    def __init__(self, input_column: str, output_column: str, process_query: str = "Yes"):
        """
            Text-based pre-processing step: Removes punctuation from a given text column in the PiplineIntermediate using the string.punctuation char set. 

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the cleaned results of this pipeline step should be stored in the PipelineIntermediate.\n
            process_query: str -> A string containing either 'Yes' or 'No'. If the string is 'Yes' punctuation will be also removed from the query itself. For 'No' or all other strings the query remains untouched. The string parameter is needed for frontend reasons. Default: 'Yes'
        """
        
        nltk.download('punkt_tab')
        self.input_column = input_column
        self.output_column = output_column
        self.process_query = True if process_query == "Yes" else False


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. 
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """

        if self.input_column not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.input_column)


        inputs = [entry if entry is not None else "" for entry in data.documents[self.input_column].to_list()]
        outputs = []

        if self.process_query:
            handler.update_progress(0, len(inputs) + 1)
        else:
            handler.update_progress(0, len(inputs))

        for input in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1((self.get_cache_fingerprint() + str(input)).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None:
                output = self.process_data_punctuation_removal(input)
                handler.put_cache(input_hash, output)

            outputs.append(output)
            handler.increment_progress()

        if self.process_query:
            data.query = self.process_data_punctuation_removal(data.query)
            handler.increment_progress()

        data.documents[self.output_column] = outputs
        data.set_text_column(self.output_column)
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)

        return data
        

    @staticmethod
    def get_info() -> dict:
        return {
            "name": PunctuationRemovalStep.get_name(),
            "category": "Pre-Processing",
            "description": "Remove punctuation from this column text",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text','summary','cleaned-text'],
                    'default': 'cleaned-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['cleaned-text', 'full-text'],
                    'default': 'cleaned-text',
                },
                'process_query': {
                    'title': 'Query Pre-processing',
                    'description': 'Should the query be also pre-processed?',
                    'type': 'dropdown',
                    'enforce-limit': True,
                    'supported-values': ['Yes', 'No'],
                    'default': 'Yes',
                },
            }
        }


    @staticmethod
    def get_name() -> str:
        return "Punctuation Remover"


    def get_cache_fingerprint(self) -> str:
        return 'rule-based'
    

    def process_data_punctuation_removal(self, data):
        """
            Normalizes the given text given by the 'data' parameter and then removes punctuations from this normalized text. 

            data: str -> Raw string input, which should be normalized and cleaned form punctuation.

            It returns the normalized and punctuation-free string.
        """

        if data is None:
            return ''

        expanded_data = contractions.fix(data)
        normalized_data = unicodedata.normalize("NFKD", expanded_data)
        normalized_data = "".join(c for c in normalized_data if unicodedata.category(c) != 'Mn')
        tokenized_words = word_tokenize(normalized_data) 
        tokenized_words = [word.translate(str.maketrans('','',string.punctuation)) for word in tokenized_words]

        cleaned_text = " ".join([word.strip() for word in tokenized_words if word != ''])
        return cleaned_text 
