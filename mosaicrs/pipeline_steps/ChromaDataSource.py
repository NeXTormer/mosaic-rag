import os

import chromadb
import pandas as pd
import requests  # Added for making API calls to Ollama
from ollama import Client

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep

# --- Ollama Configuration ---
OLLAMA_URL = f"http://{os.environ.get('OLLAMA_HOST', 'localhost:11434')}"


class ChromaDataSource(PipelineStep):

    def _get_ollama_embedding(self, query: str, handler: PipelineStepHandler) -> list[float]:
        """
        Generates an embedding using raw requests to avoid library version mismatches.
        """
        url = f"{OLLAMA_URL}/api/embed"

        payload = {
            "model": self.ollama_model,
            "input": query
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Raises error for 404, 500, etc.

            data = response.json()
            print('data from ollama: ')
            print(data)

            return data['embeddings'][0]

        except requests.exceptions.RequestException as e:
            handler.log(f"Ollama Connection Error: {e}")
            if response.status_code == 404:
                raise ValueError(f"404: Model '{self.ollama_model}' not found or endpoint incorrect.")
            raise
        except Exception as e:
            handler.log(f"Error parsing Ollama response: {e}")
            raise


    def __init__(self, output_column: str = 'full_text', limit='10',
                 embedding_model='jina/jina-embeddings-v2-base-en:latest', chromadb_url='dallions:80', # chromadb_url='172.17.0.1:8000',
                 chromadb_collection='curlie_eng'):
        self.target_column_name = output_column
        self.limit = int(limit)

        CHROMA_HOST = chromadb_url.split(':')[0]
        CHROMA_PORT = int(chromadb_url.split(':')[1])
        CHROMA_COLLECTION_NAME = chromadb_collection

        self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        self.collection = self.client.get_collection(name=CHROMA_COLLECTION_NAME)

        self.ollama_model = embedding_model
        self.ollama_url = OLLAMA_URL

    def transform(self, data: PipelineIntermediate,
                  handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:

        handler.update_progress(0, 1)

        query_text = data.query
        data.documents = self.query_chromadb_to_dataframe(query_text, handler)
        data.set_text_column('full-text')
        data.set_rank_column('chromadb_distance')
        data.set_chip_column('curlielabels_en')
        # data.set_chip_column('curlielabels')

        handler.increment_progress()
        return data

    def query_chromadb_to_dataframe(self, query: str, handler: PipelineStepHandler) -> pd.DataFrame:
        print("Starting embedding with Ollama")
        # Generate the query embedding using the Ollama API
        query_embedding = self._get_ollama_embedding(query, handler)
        handler.log(f'Generated query embedding using Ollama model: {self.ollama_model}')
        print("Finished embedding, starting query")

        search_result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.limit
        )
        print("Finished query")

        ids = search_result.get('ids', [[]])[0]
        metadatas = search_result.get('metadatas', [[]])[0]
        distances = search_result.get('distances', [[]])[0]

        if not ids:
            return pd.DataFrame()

        data_for_df = [
            {
                **meta,
                'full-text': meta.get('plain_text'),
                'chromadb_distance': dist,
                'id': doc_id,
            }
            for doc_id, meta, dist in zip(ids, metadatas, distances)
        ]

        df = pd.DataFrame(data_for_df)
        return df

    @staticmethod
    def get_info() -> dict:
        """
        Provides metadata about the pipeline step for UI generation.
        """
        return {
            "name": ChromaDataSource.get_name(),
            "category": "Data Sources",
            "description": "Retrieve initial result set from a ChromaDB collection using vector search.",
            "parameters": {
                'chromadb_url': {
                    'title': 'ChromaDB URL',
                    'description': 'URL of the ChromaDB instance.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['172.17.0.1:8000', 'dallions:80'],
                    'default': '172.17.0.1:8000',
                },
                'embedding_model': {
                    'title': 'Ollama Embedding Model',
                    'description': 'Model used to embed the query via Ollama. Must be the same as the model used for generating the document embeddings.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['jina/jina-embeddings-v2-base-en:latest', 'mxbai-embed-large', 'nomic-embed-text'],
                    'default': 'jina/jina-embeddings-v2-base-en:latest',
                },
                'chromadb_collection': {
                    'title': 'Collection',
                    'description': 'Name of the ChromaDB collection to query.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['arts', 'health', 'recreation', 'science'],
                    'default': 'arts',
                },
                'limit': {
                    'title': 'Limit',
                    'description': 'Limit the number of results returned from ChromaDB.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['5', '10', '20', '50', '100'],
                    'default': '50',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        """
        Returns the display name of the pipeline step.
        """
        return "ChromaDB Data Source"