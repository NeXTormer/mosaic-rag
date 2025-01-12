from flask import Flask
from flask import request
from flask import Response

from flask_cors import CORS

from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

from app.pipeline_backend import run

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.get('/search')
def search():
    query = request.args.get('q')

    ds = MosaicDataSource()
    response = Response(
        ds.transform(PipelineIntermediate(query=query, arguments={'limit': 20})).data.to_json(orient='records'),
        mimetype='application/json')
    return response


@app.get('/pipeline/run')
def pipeline_run():
    pipeline = request.get_json()

    result = run(pipeline)
    response = Response(
        result.data.to_json(orient='records'),
        mimetype='application/json')
    return response


@app.get('/pipeline/progress/{task_id}')
def pipeline_progress():
    pass


@app.get('/pipeline/result/{task_id}')
def pipeline_result():
    pass
