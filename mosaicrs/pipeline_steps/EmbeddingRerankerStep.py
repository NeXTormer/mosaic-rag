from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from sentence_transformers import SentenceTransformer
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

class EmbeddingRerankerStep(PipelineStep):

    def __init__(self, input_column: str, query: str = None, model: str = "Snowflake/snowflake-arctic-embed-s"):
        self.sentence_transformer = SentenceTransformer(model)
        self.source_column_name = input_column
        if query is not None:
            self.query = query
            self.use_new_query = True
        else:
            self.query = None
            self.use_new_query = False

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        handler.update_progress(1, 1)

        doc_embeddings, query_embeddings = self.create_embeddings(data)

        #cosine similarity
        scores = query_embeddings @ doc_embeddings.T
        reranking_score_name = "_reranking_score_" + str(len(data.history) + 1) + "_"
        data.documents[reranking_score_name] = scores
        data.documents.sort_values(by=reranking_score_name, ascending=False, inplace=True)

        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data


    def create_embeddings(self, data: PipelineIntermediate):
        source_docs = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]

        #Is already normalized
        doc_embeddings = self.sentence_transformer.encode(source_docs)

        query_embeddings = self.sentence_transformer.encode(self.query if self.use_new_query else data.query, prompt_name="query")

        return doc_embeddings, query_embeddings


    @staticmethod
    def get_info() -> dict:
        return {
            "name": EmbeddingRerankerStep.get_name(),
            "category": "Rerankers",
            "description": "Perform reranking based on generated dense embeddings using CosineSimilarity.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'The document embeddings are generated for this column.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['full-text', 'summary'],
                    'default': 'full-text',
                },
                'query': {
                    'title': 'Optional query',
                    'description': 'An additional query, different from the main query, used for reranking. Optional.',
                    'type': 'string',
                    'required': False,
                    'default': '',
                },
                'model': {
                    'title': 'Embedding model',
                    'description': 'The model used to generate the embeddings.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['Snowflake/snowflake-arctic-embed-s', 'Snowflake/snowflake-arctic-embed-m'],
                    'default': 'Snowflake/snowflake-arctic-embed-s',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "EmbeddingReranker"
    
