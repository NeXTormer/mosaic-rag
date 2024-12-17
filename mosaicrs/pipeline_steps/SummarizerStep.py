import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer
from tqdm import tqdm

from mosaicrs.llm.LLMInterface import LLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep


#TODO: Überlegen wo wir die SystemPrompts hinzufügen. Ob sie Task-Spezifisch sind oder LLM-Spezifisch. Kann eine LLM für mehrere tasks verwendet werden wenn sie nicht auf einen Task trainiert/instanziert wird.

class SummarizerStep(PipelineStep):

    def __init__(self, llm: LLMInterface, summary_length: int = 40):
        self.llm = llm
        self.summary_length = summary_length

    # Note: please don't add extra parameters, this needs to be the same signature everywhere. Add parameters in constructor
    def transform(self, data: PipelineIntermediate):
        # todo: find a better way to get the data from the intermediate format
        # todo: maybe rename data parameter
        data.history.append(data.data.copy(deep=True))

        full_texts = data.data['full_text'].to_list()
        summarized_texts = []

        for text in tqdm(full_texts):
            summarized_texts.append(self.llm.generate('Summarize in ' + str(self.summary_length) + ' words:' + text))

        data.data['summary'] = summarized_texts

        return data


    def get_info(self) -> dict:
        return {
            'llm': 'LLM instance to use',
            'summary_length': 'Length of summary text in words',
        }
        







