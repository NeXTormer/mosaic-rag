from mosaicrs.transformer.Transformer import Transformer


class VeryBasicRankerTransformer(Transformer):
    def __init__(self):
        pass

    def transform(self, data, query):
        new_data = data[data['textSnippet'].str.contains(query, case=False, na=False)]
        new_data = new_data[new_data['wordCount'] > 20]
        return new_data
