from flask import Flask
from flask import request
from flask import Response

from flask_cors import CORS


from mosaicrs.data_source.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"





@app.get('/search')
def search():
    query = request.args.get('q')

    ds = MosaicDataSource()


    response = Response(ds.request_data(PipelineIntermediate(query=query, arguments={'limit': 20})).data.to_json(orient='records'), mimetype='application/json')
    return response



