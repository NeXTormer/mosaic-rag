import string
import numpy as np
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
import regex as re

def translate_language_code(language_code:str):
    """
        Transalates a language code of the ISO 639 Set3 format to a full language name. Example: "eng" -> "english". Only supported languages will be translated, all other langugae codes will return ''. Supported languages are eng/englisch, deu/german, fra/french, and ita/italian.

        language_code: str -> The language code which should be transalted to a full language name given in the format ISO 639 Set3.

        Returns the language full name for supported languages or '' for unsupported languages. 
    """

    language_dict = {
        "eng":"english",
        "deu":"german",
        "fra":"french",
        "ita":"italian",
        #TODO: Extend dict (https://stackoverflow.com/questions/54573853/nltk-available-languages-for-stopwords , https://www.nltk.org/api/nltk.stem.SnowballStemmer.html?highlight=stopwords)
    }
    if language_code in language_dict:
        return language_dict[language_code]
    
    return ""

# def get_lemmatization_code(language_name:str):
#     lemmatization_codes = {
#         "german": "de_core_news_sm",
#         "french": "fr_core_news_sm",
#         "italian": "it_core_news_sm"
#     }
#     if language_name in lemmatization_codes:
#         return lemmatization_codes[language_name]
    
#     return ""
              
def get_most_current_ranking(data: PipelineIntermediate):
    """
        This function returns the most up-to-date document ranking, using the latest available reranking column if present, otherwise falling back to the original ranking or a default sequential order.

        data: PipelineIntermediate -> PipelineIntermediate object which should be checked for the most up-to-date ranking column.
        
        Returns the most up-to-date ranking as a list of integers.
    """
    
    column_name_list = data.documents.columns.to_list()

    if "_original_ranking_" not in column_name_list:
        return np.arange(1,len(data.documents)+1).tolist()
    
    ranking = data.documents["_original_ranking_"].to_list()
    
    highest_reranking_id = 0
    for column_name in column_name_list:
        match = re.match(r"_reranking_rank_(\d+)_", column_name)
        if match is not None:
            reranking_id = int(match.groups()[0])
            if reranking_id > highest_reranking_id:
                highest_reranking_id = reranking_id

    if highest_reranking_id != 0:
        ranking = data.documents["_reranking_rank_"+str(highest_reranking_id)+"_"].to_list()

    return ranking
