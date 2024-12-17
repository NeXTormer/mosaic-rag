from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd


class PipelineIntermediate:

    def __init__(self, query, arguments):
        self.query = query
        self.arguments = arguments
        self.history = []


    data: pd.DataFrame | None
    query: str
    arguments: Dict[str, Any]
    history: List[pd.DataFrame]

