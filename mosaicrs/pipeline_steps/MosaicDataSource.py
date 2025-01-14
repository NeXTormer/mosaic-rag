from typing import Any
import requests
import json
import pandas as pd
import regex as re
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
import logging


class MosaicDataSource(PipelineStep):

    def __init__(self, output_column: str = 'full_text', consider_query: bool = True, url: str = "http://localhost:8008", default_search_path: str = "/search?", default_full_text_path: str = "/full-text?"):
        self.mosaic_url = url
        self.search_path_part = default_search_path
        self.full_text_path_part = default_full_text_path
        self.consider_query = consider_query
        self.target_column_name = output_column


    def transform(self, data: PipelineIntermediate) -> PipelineIntermediate:
        if self.consider_query:
            # Check query for multiple words and if so convert to correct format
            if re.search("^[a-zA-Z]+(\+[a-zA-Z]+)*$", data.query) is None:
                query_words = [word for word in data.query.split(' ') if bool(word.strip())]
                converted_query = '+'.join(query_words)
            
            #Check arguments for query
            if (data.query is None and "q" not in data.arguments):
                raise ValueError("Error: consider_query is true but not query is given. Neither in the PipelineIntermediate or in the arguments!")
            elif ("q" in data.arguments and data.arguments["q"] != data.query):
                raise ValueError("Error: multiple different search queries found!")

            if "q" not in data.arguments:
                data.arguments["q"] = data.query

        else:
            if "q" in data.arguments:
                data.arguments.pop("q")

        data.arguments['index'] = 'simplewiki'
        data.arguments['limit'] = 10
        response = requests.get(''.join([self.mosaic_url, self.search_path_part]), params=data.arguments)

        if response.status_code == 404:
            logging.error('Source not found')
            raise ValueError("Error: Source not found")

        json_data = json.loads(response.text)

        if "results" not in json_data:
            logging.error('no \'results\' in json data')
            return data

        extracted_docs = []
        for index_result in json_data["results"]:
            for _, v in index_result.items():
                for doc in v:
                    extracted_docs.append(doc)
        
        df_docs = pd.DataFrame(extracted_docs)
        df_docs["_original_ranking_"] = df_docs.index
        df_docs[self.target_column_name] = df_docs.apply(lambda row: self._request_full_text(row['id']), axis=1)
        data.data = df_docs
        
        data.history[str(len(data.history)+1)] = data.data.copy(deep=True)


        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": MosaicDataSource.get_name(),
            "parameters": {
                'output_column': {
                    'title': 'Output column name',
                    'description': 'The column where the full text of each document is stored.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'url': {
                    'title': 'MOSAIC service URL',
                    'description': 'The URL of the MOSAIC instance to use. Must be accessible from the public web.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['http://localhost:8008', 'https://mosaic.felixholz.com', 'https://mosaic.ows.eu/service/api/'],
                    'default': 'http://localhost:8008',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "MosaicDataSource"

    def _request_full_text(self, doc_id: str) -> str:
        response = requests.get(''.join([self.mosaic_url, self.full_text_path_part]), params={'id': doc_id})
        if response.status_code == 200:
            json_data = json.loads(response.text)
            return json_data['fullText']
        else:
            return ""

    

       
