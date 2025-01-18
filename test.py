from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.Pipeline import Pipeline
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps.SummarizerStep import SummarizerStep
from mosaicrs.pipeline_steps.EmbeddingRerankerStep import EmbeddingRerankerStep

mds = MosaicDataSource(output_column="fullText")
sum = SummarizerStep(input_column="fullText", output_column="summary")
emrr = EmbeddingRerankerStep(input_column="summary")



pipeline = Pipeline(steps=[mds, sum, emrr])

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

