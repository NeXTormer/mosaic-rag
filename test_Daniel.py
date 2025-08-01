from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.LocalPipeline import LocalPipeline
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.TFIDFRerankerStep import TFIDFRerankerStep
from mosaicrs.pipeline_steps.StopwordRemovalStep import StopWordRemovalStep

mds = MosaicDataSource(output_column="fullText")
reranker = TFIDFRerankerStep(input_column="fullText")


pipeline = LocalPipeline(steps=[mds, reranker])

result, success = pipeline.run(data=PipelineIntermediate(query='Werner', arguments={'limit': 10, 'index': 'simplewiki'}))

if success:
    print(result.documents)

