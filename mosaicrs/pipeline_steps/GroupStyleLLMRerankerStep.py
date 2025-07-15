import pandas as pd
from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
import regex as re
import numpy as np
import itertools

class GroupStyleLLMRerankerStep(PipelineStep):

    def __init__(self, input_column: str, query: str = None,
                 model: str = 'gemma2', window_size: str = "2"):

        if model not in LiteLLMLLMInterface.supported_models:
            self.llm = None
            self.model = model
            return
        
        self.k = window_size.strip() if window_size.strip().isdigit() else "2"

        self.system_prompt = f"Your task is to determine which of {self.k} texts is more relevant to a given query.Please only answer with the most relevant text id in brackets ([ID]). If none of the texts is relevant to the query, answer [0]!"
        
        self.llm = LiteLLMLLMInterface(model=model, system_prompt=self.system_prompt)

        self.source_column_name = input_column
        self.model = model

        if query is not None:
            self.query = query
            self.use_new_query = True
        else:
            self.query = None
            self.use_new_query = False

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        if self.llm is None:
            handler.log(f"Model: {self.model} is not supported for the {GroupStyleLLMRerankerStep.get_name}.")
            return data
        
        handler.log("Reranking using Group Style LLM-Reranker")

        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        full_texts = list(zip(np.arange(1,len(full_texts)+1).tolist(), full_texts))

        full_text_combinations = list(itertools.combinations(full_texts, int(self.k)))

        point_counter = [0] * len(full_texts)

        handler.update_progress(0, len(full_text_combinations))

        for combi in full_text_combinations:
            relevant_combi_id = self.llm_group_comparison(combi=combi, query=self.query if self.use_new_query else data.query, handler=handler)
            if relevant_combi_id != 0:
                relevant_text_id = combi[relevant_combi_id-1][0] - 1
                point_counter[relevant_text_id] += 1
            else:
                handler.log("No relevant text in combi")

            handler.increment_progress()

        sorted_indices = sorted(range(len(point_counter)), key=lambda i: (-point_counter[i], i))
        ranks = [0] * len(point_counter)
        for rank, idx in enumerate(sorted_indices, start=1):
            ranks[idx] = rank

        reranking_id = str(data.get_next_reranking_step_number())
        reranking_rank_name = "_reranking_rank_" + reranking_id + "_"
        data.documents[reranking_rank_name] = ranks
        data.set_rank_column(reranking_rank_name)
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data

    def llm_group_comparison(self, combi, query:str, handler: PipelineStepHandler):
        timeout_max = 10
        prompt_listing = "[1]"
        prompt_texts = ""
        for i, item in enumerate(combi):
            prompt_texts += f"\n\n[{i+1}]: {item}"
            if i > 0:
                prompt_listing += f" or [{i+1}]"

        prompt=f"Here are {self.k} texts, each marked with a {prompt_listing} at the beginning. Which of the {self.k} following texts is more relevant to the Query:'{query}'. Ony answer with the most relevant text ID in brackets!{prompt_texts}"
        for _ in range(timeout_max):
            potential_answer = self.llm.generate(prompt=prompt)

            parseable_check = re.match(r"\[(\d+)\]", potential_answer)
            if parseable_check is not None:
                parsed_number = int(parseable_check.groups()[0])
                if 0 <= parsed_number and parsed_number <= int(self.k): 
                    return parsed_number 
                
            prompt_prolog = "Please only answer with the most relevant text id in brackets ([ID]). If none of the texts is relevant to the query, answer [0]!"
            prompt = prompt_prolog + prompt
                
        handler.log("Comparison run into timeout!")
        return 0

    @staticmethod
    def get_info() -> dict:
        return {
            "name": GroupStyleLLMRerankerStep.get_name(),
            "category": "Rerankers",
            "description": "Rerank documents based on individual comparisons of groups of documents. We take all possible combinations of k(window size) documents, compare them with each other and award the ones in each combination, which is most relevant to the query with a point. Afterwards the documents get ranked according to these points.",
            "parameters": {
                'model': {
                    'title': 'LLM model',
                    'description': 'LLM model instance to use for the reranking task.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['gemma2', 'qwen2.5', 'llama3.1'],
                    'default': 'gemma2',
                },
                'input_column': {
                    'title': 'Input column name',
                    'description': 'Column to use for the reranking.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                   'window_size': {
                    'title': 'Window Size',
                    'description': 'Size of the comparison window. ',
                    'type': 'string',
                    'default': '2',
                },
                'query': {
                    'title': 'Optional query',
                    'description': 'An additional query, different from the main query, used for reranking. Optional.',
                    'type': 'string',
                    'required': False,
                    'default': '',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "Group-Style Reranker Step"
