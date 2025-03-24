import nltk
from flask import Flask
from flask import request
from flask import Response

import json

from flask_cors import CORS

from app.ConversationTask import ConversationTask
from app.PipelineTask import get_pipeline_info, PipelineTask
from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

import ssl



# =========== Load Dependencies ===========
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download("stopwords")
nltk.download('punkt_tab')
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")
nltk.download("wordnet")
nltk.download('averaged_perceptron_tagger_eng')
#Install spacy lemmatization models with python -m spacy download fr_core_news_sm

# ========= END Load Dependencies =========

app = Flask(__name__)
CORS(app)


task_list: dict[str, PipelineTask] = {}
conversation_list: dict[str, ConversationTask] = {}


@app.route("/")
def hello_world():
    return "<h3>MosaicRS</h3>\n<a href='mosaicrs.felixholz.com'></a>"



@app.get('/task/chat/<string:chat_id>')
def task_chat(chat_id: str):

    print(request.args)

    model = request.args.get('model')
    column = request.args.get('column')

    task_id = request.args.get('task_id')

    if task_id not in task_list:
        return Response("Task ID not found", status=404)

    pipeline_task = task_list[task_id]

    if chat_id == 'new':
        conversation_task = ConversationTask(model, column, pipeline_task)
        conversation_list[conversation_task.uuid] = conversation_task

        return Response(
            conversation_task.uuid,
            mimetype='text/plain')

    else:
        conversation_task = conversation_list[chat_id]
        user_message = request.args.get('message')

        print('received message:', user_message)

        model_response = conversation_task.add_request(user_message)

        return Response(
            model_response,
            mimetype='text/plain'
        )








@app.post('/task/run')
def task_run():
    pipeline = request.get_json()

    task = PipelineTask(pipeline)
    task_id = task.uuid
    task_list[task_id] = task

    print('run task with id {}'.format(task_id))

    task.start()
    task.join()

    response = Response(
        json.dumps(task.get_status()),
        mimetype='application/json')

    return response

@app.get('/pipeline/info')
def pipeline_info():
    response = Response(
        get_pipeline_info(),
        mimetype='application/json')
    return response


@app.post('/task/enqueue')
def pipeline_enqueue():
    pipeline = request.get_json()

    task = PipelineTask(pipeline)
    task_id = task.uuid
    task_list[task_id] = task

    print('queued task with id {}'.format(task_id))


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

    #TODO: add cancelled flag to task
    # del task_list[task_id]

    response = Response(
        'Success',
        mimetype='text/plain')
    return response
