from flask import Flask
from flask import request

from mosaicrs.data_source.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"





@app.get('/search')
def search():
    query = request.args.get('q')

    ds = MosaicDataSource()

    return ds.request_data(PipelineIntermediate(query=query, arguments={'limit': 20, 'index': 'simplewiki', 'lang': 'eng'})).data.to_json()



