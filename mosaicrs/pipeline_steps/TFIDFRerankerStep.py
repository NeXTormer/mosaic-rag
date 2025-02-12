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
        self.source_column_name = input_column
        self.similarity_metric = self.string_enum_mapping(similarity_metric)
        
        if query is not None:
            self.query = query
            self.use_new_query = True
        else:
            self.query = None
            self.use_new_query = False

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        handler.update_progress(1, 1)

        reranking_score_name = "_reranking_score_" + str(len(data.history) + 1) + "_"

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

        data.documents.sort_values(by=reranking_score_name, ascending= (False if self.similarity_metric in [SimilarityMetrics.COSINE, SimilarityMetrics.BM25] else True), inplace=True)
        data.history[str(len(data.history)+1)] = data.documents.copy(deep=True)

        return data

    def compute_cosine_scores(self, doc_tfidf, query_tfidf):
        return cosine_similarity(doc_tfidf, query_tfidf.reshape(1, -1)).flatten()
    
    def compute_euclidean_distance_scores(self, doc_tfidf, query_tfidf):
        return euclidean_distances(doc_tfidf, query_tfidf.reshape(1, -1)).flatten()
    
    def compute_manhatten_distance_scores(self, doc_tfidf, query_tfidf):
        return manhattan_distances(doc_tfidf, query_tfidf.reshape(1, -1)).flatten()
    
    def compute_bm25_scores(self, data):
        tokenized_doc_corpus = [entry.split(" ") if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        bm25 = BM25Okapi(tokenized_doc_corpus)
        tokenized_query = (self.query if self.use_new_query else data.query).split(" ")
        return bm25.get_scores(tokenized_query)

    def string_enum_mapping(self, selected_metric:str) -> SimilarityMetrics:
        if selected_metric not in {metric.value for metric  in SimilarityMetrics}:
            #TODO: Potential Warning in the future
            return SimilarityMetrics.COSINE
            
        return SimilarityMetrics(selected_metric)

    def get_TFIDF_scores(self, data):
        tfidf_vectorizer = TfidfVectorizer()

        source_docs = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]
        source_docs.append(self.query if self.use_new_query else data.query)

        source_doc_tfidf = tfidf_vectorizer.fit_transform(source_docs).toarray()

        query_tfidf = source_doc_tfidf[-1]
        source_doc_tfidf = source_doc_tfidf[:-1]

        return source_doc_tfidf, query_tfidf


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