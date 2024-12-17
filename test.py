from mosaicrs.data_source.MosaicDataSource import MosaicDataSource
from mosaicrs.llm.T5Transformer import T5Transformer
from mosaicrs.pipeline.Pipeline import Pipeline
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.SummarizerStep import SummarizerStep



t5 = T5Transformer('google/flan-t5-base')

pipeline = Pipeline(steps=[MosaicDataSource(), SummarizerStep(llm=t5), ])



result = pipeline.run(data=PipelineIntermediate(query='Werner', arguments={'limit': 1, 'index': 'simplewiki', 'lang': 'eng'}))

df = result.data
print(df['summary'])

