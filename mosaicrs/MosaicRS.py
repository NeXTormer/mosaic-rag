import requests
import json

class MosaicRS:

    SEARCH_PATH = "api/search?q="
    DEFAULT_URL = "https://mosaic.ows.eu/service/"



    def __init__(self, mosaic_url = DEFAULT_URL):
        self.mosaic_url = mosaic_url

    def query_mosaic(self, query):
        response = requests.get(''.join([self.mosaic_url, MosaicRS.SEARCH_PATH, query]))
        json_data = json.loads(response.text)

        return json_data



