import pandas as pd
import mosaicrs.pipeline.PipelineErrorHandling as err

from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum


class CurlieFilterStep(PipelineStep):

    def __init__(self, curlie_column: str = "curlielabels_en", filter_by: str = '', filter_mode: str = 'OR'):
        self.curlie_column = curlie_column
        self.filter_by = filter_by
        self.filter_mode = filter_mode

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        df = data.documents

        # Ensure the specified column exists in the dataframe
        if self.curlie_column not in df.columns:
            # handler.warning(err.pipeline_column_does_not_exist(self.curlie_column))
            return data

        # If filter_by is empty or just whitespace, no filtering is needed.
        if not self.filter_by or not self.filter_by.strip():
            return data

        # Prepare the set of labels to filter by for efficient lookups
        labels_to_filter = {label.strip() for label in self.filter_by.split(',')}

        # Define the filtering logic based on the selected mode

        if self.filter_mode == 'OR':
            # Keep rows where at least one of the filter labels is present
            mask = df[self.curlie_column].apply(
                lambda doc_labels: isinstance(doc_labels, list) and not labels_to_filter.isdisjoint(doc_labels)
            )
        elif self.filter_mode == 'AND':
            # Keep rows where all filter labels are present
            mask = df[self.curlie_column].apply(
                lambda doc_labels: isinstance(doc_labels, list) and labels_to_filter.issubset(doc_labels)
            )
        elif self.filter_mode == 'NOT':
            # Keep rows where none of the filter labels are present
            mask = df[self.curlie_column].apply(
                lambda doc_labels: not isinstance(doc_labels, list) or labels_to_filter.isdisjoint(doc_labels)
            )
        else:
            # Handle invalid filter mode
            # handler.add_error(err.pipeline_invalid_parameter_value(
            #     'filter_mode', self.filter_mode, "Supported values are 'AND', 'OR', 'NOT'"
            # ))
            return data

        # Apply the generated mask to filter the dataframe
        data.documents = df[mask].reset_index(drop=True)
        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": CurlieFilterStep.get_name(),
            "category": "Pre-Processing",
            "description": "Reduces the number of results in the returned result set according to a selected ranking column. Either you choose the pre-selected '_original_ranking_' or enter the wanted ranking coumn name. The columns created by applying a reranker have the form '_reranking_rank_n_', where n is the reranking ID.",
            "parameters": {
                'curlie_column': {
                    'title': 'Curlie Column',
                    'description': 'Column containing the curlie labels',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['curlielabels_en'],
                    'default': 'curlielabels_en',
                },
                'filter_by': {
                    'title': 'Filter by',
                    'description': 'Filtering is done by these labels, separated by comma (, )',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['Arts', 'Science', 'Arts, Science', 'Recreation', 'Health', 'Arts/Movies'],
                    'default': 'Arts',
                },
                'filter_mode': {
                    'title': 'Filter Mode',
                    'description': 'Specify AND, OR, or NOT',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['AND', 'OR', 'NOT'],
                    'default': 'OR',
                },

            }
        }

    @staticmethod
    def get_name() -> str:
        return "Curlie label filter"

