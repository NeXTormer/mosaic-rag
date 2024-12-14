from typing import Any
import requests
import json
import pandas as pd

from mosaicrs.data_source.DataSource import DataSource


class MosaicDataSource(DataSource):
    SEARCH_PATH = "api/search?q="


    def __init__(self, url: str = "https://mosaic.ows.eu/service/"):
        self.mosaic_url = url


    def request_data(self, query: str, arguments: dict[str, Any] | None) -> pd.DataFrame:
        response = requests.get(''.join([self.mosaic_url, MosaicDataSource.SEARCH_PATH, query]))
        json_data = json.loads(response.text)

        docs = []

        for x in json_data['results']:
            for k, v in x.items():
                for d in v:
                    docs.append(d)

        return pd.DataFrame(docs)