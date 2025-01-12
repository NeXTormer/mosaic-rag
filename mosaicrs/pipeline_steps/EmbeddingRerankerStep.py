
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from sentence_transformers import SentenceTransformer
from enum import Enum
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

# class SupportedSentenceTransformers(Enum):
#     Snowflake = "Snowflake/snowflake-arctic-embed-s"


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

    def transform(self, data: PipelineIntermediate) -> PipelineIntermediate:
        source_docs = data.data[self.source_column_name].to_list()

        doc_embeddings = self.sentence_transformer.encode(source_docs)
        query_embeddings = self.sentence_transformer.encode(self.query if self.use_new_query else data.query, prompt_name="query")

        scores = query_embeddings @ doc_embeddings.T
        reranking_score_name = "_reranking_score_" + str(len(data.history) + 1) + "_"
        data.data[reranking_score_name] = scores
        data.data.sort_values(by=reranking_score_name, ascending=False, inplace=True)

        data.history[str(len(data.history)+1)] = data.data.copy(deep=True)

        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": EmbeddingRerankerStep.get_name(),
            "parameters": {
                "input_column": "Embeddings are generated from this column",
                "query": "Optional. Replaces the existing query.",
                "model": "Embedding model. Default: Snowflake/snowflake-arctic-embed-s"
            }
        }

    @staticmethod
    def get_name() -> str:
        return "EmbeddingReranker"
    
