from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline_steps.SummarizerStep import SupportedSummarizerModels
from mosaicrs.pipeline.Pipeline import Pipeline
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.SummarizerStep import SummarizerStep
from mosaicrs.pipeline_steps.EmbeddingRerankerStep import EmbeddingRerankerStep

mds = MosaicDataSource(destination_column="fullText")
emrr = EmbeddingRerankerStep(source_column="fullText")
sum = SummarizerStep(model=SupportedSummarizerModels.T5_Base, source_column="fullText", destination_column="summary")



pipeline = Pipeline(steps=[mds, emrr, sum])

result, success = pipeline.run(data=PipelineIntermediate(query='Sport in Austria', arguments={'limit': 10, 'index': 'simplewiki', 'lang': 'eng'}))

if success:
    df = result.data
    for i, text in enumerate(df["summary"].to_list()):
        print(f"{i+1}: {text}")

    print("\n\n")

    for i, text in enumerate(df["_original_ranking_"].to_list()):
        print(f"{i+1}: {text}")    
else:
    print("Abort pipeline")

