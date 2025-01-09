from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd


class PipelineIntermediate:

    def __init__(self, query: str = None, arguments: Dict[str, Any] = {}):
        self.query = query
        self.arguments = arguments
        self.history = {}
        self.data = pd.DataFrame()