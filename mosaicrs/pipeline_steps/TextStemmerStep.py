import nltk
import hashlib
import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from nltk.stem import SnowballStemmer
from tqdm import tqdm
from mosaicrs.pipeline_steps.utils import translate_language_code
from nltk.tokenize import word_tokenize

class TextStemmerStep(PipelineStep):

    def __init__(self, input_column:str, output_column:str, language_column:str = "language"):
        """
            Text-based pre-processing step: Applies stemming to a text column using the `SnowballStemmer` from NLTK. Supported languages: English, German, French, Italian

            input_column: str -> Column name of the PipelineIntermediate column used as the input for this step.\n
            output_column: str -> The name of the column where the cleaned results of this pipeline step should be stored in the PipelineIntermediate.\n
            language_column: str -> The column containing the language ISO 639 Set3 language code. Is needed for stemming and stopword removable. Default: 'language'
        """

        self.input_column = input_column
        self.output_column = output_column
        self.language_column = language_column

        self.supported_stemmers = {} 
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

        self.supported_stemmers = self.initialize_stemmers(data)

        pre_processed_outputs = []

        handler.update_progress(0, len(inputs))

        for input, language in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1(('rule-based' + str(input)).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None:
                supported_language = translate_language_code(language)
                if supported_language and supported_language in self.supported_stemmers:
                    output = self.process_data_stemming(input, self.supported_stemmers[supported_language])
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
            "name": TextStemmerStep.get_name(),
            "category": "Pre-Processing",
            "description": "Text-based pre-processing step: Stemming of given column. Supported languages: English, German, French, Italian",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'The pre-processing steps will be performed on this column.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['full-text', 'summary', 'cleaned-text'],
                    'default': 'cleaned-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': 'The pre-processed text will be put into this column.',
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
        return "Text Stemmer"
    

    def initialize_stemmers(self, data: PipelineIntermediate):
        """
            This method initializes a instance of the NLTK 'SnowballStemmer' for every supported language, which is present and needed in the current data version of the PipelineIntermediate.

            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.

            It returns a dictionary with all supported stemmers. The specific language_name (not code) is the key and the stemmer object is the value for each dictionary item.
        """

        requiried_languages = data.documents[self.language_column].value_counts().to_dict()
        supported_stemmers = {}
        for k, _ in requiried_languages.items():
            language_name = translate_language_code(k)
            if language_name:
                supported_stemmers[language_name] = SnowballStemmer(language_name)

        return supported_stemmers
    

    def process_data_stemming(self, input, stemmer):
        """
            It tokenizes all words from the input parameter and then uses the given stemmer to get its word stem and return the stemmed input string. 

            input: str -> Input string which should be stemmed.
            stemmer: SnowballStemmer -> Specific stemmer for the language of the input text. 

            Returns the stemmed version of the input string. 
        """

        stemmed_words = [stemmer.stem(word).strip() for word in word_tokenize(input)]
        return " ".join(stemmed_words)