import pandas as pd
import mosaicrs.pipeline.PipelineErrorHandling as err

from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum


class ReductionStep(PipelineStep):

    def __init__(self, k: str = "10", ranking_column: str = "_original_ranking_"):
        """
           Reduces the number of documents in the PipelineIntermediate to the top `k` based on a `ranking column`. Either you choose the pre-selected '_original_ranking_' or enter the wanted ranking coumn name. The columns created by applying a reranker have the form '_reranking_rank_n_', where n is the reranking ID. 

            k: str -> A string that should represent an integer, which indicates the number of items that should remain in the document set f the PipelineIntermediate after this step. Default: '10'\n
            ranking_column: str ->  Column containing the ranking in the PipelineIntermediate according to which the selection should happen. Default: '_original_ranking_'
        """
            
        self.k = k.strip() if k.strip().isdigit() else "10"
        self.ranking_column = ranking_column
        
    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. 
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """
                
        k = int(self.k)

        if self.checkIfRankingColumnIsValid(data.metadata, self.ranking_column):
            if k > len(data.documents):
                k = len(data.documents)
                handler.warning(err.PipelineStepWarning(err.WarningMessages.TooLargeKValue, k=k))

            data.documents = data.documents.loc[data.documents[self.ranking_column].nsmallest(k).index]
        else:
            raise err.PipelineStepError(err.ErrorMessages.InvalidRankingColumn, ranking_column=self.ranking_column, given_columns=self.getRankingColumns(data.metadata))

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
        """
            Checks if a given column name is a ranking column in the current metadata dataframe or not.

            metadata: pd.DataFrame -> Contains the current metadata information of the PipelineIntermediate.
            ranking_column: The column name of the column which should be checked. 

            Returns True if the column given by 'ranking_column' is infact a rank column, else False
        """

        return ((metadata['id'] == ranking_column) & (metadata['rank'] == True)).any()
    
    def getRankingColumns(self, metadata):
        """
            Returns a list of all column names of the current PipelineIntermediate version which are rank columns. 

            metadata:  pd.DataFrame -> Contains the current metadata information of the PipelineIntermediate.

            Returns a string of all given names of rank columns seperated by a ','
        """

        return ", ".join(metadata[(metadata["rank"] == True)]["id"].tolist())
        
