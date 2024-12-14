from mosaicrs.data_source.MosaicDataSource import MosaicDataSource
from mosaicrs.endpoint.SummarizerEndpoint import SummarizerEndpoint
from mosaicrs.llm.T5Transformer import T5Transformer
from mosaicrs.transformer.VeryBasicRankerTransformer import VeryBasicRankerTransformer

t5 = T5Transformer(model='google/flan-t5-base')

source = MosaicDataSource()
searcher = VeryBasicRankerTransformer()
summarizer = SummarizerEndpoint(llm=t5)

query = 'werner'

data = source.request_data(query, None)
filtered = searcher.transform(data, query)
summary = summarizer.process(filtered, query)

print("Summarizing for query: ", query)
print(summary)
