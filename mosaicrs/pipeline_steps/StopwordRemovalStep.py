from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from nltk.corpus import stopwords
import nltk
from tqdm import tqdm
import hashlib
from mosaicrs.pipeline_steps.utils import translate_language_code, process_data_stopword_removal

class StopWordRemovalStep(PipelineStep):

    def __init__(self, input_column:str, output_column:str, language_column:str = "language"):
        self.input_column = input_column
        self.output_column = output_column
        self.language_column = language_column

        self.supported_stopword_sets = {}
        self.unsupported_languages = set()

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        if self.input_column not in data.documents:
            handler.log(f"StopwordRemoval - InputColumn: {self.input_column} not in the PipelineIntermediate DataFrame.")
            return data
        
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
                supported_language = translate_language_code(language)
                if supported_language and supported_language in self.supported_stopword_sets:
                    output = process_data_stopword_removal(input, self.supported_stopword_sets[supported_language])                  
                else:
                    output = input
                    self.unsupported_languages.add(language)

                handler.put_cache(input_hash, output)

            pre_processed_outputs.append(output)
            handler.increment_progress()

        if self.unsupported_languages:
            unsupported_lanuages_string = ", ".join(self.unsupported_languages)
            handler.log(f"Languages: {unsupported_lanuages_string} are not supported for stopword removal.")

        data.documents[self.output_column] = pre_processed_outputs
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)
        data.set_text_column(self.output_column)

        handler.log("TEST1234")
        

        return data

    def initialize_stopwords(self, data):
        requiried_languages = data.documents[self.language_column].value_counts().to_dict()
        supported_stopword_sets = {}
        for k, _ in requiried_languages.items():
            language_name = translate_language_code(k)
            if language_name:
                supported_stopword_sets[language_name] = set(stopwords.words(language_name))

        return supported_stopword_sets


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