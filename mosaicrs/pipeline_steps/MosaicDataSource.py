import requests
import json
import pandas as pd
import regex as re
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
import logging

import asyncio
import aiohttp
import ssl
from mosaicrs.pipeline_steps.utils import get_most_current_ranking


class MosaicDataSource(PipelineStep):

    def __init__(self, output_column: str = 'full_text', consider_query: bool = True, url: str = "https://mosaic.ows.eu/service/api", default_search_path: str = "/search?", default_full_text_path: str = "/full-text?", search_index = 'simplewiki', limit = '10'):
        self.mosaic_url = url
        self.search_path_part = default_search_path
        self.full_text_path_part = default_full_text_path
        self.consider_query = consider_query
        self.target_column_name = output_column
        self.index = search_index
        self.limit = limit.strip() if limit.strip().isdigit() else "10"

        self.request_limiter_semaphore = asyncio.Semaphore(50)


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        data.arguments.clear()

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

        if self.index != "all":
            data.arguments['index'] = self.index

        data.arguments['limit'] = int(self.limit)

        response = requests.get(''.join([self.mosaic_url, self.search_path_part]), params=data.arguments)

        if response.status_code == 404:
            handler.log('Data Source service not found (404)')
            raise ValueError("Error: Source not found")

        json_data = json.loads(response.text)

        if "results" not in json_data:
            handler.log('no \'results\' in json data')
            return data

        extracted_docs = []
        for index_result in json_data["results"]:
            for key, v in index_result.items():
                for doc in v:
                    doc["_source_index_"] = key
                    extracted_docs.append(doc)
        
        df_docs = pd.DataFrame(extracted_docs)
        df_docs["_original_ranking_"] = df_docs.index + 1

        df_docs[self.target_column_name] = None

        handler.update_progress(0, len(df_docs))



        if 'mainContent' in df_docs and (df_docs['mainContent'].str.len() > 0).any():
            df_docs[self.target_column_name] = df_docs['mainContent']
        else:
            df_docs = asyncio.run(self._fetch_all_texts(handler, df_docs))

        if data.documents.empty:
            data.documents = df_docs
            data.set_text_column(self.target_column_name)
            data.set_rank_column('_original_ranking_')
        else:
            prev_max_ranking_id = max(get_most_current_ranking(data))
            df_docs["_original_ranking_"] += prev_max_ranking_id

            if len(data.metadata[data.metadata["rank"]]) != 1:  
                ranking_columns = data.metadata[data.metadata["rank"]]["id"].to_list()
                for ranking_column in ranking_columns:
                    if ranking_column != "_original_ranking_":
                        df_docs[ranking_column] = df_docs["_original_ranking_"] #Version1: giving docs original continous ranking
                        #df_docs[ranking_column] = 1_000_000_000 #Version2: giving an extremly high ranking - might be a problem for certain combinations of steps

            data.documents = pd.concat([data.documents, df_docs], ignore_index=True)

        data.set_chip_column("_source_index_")

        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data

    @staticmethod
    def get_index_names():
        url = "https://mosaic.ows.eu/service/api/index-info"

        try:
            # Make the GET request
            response = requests.get(url)
            # Raise an exception for HTTP errors (4xx or 5xx)
            response.raise_for_status()

            data = response.json()

            # Extract the first key from each dictionary inside the 'results' list
            # result.keys() returns a view, so we convert to list or take the next iterator
            index_names = [list(item.keys())[0] for item in data.get("results", [])]

            return index_names

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return []

    @staticmethod
    def get_info() -> dict:
        return {
            "name": MosaicDataSource.get_name(),
            "category": "Data Sources",
            "description": "Retrieve initial result set from a MOSAIC instance.",
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
                    'supported-values': ['http://localhost:8008', 'https://mosaic.felixholz.com', 'https://mosaic.ows.eu/service/api'],
                    'default': 'https://mosaic.ows.eu/service/api',
                },
                'limit': {
                    'title': 'Limit',
                    'description': 'Limit the amount of results returned from MOSAIC.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['5', '10', '20', '50', '100', '500'],
                    'default': '50',
                },
                'search_index': {
                    'title': 'Search index',
                    'description': 'Limit the search to a specific index.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': list(set(MosaicDataSource.get_index_names() + ['arts', 'health', 'recreation', 'science', 'all'])),
                    'default': 'arts',
                },
            }
        }



    @staticmethod
    def get_name() -> str:
        return "MosaicDataSource"

    def _request_full_text(self, doc_id: str, handler: PipelineStepHandler) -> str:
        response = requests.get(''.join([self.mosaic_url, self.full_text_path_part]), params={'id': doc_id})
        handler.increment_progress()
        if response.status_code == 200:
            json_data = json.loads(response.text)
            return json_data['fullText']
        else:
            return ""

    async def _request_full_text_async(self, session, doc_id: str, handler: PipelineStepHandler) -> str:
        url = ''.join([self.mosaic_url, self.full_text_path_part])
        cache_key = 'full-text-for-id-{}'.format(doc_id)

        result = handler.get_cache(cache_key)
        if result is not None:
            handler.increment_progress()
            return result


        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # Disables SSL verification

        async with self.request_limiter_semaphore:
            async with session.get(url, ssl=ssl_context, params={'id': doc_id}) as response:
                result = await response.text()
                handler.increment_progress()

                json_data = json.loads(result)
                if 'fullText' in json_data:
                    handler.put_cache(cache_key, json_data['fullText'])
                    return json_data['fullText']

                return result


    async def _fetch_all_texts(self, handler: PipelineStepHandler, df_docs):
        async with aiohttp.ClientSession() as session:
            tasks = [self._request_full_text_async(session, row['id'], handler) for _, row in df_docs.iterrows()]
            results = await asyncio.gather(*tasks)


        df_docs[self.target_column_name] = results
        return df_docs
    

       
