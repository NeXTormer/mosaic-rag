import pandas as pd
from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
import regex as re
import numpy as np

from mosaicrs.pipeline_steps.utils import get_most_current_ranking

class TournamentStyleLLMRerankerStep(PipelineStep):

    def __init__(self, input_column: str, query: str = None,
                 model: str = 'gemma2'):

        if model not in LiteLLMLLMInterface.supported_models:
            self.llm = None
            self.model = model
            return
        
        self.system_prompt = "Your task is to determine which of two texts is more relevant to a given query."
        
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
            handler.log(f"Model: {self.model} is not supported for the {TournamentStyleLLMRerankerStep.get_name}.")
            return data
        
        handler.log("Reranking using Tournament Style LLM-Reranker")

        current_ranking = get_most_current_ranking(data)
        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        full_texts = list(zip(np.arange(1,len(full_texts)+1).tolist(), full_texts))
        sorted_texts = [text for _,text in sorted(zip(current_ranking, full_texts))]
    
        max_stage_count = int(np.ceil(np.log2(len(sorted_texts))))

        handler.update_progress(0, max_stage_count)

        reranked_doc_ids = []

        for stage_id in range(max_stage_count): 
            if handler.should_cancel:
                break

            stage_winning_doc_id_combis = []
            stage_losing_ids = []
            current_id = 0
            if len(sorted_texts) % 2 == 1:
                stage_winning_doc_id_combis.append(sorted_texts[current_id])
                current_id += 1

            while(current_id < len(sorted_texts)):
                id1 = current_id
                id2 = current_id + 1
                current_id += 2

                doc1_text = sorted_texts[id1][1]
                doc2_text = sorted_texts[id2][1]

                llm_answer = self.llm_1_on_1_comparison(doc1=doc1_text, doc2=doc2_text, query=self.query if self.use_new_query else data.query, handler=handler)

                if llm_answer == 1:
                    stage_winning_doc_id_combis.append(sorted_texts[id1])
                    stage_losing_ids.append(sorted_texts[id2][0])
                else:
                    stage_winning_doc_id_combis.append(sorted_texts[id2])
                    stage_losing_ids.append(sorted_texts[id1][0])

            stage_losing_ids.reverse()
            reranked_doc_ids.extend(stage_losing_ids)
            sorted_texts = stage_winning_doc_id_combis

            handler.increment_progress()
            
        reranked_doc_ids.append(stage_winning_doc_id_combis[0][0])
        reranked_doc_ids.reverse()

        reranking_id = str(data.get_next_reranking_step_number())
        reranking_rank_name = "_reranking_rank_" + reranking_id + "_"
        data.documents[reranking_rank_name] = reranked_doc_ids
        data.set_rank_column(reranking_rank_name)
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data

    def llm_1_on_1_comparison(self, doc1:str, doc2:str, query:str, handler: PipelineStepHandler):
        timeout_max = 10
        prompt=f"Here are two texts, each marked with a [1] or [2] at the beginning. Which of the two following texts is more relevant to the Query:'{query}'. Only answer '[1]' if the first text is more relevant or '[2]' if the second one is more relevent!\n\n[1]: {doc1} \n\n[2]: {doc2}"
        for _ in range(timeout_max):
            potential_answer = self.llm.generate(prompt=prompt)
            parseable_check = re.match(r"\[(1|2)\]", potential_answer)
            if parseable_check is not None:
                return int(parseable_check.groups()[0])
            prompt_prolog = "Please only answer either [1] if the first one is more relevant or [2] if the second one is more relevant. If none of the two is relevant, answer [1]!"
            prompt = prompt_prolog + prompt
                
        handler.log("Comparison run into timeout!")
        return 1

    @staticmethod
    def get_info() -> dict:
        return {
            "name": TournamentStyleLLMRerankerStep.get_name(),
            "category": "Rerankers",
            "description": "Rerank documents based on a 1vs1 tournament style approach. Each step two docuemnts get compared using an LLM to a given query. The more suitable document advances - gets a higher ranking.",
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
        return "Tournament-Style Reranker Step"
