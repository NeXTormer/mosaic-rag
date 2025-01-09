import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer
from mosaicrs.llm.T5Transformer import T5Transformer
from tqdm import tqdm
from mosaicrs.llm.LLMInterface import LLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum

class SupportedSummarizerModels(Enum):
    Flan_T5_Base = "google/flan-t5-base",
    T5_Base = "google-t5/t5-base"

class SummarizerStep(PipelineStep):

    def __init__(self, source_column: str, destination_column: str, model: SupportedSummarizerModels = SupportedSummarizerModels.Flan_T5_Base, system_prompt: str = "summarize:"):
        if model == SupportedSummarizerModels.Flan_T5_Base or model == SupportedSummarizerModels.T5_Base:
            self.llm = T5Transformer(model.value)
        self.source_column_name = source_column
        self.target_column_name = destination_column
        self.system_prompt = system_prompt

    # style note: most important class (in this case 'transform' should be at the top, below constructor)
    def transform(self, data: PipelineIntermediate):
        full_texts = data.data[self.source_column_name].to_list()
        summarized_texts = []

        for text in tqdm(full_texts):
            summarized_texts.append(self.llm.generate(self.system_prompt + text))

        data.data[self.target_column_name] = summarized_texts

        data.history[str(len(data.history)+1)] = data.data.copy(deep=True)

        return data


    def get_info(self) -> dict:
        return {
            'model' : 'LLM model instance to use for summarization.',
            'source_column' : 'Column name in PipelineIntermediate.data that should be summarized.',
            'destination_column' : 'Column name in PipelineIntermediate.data where the summary should be saved.',
            'system_prompt' : 'System prompt for summarization. Default="Summarize in 40 words:" ',
        }

    def get_name(self) -> str:
        return "LLM Summarizer"

    
        







