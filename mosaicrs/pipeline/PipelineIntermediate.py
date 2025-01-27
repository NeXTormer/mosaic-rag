from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd


class PipelineIntermediate:

    def __init__(self, query: str = None, arguments: Dict[str, Any] = {}):
        self.query: str = query
        self.arguments: Dict[str, Any] = arguments
        self.history = {}
        self.documents: pd.DataFrame = pd.DataFrame()

        self.metadata: pd.DataFrame = pd.DataFrame(columns=["title", "data"])