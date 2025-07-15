import pandas as pd
from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum

class ReductionStep(PipelineStep):

    def __init__(self, k: str = "10", ranking_column: str = "_original_ranking_"):
        self.k = k.strip() if k.strip().isdigit() else "10"
        self.ranking_column = ranking_column
        
    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        
        k = int(self.k)

        if self.checkIfRankingColumnIsValid(data.metadata, self.ranking_column):
            if k > len(data.documents):
                k = len(data.documents)
                handler.log(f"The selected number of remaining rows after reduction is larger than the current result set. The number of remaining results is therefore set to the overall number of existing results (k={k}).")

            data.documents = data.documents.loc[data.documents[self.ranking_column].nsmallest(k).index]
        else:
            handler.log(f"The ranking column '{self.ranking_column}' does not exist in the current pipeline intermediate.\nThe following ranking columns exist: {self.getRankingColumns(data.metadata)}")

        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)
        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": ReductionStep.get_name(),
            "category": "Pre-Processing",
            "description": "Reduces the number of results in the returned result set according to a selected ranking column. Either you choose the pre-selected '_original_ranking_' or enter the wanted ranking coumn name. The columns created by applying a reranker have the form '_reranking_rank_n_', where n is the reranking ID.",
            "parameters": {
                'k': {
                    'title': 'Number of remaining results',
                    'description': 'A positive integer number indicating, how many results remain in the returned result set.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['5', '10', '50', '100'],
                    'default': '10',
                },
                'ranking_column': {
                    'title': 'Ranking column name',
                    'description': 'Column containing the ranking according to which the selection should happen.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['_original_ranking_'],
                    'default': '_original_ranking_',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "Result Reduction"

    def checkIfRankingColumnIsValid(self, metadata, ranking_column):
        return ((metadata['id'] == ranking_column) & (metadata['rank'] == True)).any()
    
    def getRankingColumns(self, metadata):
        return metadata[(metadata["rank"] == True)]["id"].tolist()
        
