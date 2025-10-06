import chromadb
import pandas as pd
import requests  # Added for making API calls to Ollama

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep

# --- Ollama Configuration ---
OLLAMA_URL = "http://dallions.tail44754b.ts.net/api/embeddings"


class ChromaDataSource(PipelineStep):

    def __init__(self, output_column: str = 'full_text', limit='10',
                 embedding_model='jina/jina-embeddings-v2-base-en', chromadb_url='dallions:80',
                 chromadb_collection='curlie_eng'):
        self.target_column_name = output_column
        self.limit = int(limit)

        CHROMA_HOST = chromadb_url.split(':')[0]
        CHROMA_PORT = int(chromadb_url.split(':')[1])
        CHROMA_COLLECTION_NAME = chromadb_collection

        self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        self.collection = self.client.get_collection(name=CHROMA_COLLECTION_NAME)

        # Set Ollama model and URL from parameters
        self.ollama_model = embedding_model
        self.ollama_url = OLLAMA_URL

    def _get_ollama_embedding(self, query: str, handler: PipelineStepHandler) -> list[float]:
        """
        Generates an embedding for a given query using the Ollama API.
        """
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": self.ollama_model, "prompt": query},
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json().get("embedding")

        except requests.exceptions.RequestException as e:
            handler.log(f"Error connecting to Ollama API: {e}")
            # You might want to re-raise the exception or handle it differently
            raise ConnectionError(f"Failed to connect to Ollama API at {self.ollama_url}. Is Ollama running?") from e
        except ValueError as e:
            handler.log(f"Error processing Ollama API response: {e}")
            raise

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
                    'supported-values': ['dallions:80'],
                    'default': 'dallions:80',
                },
                'embedding_model': {
                    'title': 'Ollama Embedding Model',
                    'description': 'Model used to embed the query via Ollama. Must be the same as the model used for generating the document embeddings.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['jina/jina-embeddings-v2-base-en', 'mxbai-embed-large', 'nomic-embed-text'],
                    'default': 'jina/jina-embeddings-v2-base-en',
                },
                'chromadb_collection': {
                    'title': 'Collection',
                    'description': 'Name of the ChromaDB collection to query.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['curlie_eng', 'curlie', 'test', 'ows'],
                    'default': 'curlie_eng',
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