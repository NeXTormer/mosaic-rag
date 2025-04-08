import meilisearch
import pandas as pd

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep


class MeiliDataSource(PipelineStep):

    def __init__(self, output_column: str = 'full_text', limit='100'):
        self.target_column_name = output_column
        self.limit = limit
        self.client = meilisearch.Client('http://127.0.0.1:7700', 'eS1o1KEq6NHFjCCvZhFU9N_zdr9locqxJRZHkWEQ4AA')

    def transform(self, data: PipelineIntermediate,
                  handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:

        data.documents = self.query_meilisearch_to_dataframe(data.query)

        data.set_text_column('full-text')

        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": MeiliDataSource.get_name(),
            "category": "Data Sources",
            "description": "Retrieve initial result set from a MOSAIC instance.",
            "parameters": {
                'limit': {
                    'title': 'Limit',
                    'description': 'Limit the amount of results returned from MOSAIC.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['5', '10', '20', '50', '100', '500'],
                    'default': '10',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "MeiliSearch Data Source"



    def query_meilisearch_to_dataframe(self, query: str) -> pd.DataFrame:
            index = self.client.index('ows2')

            search_params = {
                'attributesToRetrieve': ['title', 'plain_text', 'url'],
                'limit': int(self.limit)
            }
            search_result = index.search(query, search_params)

            hits = search_result.get('hits', []) # Use .get for safety

            # 5. Prepare data for DataFrame
            # Using .get() for each key ensures that if a field is missing in a
            # specific document, it gets a None value instead of raising an error.
            data_for_df = [
                {
                    'title': hit.get('title'),
                    'full-text': hit.get('plain_text'),
                    'url': hit.get('url'),
                }
                for hit in hits
            ]

            # 6. Create Pandas DataFrame
            df = pd.DataFrame(data_for_df)

            return df