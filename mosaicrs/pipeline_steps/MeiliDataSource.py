import meilisearch
import pandas as pd

from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep


class MeiliDataSource(PipelineStep):

    def __init__(self, output_column: str = 'full-text', limit='100'):
        self.target_column_name = output_column
        self.limit = limit
        self.client = meilisearch.Client('http://dallions:7700', 'k5brEECPmrM5bhQpDDzvJz3v')
        self.output_column = output_column


    def transform(self, data: PipelineIntermediate,
                  handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:

        data.documents = self.query_meilisearch_to_dataframe(data.query)

        data.set_text_column(self.output_column)

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
                    'supported-values': ['5', '10', '20', '50', '100', '200', '500'],
                    'default': '200',
                },
                'output_column': {
                    'title': 'Output Column',
                    'description': 'Output column of the plain text',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'required': True,
                    'supported-values': ['plain_text', 'full-text'],
                    'default': 'full-text',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "MeiliSearch Data Source"



    def query_meilisearch_to_dataframe(self, query: str) -> pd.DataFrame:
            index = self.client.index('curlie_en')

            search_params = {
                'attributesToRetrieve': ['title', 'plain_text', 'url', 'curlielabels', 'curlielabels_en', 'ows_tags', 'warc_file'],
                'attributesToSearchOn': ['plain_text'],
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
                    self.output_column: hit.get('plain_text'),
                    'url': hit.get('url'),
                    'curlielabels': hit.get('curlielabels'),
                    'curlielabels_en': hit.get('curlielabels_en'),
                    'ows_tags': hit.get('ows_tags'),
                    'warc_file': hit.get('warc_file'),
                }
                for hit in hits
            ]

            # 6. Create Pandas DataFrame
            df = pd.DataFrame(data_for_df)

            return df