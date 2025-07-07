from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd


class PipelineIntermediate:

    def __init__(self, query: str = None, arguments: Dict[str, Any] = {}):
        self.query: str = query

        # TODO:
        # self.user_query: str = query
        # self.expanded_queries: List[str] = []

        self.arguments: Dict[str, Any] = arguments
        self.history = {}


        self.documents: pd.DataFrame = pd.DataFrame()
        self.aggregated_data: pd.DataFrame = pd.DataFrame(columns=['title', 'data'])

        self.metadata: pd.DataFrame = pd.DataFrame(columns=['id', 'rank', 'text', 'chip'])


    def set_column_type(self, column_id: str, column_type: str):
        match column_type:
            case 'text':
                self.set_text_column(column_id)
            case 'chip':
                self.set_chip_column(column_id)
            case 'rank':
                self.set_rank_column(column_id)


    def set_text_column(self, column: str):
        self.add_update_column(column, False, True, False)

    def set_chip_column(self, column: str):
        self.add_update_column(column, False, False, True)

    def set_rank_column(self, column: str):
        self.add_update_column(column, True, False, False)
        
    def add_update_column(self, column, rank, text, chip):
        if column in self.metadata["id"].values:
            self.metadata.loc[self.metadata["id"] == column, ['rank', 'text', 'chip']] = [rank, text, chip]
        else:
            self.metadata.loc[len(self.metadata)] = [column, rank, text, chip]

    def get_next_reranking_step_number(self):
        return (self.metadata['rank'] == True).sum()