import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from sentence_transformers import SentenceTransformer
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

class EmbeddingRerankerStep(PipelineStep):

    def __init__(self, input_column: str, query: str = None, model: str = "Snowflake/snowflake-arctic-embed-s"):
        """
            Performs document reranking based on dense embeddings. This step uses a SentenceTransformer model to encode both the documents and the query into embeddings. It then computes cosine similarity scores between query and document embeddings, ranks the documents accordingly, and stores the reranking results in the PipelineIntermediate. 

            input_column: str -> Column of the PipelineIntermediate used to generate embeddings (e.g., "full-text"). \n
            query: str -> Optional query string for reranking. If not provided, the main pipeline query is used. \n
            model: str -> SentenceTransformer model name used to generate embeddings. Default: "Snowflake/snowflake-arctic-embed-s". 
        """

        self.sentence_transformer = SentenceTransformer(model)
        self.source_column_name = input_column
        if query is not None:
            self.query = query
            self.use_new_query = True
        else:
            self.query = None
            self.use_new_query = False

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. The 'transform()' method executes the reranking logic by generating embeddings, computing cosine similarity, and updating the PipelineIntermediate with scores and ranks. 
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """
        
        handler.update_progress(1, 1)

        doc_embeddings, query_embeddings = self.create_embeddings(data)

        #cosine similarity
        scores = query_embeddings @ doc_embeddings.T
        
        reranking_id = str(data.get_next_reranking_step_number())
        reranking_score_name = "_reranking_score_" + reranking_id + "_"
        data.documents[reranking_score_name] = scores
        reranking_rank_name = "_reranking_rank_" + reranking_id + "_"
        data.documents[reranking_rank_name] = data.documents[reranking_score_name].rank(method="first", ascending=False).astype(int)
        data.set_rank_column(reranking_rank_name)
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)
        return data


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
    

    def create_embeddings(self, data: PipelineIntermediate):
        """
            Generates dense embeddings for both the documents and the query.  

            data: PipelineIntermediate -> Object containing documents and query. \n

            It returns a tuple: (doc_embeddings, query_embeddings). 
        """
        if self.source_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.source_column_name)

        source_docs = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]

        #Is already normalized
        doc_embeddings = self.sentence_transformer.encode(source_docs)

        query_embeddings = self.sentence_transformer.encode(self.query if self.use_new_query else data.query, prompt_name="query")

        return doc_embeddings, query_embeddings
    
