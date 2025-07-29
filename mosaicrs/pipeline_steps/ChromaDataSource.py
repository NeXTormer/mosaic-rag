import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep


class ChromaDataSource(PipelineStep):
    model = None

    def __init__(self, output_column: str = 'full_text', limit='10', embedding_model='jinaai/jina-embeddings-v2-small-en', chromadb_url='dallions:8002', chromadb_collection='curlie'):
        self.target_column_name = output_column
        self.limit = int(limit)

        CHROMA_HOST = chromadb_url.split(':')[0]
        CHROMA_PORT = int(chromadb_url.split(':')[1])
        CHROMA_COLLECTION_NAME = chromadb_collection

        self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        self.collection = self.client.get_collection(name=CHROMA_COLLECTION_NAME)
        self.model = SentenceTransformer(embedding_model)


    def transform(self, data: PipelineIntermediate,
                  handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:

        handler.update_progress(0, 1)


        query_text = data.query
        data.documents = self.query_chromadb_to_dataframe(query_text, handler)
        data.set_text_column('full-text')
        data.set_rank_column('chromadb_distance')

        handler.increment_progress()
        return data

    def query_chromadb_to_dataframe(self, query: str, handler: PipelineStepHandler) -> pd.DataFrame:
        query_embedding = self.model.encode(query).tolist()
        handler.log(f'Generated query embedding: {query_embedding}')
        search_result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.limit
        )

        ids = search_result.get('ids', [[]])[0]
        documents = search_result.get('documents', [[]])[0]
        metadatas = search_result.get('metadatas', [[]])[0]
        distances = search_result.get('distances', [[]])[0]

        if not ids:
            return pd.DataFrame()

        data_for_df = [
            {
                'title': meta.get('url'),
                'full-text': doc,
                'url': meta.get('url'),
                'chromadb_distance': dist,
                'id': doc_id,
                'curlielabels': meta.get('curlielabels')
            }
            for doc_id, doc, meta, dist in zip(ids, documents, metadatas, distances)
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
                    'supported-values': ['dallions:8002'],
                    'default': 'dallions:8002',
                },
                'embedding_model': {
                    'title': 'Embedding Model',
                    'description': 'Model used to embed the query. Must be the same as the model used for generating the document embeddings.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['jinaai/jina-embeddings-v2-small-en'],
                    'default': 'jinaai/jina-embeddings-v2-small-en',
                },
                'chromadb_collection': {
                    'title': 'Collection',
                    'description': 'Name of the ChromaDB collection to query.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['curlie', 'test', 'ows'],
                    'default': 'curlie',
                },
                'limit': {
                    'title': 'Limit',
                    'description': 'Limit the number of results returned from ChromaDB.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['5', '10', '20', '50', '100'],
                    'default': '10',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        """
        Returns the display name of the pipeline step.
        """
        return "ChromaDB Data Source"
