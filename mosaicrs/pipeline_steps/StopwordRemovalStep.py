from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from tqdm import tqdm
import hashlib
from mosaicrs.pipeline_steps.utils import translate_language_code

class StopWordRemovalStep(PipelineStep):

    def __init__(self, input_column:str, output_column:str, language_column:str = "language"):
        self.input_column = input_column
        self.output_column = output_column
        self.language_column = language_column

        self.retrieved_stopwords = {}

        nltk.download("stopwords")
        nltk.download('punkt_tab')

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:

        inputs = [entry if entry is not None else "" for entry in data.documents[self.input_column].to_list()]
        if self.language_column in data.documents:
            languages = data.documents[self.language_column].to_list()
            inputs = list(zip(inputs, languages))
        else:
            inputs = list(zip(inputs, ["" for _ in inputs]))

        pre_processed_outputs = []

        handler.update_progress(0, len(inputs))

        for input, language in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1(('rule-based' + str(input)).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None and language is not "":
                supported_language = translate_language_code(language)
                if supported_language is not "":
                    if supported_language in self.retrieved_stopwords:
                        selected_stopwords = self.retrieved_stopwords[supported_language]
                    else:
                        selected_stopwords = set(stopwords.words(supported_language))
                        self.retrieved_stopwords[supported_language] = selected_stopwords

                    withouth_stopwords = [word.strip() for word in word_tokenize(input) if word not in selected_stopwords]
                    output = " ".join(withouth_stopwords)                    
                else:
                    output = input
                    #TODO: Warning Language not supported

                handler.put_cache(input_hash, output)

            pre_processed_outputs.append(output)
            handler.increment_progress()

        data.documents[self.output_column] = pre_processed_outputs
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)

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
                    'description': 'The pre-processing steps will be performed on this column.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['full-text', 'summary','cleaned-text'],
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
        return "Stopword Remover"