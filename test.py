from mosaicrs.data_source.MosaicDataSource import MosaicDataSource
from mosaicrs.endpoint.SummarizerEndpoint import SummarizerEndpoint
from mosaicrs.llm.T5Transformer import T5Transformer
from mosaicrs.transformer.VeryBasicRankerTransformer import VeryBasicRankerTransformer

t5 = T5Transformer(model='google/flan-t5-base')


source = MosaicDataSource()
#TODO: Namensgebung nochmal überdenken, RankerTransformer hört sich sehr stark nach LLM transformers sein
searcher = VeryBasicRankerTransformer()
summarizer = SummarizerEndpoint(llm=t5)


params = {
    "index":"simplewiki",
    "limit":"20",
    "lang":"eng"
}

query = 'werner'

#TODO: Object überdenken, welches zum Hin- und Hergeben zwischen den Komponenten dienen kann


data = source.request_data(query, params, True)
filtered = searcher.transform(data, query)
summary = summarizer.process(filtered, query)

print("Summarizing for query: ", query)
print(summary["textSnippet"])

for elem in summary["textSnippet"]:
    print(len(elem))
    print(elem)
    print("\n")
