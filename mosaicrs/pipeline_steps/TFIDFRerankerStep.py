import mosaicrs.pipeline.PipelineErrorHandling as err

from sklearn.feature_extraction.text import TfidfVectorizer
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from enum import Enum
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances, manhattan_distances
from rank_bm25 import BM25Okapi

class SimilarityMetrics(Enum):
    COSINE = "Cosine"
    EUCLIDEAN = "Euclidean"
    MANHATTAN = "Manhattan"
    BM25 = "BM25"


class TFIDFRerankerStep(PipelineStep):
    
    def __init__(self, input_column: str, query: str = None, similarity_metric: str = "Cosine"):
        """
            Performs document reranking using TF-IDF or BM25 with configurable similarity metrics.   

            input_column: str -> Column in the PipelineIntermediate used to build TF-IDF/BM25 vectors. \n
            query: str -> Optional query string for reranking. If None, the pipeline's main query is used. \n
            similarity_metric: str -> One of {"Cosine", "Euclidean", "Manhattan", "BM25"}. Default is "Cosine". 
        """

        self.source_column_name = input_column
        self.similarity_metric, self.metric_exists = self.string_enum_mapping(similarity_metric)
        
        if query is not None:
            self.query = query
            self.use_new_query = True
        else:
            self.query = None
            self.use_new_query = False


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. Executes the reranking process by computing scores and assigning ranks.   
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """

        if not self.metric_exists:
            handler.warning(err.PipelineStepWarning(err.WarningMessages.MetricDoesNotExist))

        handler.update_progress(1, 1)

        reranking_id = str(data.get_next_reranking_step_number())
        reranking_score_name = "_reranking_score_" + reranking_id + "_"

        if self.similarity_metric == SimilarityMetrics.BM25:
            data.documents[reranking_score_name] = self.compute_bm25_scores(data)
        else:
            doc_tfidf, query_tfidf = self.get_TFIDF_scores(data)

            if self.similarity_metric == SimilarityMetrics.COSINE:
                data.documents[reranking_score_name] = self.compute_cosine_scores(doc_tfidf, query_tfidf)
            elif self.similarity_metric == SimilarityMetrics.EUCLIDEAN:
                data.documents[reranking_score_name] = self.compute_euclidean_distance_scores(doc_tfidf, query_tfidf)
            elif self.similarity_metric == SimilarityMetrics.MANHATTAN:
                data.documents[reranking_score_name] = self.compute_manhatten_distance_scores(doc_tfidf, query_tfidf)

        reranking_rank_name = "_reranking_rank_" + reranking_id + "_"
        data.documents[reranking_rank_name] = data.documents[reranking_score_name].rank(method="first", ascending=(False if self.similarity_metric in [SimilarityMetrics.COSINE, SimilarityMetrics.BM25] else True)).astype(int)
        data.set_rank_column(reranking_rank_name)
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data


    @staticmethod
    def get_info() -> dict:
        return {
            "name": TFIDFRerankerStep.get_name(),
            "category": "Rerankers",
            "description": "Perform reranking based on TF-IDF vectors and a selected similarity metric.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'The TF-IDF scores get generated based on this column.',
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
                'similarity_metric': {
                    'title': 'Similarity Metric',
                    'description': 'The similarity metric used to compute the reranking on the tf idf scores of query and documents. Default: Cosine',
                    'type': 'dropdown',
                    'enforce-limit': True,
                    'required': True,
                    'supported-values': [metric.value for metric in SimilarityMetrics],
                    'default': 'Cosine',
                },
            }
        }


    @staticmethod
    def get_name() -> str:
        return "TF-IDF-Reranker"
    

    def compute_cosine_scores(self, doc_tfidf, query_tfidf):
        """
            Computes Cosine similarity scores between query and documents.  

            doc_tfidf: np.ndarray -> TF-IDF vectors of documents. \n
            query_tfidf: np.ndarray -> TF-IDF vector of the query. \n

            It returns a 1D array of similarity scores (higher = more relevant). 
        """
        
        return cosine_similarity(doc_tfidf, query_tfidf.reshape(1, -1)).flatten()
    
    def compute_euclidean_distance_scores(self, doc_tfidf, query_tfidf):
        """
            Computes Euclidean distance between query and document vectors.  

            doc_tfidf: np.ndarray -> TF-IDF vectors of documents. \n
            query_tfidf: np.ndarray -> TF-IDF vector of the query. \n

            It returns a 1D array of distance scores (lower = more relevant). 
        """
        return euclidean_distances(doc_tfidf, query_tfidf.reshape(1, -1)).flatten()
    
    def compute_manhatten_distance_scores(self, doc_tfidf, query_tfidf):
        """
            Computes Manhattan (L1) distance between query and document vectors.  

            doc_tfidf: np.ndarray -> TF-IDF vectors of documents. \n
            query_tfidf: np.ndarray -> TF-IDF vector of the query. \n

            It returns a 1D array of distance scores (lower = more relevant). 
        """
        return manhattan_distances(doc_tfidf, query_tfidf.reshape(1, -1)).flatten()
    
    def compute_bm25_scores(self, data):
        """
            Computes BM25 scores between query and documents.  

            data: PipelineIntermediate -> Provides documents and query text. \n

            It returns a list of BM25 scores (higher = more relevant). 
        """

        if self.source_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.source_column_name)
         
        tokenized_doc_corpus = [entry.split(" ") if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        bm25 = BM25Okapi(tokenized_doc_corpus)
        tokenized_query = (self.query if self.use_new_query else data.query).split(" ")
        return bm25.get_scores(tokenized_query)

    def string_enum_mapping(self, selected_metric:str) -> SimilarityMetrics:
        """
            Maps a user-provided string to the appropriate SimilarityMetrics enum value.  

            selected_metric: str -> The metric name as a string. \n

            If the metric is invalid, defaults to Cosine similarity and False as a second return value. \n
            If the metric is valid it returns a SimilarityMetrics enum value and True as a second return value. 
        """
        
        if selected_metric not in {metric.value for metric  in SimilarityMetrics}:
            
            return SimilarityMetrics.COSINE, False
            
        return SimilarityMetrics(selected_metric), True

    def get_TFIDF_scores(self, data):
        """
            Generates TF-IDF vectors for both documents and query.  

            data: PipelineIntermediate -> Provides documents and query. \n

            It returns a tuple: (doc_tfidf, query_tfidf). 
        """

        if self.source_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.source_column_name)

        tfidf_vectorizer = TfidfVectorizer()

        source_docs = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        source_docs.append(self.query if self.use_new_query else data.query)

        source_doc_tfidf = tfidf_vectorizer.fit_transform(source_docs).toarray()

        query_tfidf = source_doc_tfidf[-1]
        source_doc_tfidf = source_doc_tfidf[:-1]

        return source_doc_tfidf, query_tfidf
