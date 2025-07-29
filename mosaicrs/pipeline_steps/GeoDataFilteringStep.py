import pandas as pd
from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum

class GeoDataFilteringStep(PipelineStep):

    def __init__(self, latitude_value_p1: str, longitude_value_p1: str, latitude_value_p2: str, longitude_value_p2: str, latitude_column_name: str = "latitude", longitude_column_name: str = "longitude"):
        
        self.invalid_value_names = []
        self.latitude_P1 = self.checkInputValue(latitude_value_p1, "Latitude Point 1")
        self.longitude_P1 = self.checkInputValue(longitude_value_p1, "Longitude Point 1")
        self.latitude_P2 = self.checkInputValue(latitude_value_p2, "Latitude Point 2")
        self.longitude_P2 = self.checkInputValue(longitude_value_p2, "Longitude Point 2")
        
        self.latitude_column_name = latitude_column_name
        self.longitude_column_name = longitude_column_name

    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        if len(self.invalid_value_names) > 0:
            handler.log(f"The following fields have invalid values: {self.invalid_value_names}. The fields should only contain numerical chars seperated by a single '.'. For all invalid fields we take the default value of 0.0.")

        if self.latitude_column_name not in data.documents:
            handler.log(f"The column {self.latitude_column_name} does not exist in the PipelineIntermediate.")

        if self.longitude_column_name not in data.documents:
            handler.log(f"The column {self.longitude_column_name} does not exist in the PipelineIntermediate.")

        indicator_list = []
        value_list = list(zip(data.documents[self.latitude_column_name].fillna("0.0").to_list(), data.documents[self.longitude_column_name].fillna("0.0").to_list()))

        handler.update_progress(0, len(value_list))

        latitude_lower_border = min(self.latitude_P1, self.latitude_P2)
        latitude_upper_border = max(self.latitude_P1, self.latitude_P2)

        longitude_lower_border = min(self.longitude_P1, self.longitude_P2)
        longitude_upper_border = max(self.longitude_P1, self.longitude_P2)

        for value_tuple in tqdm(value_list):
            if handler.should_cancel:
                break

            if latitude_lower_border <= value_tuple[0] and value_tuple[0] <= latitude_upper_border and longitude_lower_border <= value_tuple[1] and value_list[1] <= longitude_upper_border:
                indicator_list.append(1)
            else: 
                indicator_list.append(0)

            handler.increment_progress()

        data.documents = data.documents[[bool(x) for x in indicator_list]]
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)
        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": GeoDataFilteringStep.get_name(),
            "category": "Pre-Processing",
            "description": "Reduces the number of results in the returned result set according to the given geo coordinates. Given the latitude and longitude values of two points a rectangle gets constructed and only those entries are kept in the PipelineIntermediate whose own Latitude and Longitude values are inside this rectangle.",
            "parameters": {
                'latitude_value_p1': {
                    'title': 'Latitude P1',
                    'description': 'The latitude value of the first point in the format xxx.xxx.',
                    'type': 'string',
                    'enforce-limit': False,
                    'default': '',
                },
                'longitude_value_p1': {
                    'title': 'Longitude P1',
                    'description': 'The longitude value of the first point in the format xxx.xxx.',
                    'type': 'string',
                    'enforce-limit': False,
                    'default': '',
                },
                'latitude_value_p2': {
                    'title': 'Latitude P2',
                    'description': 'The latitude value of the second point in the format xxx.xxx.',
                    'type': 'string',
                    'enforce-limit': False,
                    'default': '',
                },
                'longitude_value_p2': {
                    'title': 'Longitude P2',
                    'description': 'The longitude value of the second point in the format xxx.xxx.',
                    'type': 'string',
                    'enforce-limit': False,
                    'default': '',
                },
                'latitude_column_name': {
                    'title': 'Latitude column name',
                    'description': 'Column containing the latitude values of the documents.',
                    'type': 'string',
                    'enforce-limit': False,
                    'supported-values': ['latitude'],
                    'default': 'latitude',
                },
                'longitude_column_name': {
                    'title': 'Longitude column name',
                    'description': 'Column containing the longitude values of the documents.',
                    'type': 'string',
                    'enforce-limit': False,
                    'supported-values': ['longitude'],
                    'default': 'longitude',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return "Geo Data Filtering"
    
    def checkInputValue(self, value_string, value_name):
        if value_string.strip().isdigit():
            return float(value_string.strip())
        else:
            self.invalid_value_names.append(value_name)
            return 0.0
            
        
        
