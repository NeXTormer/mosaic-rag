def translate_language_code(language_code:str):
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