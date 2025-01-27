from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.Pipeline import Pipeline
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.DocumentSummarizerStep import DocumentSummarizerStep
from mosaicrs.pipeline_steps.EmbeddingRerankerStep import EmbeddingRerankerStep
from mosaicrs.pipeline_steps.ResultsSummarizerStep import ResultsSummarizerStep

mds = MosaicDataSource(output_column="fullText")
summarizer = ResultsSummarizerStep(input_column="fullText", output_column="Test Summary")



pipeline = Pipeline(steps=[mds, summarizer])

result, success = pipeline.run(data=PipelineIntermediate(query='Sport in Austria', arguments={'limit': 10, 'index': 'simplewiki', 'lang': 'eng'}))

print(result.metadata.head())
