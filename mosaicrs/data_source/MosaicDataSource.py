from typing import Any
import requests
import json
import pandas as pd
import regex as re

from mosaicrs.data_source.DataSource import DataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate


class MosaicDataSource(DataSource):
    SEARCH_PATH = "/search?"
    FULL_TEXT_PATH = '/full-text?'


    def __init__(self, url: str = "http://localhost:8008"):
        self.mosaic_url = url


    def request_data(self, data: PipelineIntermediate) -> PipelineIntermediate:
        query = data.query
        arguments = data.arguments


        if re.search("^[a-zA-Z]+(\+[a-zA-Z]+)*$", query) is None:
            query = '+'.join(query.split(' '))
        
        if arguments is None:
            arguments = {}
        elif "q" in arguments and arguments["q"] != query:
            print("Error: Multiple different search terms found!")
            raise ValueError("Multiple different search terms found!") # Note: don't return null as an error, this is python, not C xD

        elif "q" not in arguments:
            arguments["q"] = query

        
        response = requests.get(''.join([self.mosaic_url, MosaicDataSource.SEARCH_PATH]), params=arguments)
        json_data = json.loads(response.text)

        docs = []

        for x in json_data['results']:
            for k, v in x.items():
                for d in v:
                    docs.append(d)

        df_docs = pd.DataFrame(docs)

        # Load full text

        df_docs['full_text'] = df_docs.apply(lambda row: self._request_full_text(row['id']), axis=1)


        data.data = df_docs
        return data


    def _request_full_text(self, doc_id: str) -> str:
        response = requests.get(''.join([self.mosaic_url, MosaicDataSource.FULL_TEXT_PATH]), params={'id': doc_id})
        json_data = json.loads(response.text)

        return json_data['fullText']
