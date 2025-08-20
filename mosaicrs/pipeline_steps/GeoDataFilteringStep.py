import pandas as pd
import mosaicrs.pipeline.PipelineErrorHandling as err

from tqdm import tqdm
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from enum import Enum

class GeoDataFilteringStep(PipelineStep):

    def __init__(self, latitude_value_p1: str, longitude_value_p1: str, latitude_value_p2: str, longitude_value_p2: str, latitude_column_name: str = "latitude", longitude_column_name: str = "longitude"):
        """
            Initialize the filtering step with two coordinate points and optional latitude/longitude column names. A pipeline step that filters documents based on geographic coordinates. Given two latitude/longitude points, this step constructs a bounding rectangle and keeps only the documents whose latitude and longitude values fall within that rectangle.

            latitude_value_p1 (str): Latitude value of the first point.
            longitude_value_p1 (str): Longitude value of the first point.
            latitude_value_p2 (str): Latitude value of the second point.
            longitude_value_p2 (str): Longitude value of the second point.
            latitude_column_name (str): Name of the latitude column in the documents.
            longitude_column_name (str): Name of the longitude column in the documents.
        """

        self.invalid_value_names = []
        self.latitude_P1 = self.checkInputValue(latitude_value_p1, "Latitude Point 1")
        self.longitude_P1 = self.checkInputValue(longitude_value_p1, "Longitude Point 1")
        self.latitude_P2 = self.checkInputValue(latitude_value_p2, "Latitude Point 2")
        self.longitude_P2 = self.checkInputValue(longitude_value_p2, "Longitude Point 2")
        
        self.latitude_column_name = latitude_column_name
        self.longitude_column_name = longitude_column_name


    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step. Apply geographic filtering to the pipeline's documents.
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """
        
        if len(self.invalid_value_names) > 0:
            raise err.PipelineStepError(err.ErrorMessages.InvalidCoordinates, invalid_value_names=", ".join(self.invalid_value_names))

        if self.latitude_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.latitude_column_name)

        if self.longitude_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.longitude_column_name)

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
        """
            Validate and convert an input string to a float. If the value is invalid, append its name to `invalid_value_names` and return 0.0 as a default.

            value_string (str): The input value to check.
            value_name (str): The name of the parameter for error logging.

            Returns a parsed float value, or 0.0 if invalid.
        """

        if value_string.strip().isdigit():
            return float(value_string.strip())
        else:
            self.invalid_value_names.append(value_name)
            return 0.0
            
        
        
