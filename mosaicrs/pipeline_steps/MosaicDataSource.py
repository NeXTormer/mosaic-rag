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


class MosaicDataSource(PipelineStep):

    def __init__(self, output_column: str = 'full_text', consider_query: bool = True, url: str = "https://mosaic.ows.eu/service/api/", default_search_path: str = "/search?", default_full_text_path: str = "/full-text?", search_index = 'simplewiki', limit = '10'):
        self.mosaic_url = url
        self.search_path_part = default_search_path
        self.full_text_path_part = default_full_text_path
        self.consider_query = consider_query
        self.target_column_name = output_column
        self.index = search_index
        self.limit = limit

        self.request_limiter_semaphore = asyncio.Semaphore(50)


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
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

        data.arguments['index'] = self.index
        data.arguments['limit'] = int(self.limit)

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

        df_docs[self.target_column_name] = None

        handler.update_progress(0, len(df_docs))


        df_docs = asyncio.run(self._fetch_all_texts(handler, df_docs))

        data.documents = df_docs
        
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        data.set_text_column(self.target_column_name)

        return data

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
                    'supported-values': ['http://localhost:8008', 'https://mosaic.felixholz.com', 'https://mosaic.ows.eu/service/api/'],
                    # 'default': 'https://mosaic.ows.eu/service/api/',
                    'default': 'https://mosaic.felixholz.com',
                },
                'limit': {
                    'title': 'Limit',
                    'description': 'Limit the amount of results returned from MOSAIC.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['5', '10', '20', '50', '100', '500'],
                    'default': '10',
                },
                'search_index': {
                    'title': 'Search index',
                    'description': 'Limit the search to a specific index.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['tech-knowledge', 'harry-potter', 'owi-snapshot-20240205-eng', 'simplewiki', 'unis-austria', 'medical-information', 'recipes'],
                    'default': 'simplewiki',
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
    

       
