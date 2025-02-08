from flask import Flask
from flask import request
from flask import Response

import json

from flask_cors import CORS

from app.PipelineTask import get_pipeline_info, PipelineTask
from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

app = Flask(__name__)
CORS(app)


task_list: dict[str, PipelineTask] = {}


@app.route("/")
def hello_world():
    return "<h3>MosaicRS</h3>"


@app.get('/search')
def search():
    query = request.args.get('q')

    ds = MosaicDataSource()
    response = Response(
        ds.transform(PipelineIntermediate(query=query, arguments={'limit': 20})).documents.to_json(orient='records'),
        mimetype='application/json')
    return response


@app.post('/pipeline/run')
def pipeline_run():
    return 'Deprecated', 405

    # pipeline = request.get_json()
    #
    # print("Running pipeline with parameters:")
    # print(pipeline)

    # result = run_pipeline_old(pipeline)
    # response = Response(
    #     result.documents.to_json(orient='records'),
    #     mimetype='application/json')
    # return response


@app.get('/pipeline/info')
def pipeline_info():
    response = Response(
        get_pipeline_info(),
        mimetype='application/json')
    return response


@app.post('/task/enqueue')
def pipeline_enqueue():
    pipeline = request.get_json()

    print("Enqueueing pipeline with parameters:")
    print(pipeline)

    task = PipelineTask(pipeline)
    task_id = task.uuid
    task_list[task_id] = task


    task.start()
    response = Response(
        task_id,
        mimetype='text/plain')

    return response


@app.get('/task/progress/<string:task_id>')
def task_progress(task_id: str):
    if task_id not in task_list:
        response = Response('Task id not found', 404)
        return response

    task = task_list[task_id]

    response = Response(
        json.dumps(task.get_status()),
        mimetype='application/json')


    return response

@app.get('/task/cancel/<string:task_id>')
def task_cancel(task_id: str):
    if task_id not in task_list:
        response = Response('Task id not found', 404)
        return response


    task = task_list[task_id]
    task.cancel()

    del task_list[task_id]

    response = Response(
        'Success',
        mimetype='text/plain')
    return response
