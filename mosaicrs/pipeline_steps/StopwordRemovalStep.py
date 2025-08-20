import hashlib
import copy
import mosaicrs.pipeline_steps.utils as utils
import mosaicrs.pipeline.PipelineErrorHandling as err

from nltk.tokenize import word_tokenize
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from nltk.corpus import stopwords
from tqdm import tqdm

class StopWordRemovalStep(PipelineStep):

    def __init__(self, input_column:str, output_column:str, language_column:str = "language"):
        """
            Text-based pre-processing step: Removing Stopwords. Supported languages: English, German, French, Italian

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the cleaned results of this pipeline step should be stored in the PipelineIntermediate.\n
            language_column: str -> The column containing the language ISO 639 Set3 language code. Is needed for stemming and stopword removable. Default: 'language'
        """

        self.input_column = input_column
        self.output_column = output_column
        self.language_column = language_column

        self.supported_stopword_sets = {}
        self.unsupported_languages = set()


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

        if self.language_column in data.documents:
            languages = data.documents[self.language_column].to_list()
            inputs = list(zip(inputs, languages))
        else:
            inputs = list(zip(inputs, ["" for _ in inputs]))

        pre_processed_outputs = []

        self.supported_stopword_sets = self.initialize_stopwords(data)

        handler.update_progress(0, len(inputs))

        for input, language in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1(('rule-based' + str(input)).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None:
                supported_language = utils.translate_language_code(language)
                if supported_language and supported_language in self.supported_stopword_sets:
                    output = self.process_data_stopword_removal(input, self.supported_stopword_sets[supported_language])                  
                else:
                    output = input
                    self.unsupported_languages.add(language)

                handler.put_cache(input_hash, output)

            pre_processed_outputs.append(output)
            handler.increment_progress()

        if self.unsupported_languages:
            handler.warning(err.PipelineStepWarning(err.WarningMessages.UnsupportedLanguage, languages = ", ".join(self.unsupported_languages)))

        data.documents[self.output_column] = pre_processed_outputs
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)
        data.set_text_column(self.output_column)
        
        return data


    @staticmethod
    def get_info() -> dict:
        return {
            "name": StopWordRemovalStep.get_name(),
            "category": "Pre-Processing",
            "description": "Text-based pre-processing step: Removing Stopwords. Supported languages: English, German, French, Italian",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'Column name of the PipelineIntermediate column used as the input for this step.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['full-text', 'summary','cleaned-text'],
                    'default': 'cleaned-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': 'The name of the column where the cleaned results of this pipeline step should be stored in the PipelineIntermediate. ',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['cleaned-text', 'full-text'],
                    'default': 'cleaned-text',
                },
                'language_column': {
                    'title': 'Language column name',
                    'description': 'The column containing the language ISO 639 Set3 language code. Is needed for stemming and stopword removable. Default: language',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': False,
                    'supported-values': ['language'],
                    'default': 'language',
                },
            }
        }


    @staticmethod
    def get_name() -> str:
        return "Stopword Remover"
    

    def initialize_stopwords(self, data: PipelineIntermediate):
        """
            Initializes a disctionary of all currently supported stopword lists which are needed by the given PipelineIntermediate.

            data: PipelineIntermediate -> Given the documents in the current state of the PipelineIntermediate, all needed languages which are currently supported are considered. 

            It returns a dictionary containing the stopword lists of all supported languages. As a key the language names are used and the values are then the respective sets of stopwords per language. 
        """
        
        requiried_languages = data.documents[self.language_column].value_counts().to_dict()
        supported_stopword_sets = {}
        for k, _ in requiried_languages.items():
            language_name = utils.translate_language_code(k)
            if language_name:
                supported_stopword_sets[language_name] = set(stopwords.words(language_name))

        return supported_stopword_sets
    

    def process_data_stopword_removal(self, input, selected_stopwords):
        """
            It tokenizes the words from the input parameter, trims leading and trailing whitespace, converts each word to lowercase, and removes any that appear in the selected_stopwords list. The remaining words are then joined with spaces to form and return a stopword-free string.

            input: str -> INput string, from which the stopwords should be removed.
            selected_stopwords: list(str) -> List of all stopwords against which teh string should be checked.

            It returns the given input string without any stopwords from the selected_stopwords list. 
        """
        
        withouth_stopwords = [word.strip() for word in word_tokenize(input) if word.lower() not in selected_stopwords]
        return " ".join(withouth_stopwords)  
