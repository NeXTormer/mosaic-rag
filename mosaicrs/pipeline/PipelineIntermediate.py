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
        self.metadata.loc[len(self.metadata)] = [column, False, True, False]

    def set_chip_column(self, column: str):
        self.metadata.loc[len(self.metadata)] = [column, False, False, True]

    def set_rank_column(self, column: str):
        self.metadata.loc[len(self.metadata)] = [column, True, False, False]
