from mosaicrs.endpoint.Endpoint import Endpoint
import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer
from tqdm import tqdm

from mosaicrs.llm.LLMInterface import LLMInterface

#TODO: Überlegen wo wir die SystemPrompts hinzufügen. Ob sie Task-Spezifisch sind oder LLM-Spezifisch. Kann eine LLM für mehrere tasks verwendet werden wenn sie nicht auf einen Task trainiert/instanziert wird. 

class SummarizerEndpoint(Endpoint):

    def __init__(self, llm: LLMInterface, summarization_system_prompt: str = "Summarize the following text and explain what is described in it:"):
        self.llm = llm
        self.summ_system_prompt = summarization_system_prompt


    #TODO: Überlegen ob die Daten immer im FOrmat sein müssen, dass die Spalte TextSnippet heißt oder ob man den Spaltennamen auch mitgibt

    #TODO: Datenbank abgreifen weil nicht die gesamten Texte in TextSnippet stehen

    def process(self, data, keep_format: bool = False):
        print("Begin summerizing data")
        summarized_texts = []
        original_texts = data["textSnippet"].to_list()
        for text in tqdm(original_texts):
            summarized_texts.append(self.llm.generate(self.summ_system_prompt + text))

        # for i in range(len(summarized_texts)):
        #     print(original_texts[i] + "\n" + summarized_texts[i] + "\n\n")

        print("Data has been summerized")
        if keep_format:
            data["textSnippet"] = summarized_texts
            return data

        return summarized_texts

        







