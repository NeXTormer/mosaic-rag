import pandas as pd
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep


class CurlieFilterStep(PipelineStep):

    def __init__(self, curlie_column: str = "curlielabels_en", filter_by: str = '', filter_mode: str = 'OR'):
        self.curlie_column = curlie_column
        self.filter_by = filter_by
        self.filter_mode = filter_mode

    def transform(self, data: PipelineIntermediate,
                  handler: PipelineStepHandler = PipelineStepHandler()) -> PipelineIntermediate:
        documents = data.documents

        if self.curlie_column not in documents.columns:
            raise KeyError(f"Column '{self.curlie_column}' not found in the DataFrame.")

        if not self.filter_by or not self.filter_by.strip():
            return data

        labels_to_filter = {label.strip() for label in self.filter_by.split(',')}

        def has_any_label(doc_labels: list) -> bool:


            for required_label in labels_to_filter:
                if required_label in doc_labels:
                    return True

            return False

        def has_all_labels(doc_labels: list) -> bool:


            for required_label in labels_to_filter:
                if required_label not in doc_labels:
                    return False

            return True

        def has_any_of_the_labels(doc_labels: list) -> bool:
            for forbidden_label in labels_to_filter:
                if forbidden_label in doc_labels:
                    return False

            return True

        filter_logics = {
            'OR': has_any_label,
            'AND': has_all_labels,
            'NOT': has_any_of_the_labels,
        }

        if self.filter_mode not in filter_logics:
            supported_modes = ", ".join(filter_logics.keys())
            raise ValueError(f"Invalid filter_mode '{self.filter_mode}'. Supported modes are: {supported_modes}.")

        selected_logic = filter_logics[self.filter_mode]
        mask = documents[self.curlie_column].apply(selected_logic)

        print(mask)

        data.documents = documents[mask].reset_index(drop=True)
        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": CurlieFilterStep.get_name(),
            "category": "Pre-Processing",
            "description": "Filters documents based on the presence (OR, AND) or absence (NOT) of specific labels in the selected Curlie column. Labels should be provided as a comma-separated string.",
            "parameters": {
                'curlie_column': {
                    'title': 'Curlie Column',
                    'description': 'Column containing the curlie labels.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['curlielabels_en'],
                    'default': 'curlielabels_en',
                },
                'filter_by': {
                    'title': 'Filter by Labels',
                    'description': 'A comma-separated list of labels to filter by.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['Arts', 'Science', 'Arts, Science', 'Recreation', 'Health', 'Arts/Movies'],
                    'default': 'Arts',
                },
                'filter_mode': {
                    'title': 'Filter Mode',
                    'description': 'The logical mode for filtering: AND (all labels must be present), OR (any label must be present), or NOT (no labels can be present).',
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