from mosaicrs.endpoint.Endpoint import Endpoint
import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer

from mosaicrs.llm.LLMInterface import LLMInterface


class SummarizerEndpoint(Endpoint):

    def __init__(self, llm: LLMInterface):
        self.llm = llm



    def process(self, data, query):
        text = data['textSnippet'].str.cat(sep='|')

        summary = self.llm.generate('summarize: ' + text)

        return summary





