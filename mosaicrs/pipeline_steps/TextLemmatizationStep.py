from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
import nltk
import spacy
from tqdm import tqdm
import hashlib
from mosaicrs.pipeline_steps.utils import translate_language_code, get_lemmatization_code


class TextLemmatizerStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str, language_column: str = "language"):
        self.input_column = input_column
        self.output_column = output_column
        self.language_column = language_column
        self.retrieved_lemmatizers = {}
        self.unsupported_languages = set()

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        if self.input_column not in data.documents:
            handler.log(f"TextLemmatizer - InputColumn: {self.input_column} not found in PipelineIntermediate DataFrame.")
            return data
        
        inputs = [entry if entry is not None else "" for entry in data.documents[self.input_column].to_list()]
        languages = data.documents[self.language_column].to_list() if self.language_column in data.documents else ["" for _ in inputs]
        inputs = list(zip(inputs, languages))

        pre_processed_outputs = []

        self.retrieved_lemmatizers = self._initialize_lemmatizers(data, handler)

        handler.update_progress(0, len(inputs))

        for text, language in tqdm(inputs):
            if handler.should_cancel:
                break

            input_hash = hashlib.sha1(('lemmatization' + text).encode()).hexdigest()
            output = handler.get_cache(input_hash)

            if output is None and language:
                supported_language = translate_language_code(language)
                if supported_language and supported_language in self.retrieved_lemmatizers:
                    lemmatizer = self.retrieved_lemmatizers.get(supported_language)

                    if supported_language == "english" and lemmatizer:
                        tokens = word_tokenize(text)
                        pos_tags = pos_tag(tokens)
                        lemmatized_words = [lemmatizer.lemmatize(word, self._get_wordnet_pos(tag)) for word, tag in pos_tags]
                        output = " ".join(lemmatized_words)
                    elif lemmatizer:
                        doc = lemmatizer(text)
                        output = " ".join([token.lemma_ for token in doc])
                    
                    else:
                        output = text
                        handler.log(f"Error: Lemmatization cannot be done for language {language}")
                else:
                    output = text
                    self.unsupported_languages.add(language)

                handler.put_cache(input_hash, output)

            pre_processed_outputs.append(output)
            handler.increment_progress()

        if self.unsupported_languages:
            unsupported_languages_string = ", ".join(self.unsupported_languages)
            handler.log(f"Languages: {unsupported_languages_string} are not supported for lemmatization.")

        data.documents[self.output_column] = pre_processed_outputs
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)
        data.set_text_column(self.output_column)

        return data
    

    def _initialize_lemmatizers(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        requiried_languages = data.documents[self.language_column].value_counts().to_dict()
        supported_lemmatizers = {}
        for k, _ in requiried_languages.items():
            language_name = translate_language_code(k)
            if language_name == "english":
                supported_lemmatizers[language_name] = WordNetLemmatizer()
            elif language_name:
                lemmatization_model = get_lemmatization_code(language_name)
                if lemmatization_model:
                    try:
                        supported_lemmatizers[language_name] = spacy.load(lemmatization_model)
                    except Exception as e:
                        handler.log(f"Warning: Could not load spaCy model {lemmatization_model}. Ensure it is installed using `python -m spacy download {lemmatization_model}`")
                
        return supported_lemmatizers


    def _get_wordnet_pos(self, treebank_tag: str):
        """Converts POS tag to WordNet format for better lemmatization."""
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN  # Default to noun

    @staticmethod
    def get_info() -> dict:
        """Returns metadata about the pipeline step."""
        return {
            "name": TextLemmatizerStep.get_name(),
            "category": "Pre-Processing",
            "description": "Text-based pre-processing step: Lemmatization of given column.",
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
                    'description': 'The column containing the language ISO 639 Set3 language code. Default: language',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['language'],
                    'default': 'language',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        """Returns the step name."""
        return "Text Lemmatizer"
