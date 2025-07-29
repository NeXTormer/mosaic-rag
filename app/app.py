import nltk
from flask import Flask
from flask import request
from flask import Response
from flask import send_from_directory, abort
import subprocess
import shutil
import os
import shutil
import logging
from pathlib import Path
from flask import Flask, send_from_directory, abort
import git # GitPython library
import nltk
from flask import Flask
from flask import request
# ... other imports
import git  # GitPython library
import json
import redis
import shortuuid

from flask_cors import CORS
# ... rest of your imports

import json

from flask_cors import CORS
from sentence_transformers import SentenceTransformer

from app.ConversationTask import ConversationTask
from app.PipelineTask import get_pipeline_info, PipelineTask
from mosaicrs.pipeline_steps.ChromaDataSource import ChromaDataSource
from mosaicrs.pipeline_steps.MosaicDataSource import MosaicDataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate

import os
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




# --- Configuration ---
# !!! REPLACE WITH YOUR ACTUAL GIT REPOSITORY URL !!!
GIT_REPO_URL = "https://github.com/NeXTormer/mosaic-rag-frontend.git"
# Directory where the git repo will be cloned locally
LOCAL_REPO_PATH = Path("./frontend")
# Relative path within the repo to the built web files
FLUTTER_WEB_BUILD_DIR = Path("build/web")
# --- End Configuration ---



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Git Fetching Logic ---
def fetch_flutter_web_app(repo_url: str, local_path: Path, web_build_dir: Path) -> Path:
    """
    Clones or pulls the latest code from the Git repository.
    Returns the absolute path to the web root directory (build/web).
    Raises FileNotFoundError if the web root directory is not found after clone/pull.
    """
    web_root_path = local_path / web_build_dir
    repo = None


    try:
        if local_path.exists():
            logging.info(f"Local repository found at {local_path}. Attempting to pull updates...")
            try:
                repo = git.Repo(local_path)
                # Ensure remote 'origin' exists
                if 'origin' not in repo.remotes:
                     logging.warning(f"Remote 'origin' not found in {local_path}. Re-cloning.")
                     shutil.rmtree(local_path) # Remove corrupted/incomplete repo
                     repo = None # Force cloning below
                else:
                    origin = repo.remotes.origin
                    origin.fetch() # Fetch changes from remote without merging
                    # Get the default branch (commonly 'main' or 'master')
                    # This assumes the default branch is the one you want to pull
                    # You might need to adjust this if you use a different branch
                    default_branch = repo.active_branch.name # Or specify directly e.g., 'main'
                    logging.info(f"Pulling changes from origin/{default_branch}...")
                    # Resetting hard to the fetched state of the default branch
                    # This overwrites local changes, which is often desired for build artifacts
                    repo.git.reset('--hard', f'origin/{default_branch}')
                    logging.info("Pull successful.")

            except git.InvalidGitRepositoryError:
                logging.warning(f"Directory {local_path} exists but is not a valid Git repository. Removing and re-cloning.")
                shutil.rmtree(local_path)
                repo = None # Force cloning below
            except git.GitCommandError as e:
                logging.error(f"Git command failed during pull: {e}")
                # Decide if you want to proceed with potentially old code or raise an error
                # For simplicity here, we'll proceed but log the error
            except Exception as e:
                 logging.error(f"An unexpected error occurred during git pull: {e}")
                 # Decide whether to proceed or raise

        if not local_path.exists():
             logging.info(f"Cloning repository from {repo_url} into {local_path}...")
             try:
                 git.Repo.clone_from(repo_url, local_path)
                 repo = git.Repo(local_path) # Open repo after clone
                 logging.info("Clone successful.")
             except git.GitCommandError as e:
                 logging.error(f"Git command failed during clone: {e}")
                 raise ConnectionError(f"Failed to clone repository: {e}") from e
             except Exception as e:
                 logging.error(f"An unexpected error occurred during git clone: {e}")
                 raise ConnectionError(f"Failed to clone repository: {e}") from e

        # --- Verification ---
        if not web_root_path.is_dir():
            logging.error(f"Flutter web build directory not found at expected location: {web_root_path}")
            raise FileNotFoundError(f"Could not find the web root directory at {web_root_path} after git operation.")
        else:
             logging.info(f"Flutter web root found at: {web_root_path.resolve()}")
             return web_root_path.resolve() # Return absolute path

    except Exception as e:
        logging.error(f"Failed to fetch or verify Flutter web app: {e}")
        # Depending on requirements, you might want the app to fail startup
        # or attempt to serve from an old version if web_root_path exists
        if web_root_path.is_dir():
            logging.warning(f"Proceeding with existing local files at {web_root_path} due to fetch error.")
            return web_root_path.resolve()
        else:
            raise RuntimeError(f"Could not fetch Flutter app and no local version found: {e}") from e


# --- Flask Application Setup ---
logging.info("Starting Flask server setup...")


# Fetch the code BEFORE creating the app routes that depend on it
try:
    FLUTTER_WEB_ROOT = fetch_flutter_web_app(GIT_REPO_URL, LOCAL_REPO_PATH, FLUTTER_WEB_BUILD_DIR)
except (FileNotFoundError, ConnectionError, RuntimeError) as e:
     logging.critical(f"FATAL: Could not initialize Flutter web app from Git. Server cannot start. Error: {e}")
     # Exit if fetching fails critically and no local copy is usable
     exit(1) # Or raise an exception that stops the WSGI server if applicable


# ========= END Load Dependencies =========


# ========= Redis Setup =========
# Connect to Redis. Assumes Redis is running on localhost:6379.
# For production, consider using environment variables for connection details.
try:
    redis_host = os.environ.get('REDIS_HOST', 'localhost')

    redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
    # Ping the server to check the connection
    redis_client.ping()
    logging.info("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Could not connect to Redis: {e}. Pipeline save/restore will not work.")
    redis_client = None


app = Flask(__name__)
CORS(app)

task_list: dict[str, PipelineTask] = {}
conversation_list: dict[str, ConversationTask] = {}






# Route to serve index.html from the Flutter web build directory
@app.route('/')
def serve_flutter_index():
    logging.debug(f"Serving index.html from {FLUTTER_WEB_ROOT}")
    try:
        return send_from_directory(FLUTTER_WEB_ROOT, 'index.html')
    except FileNotFoundError:
        logging.error(f"index.html not found in {FLUTTER_WEB_ROOT}")
        abort(404, description="index.html not found.")

# Route to serve any other static file from the Flutter web build directory
# This includes JS, CSS, images, fonts, assets, etc.
@app.route('/<path:filename>')
def serve_flutter_static(filename):
    logging.debug(f"Serving static file '{filename}' from {FLUTTER_WEB_ROOT}")
    try:
        # Check if the requested file actually exists within the web root
        requested_path = (FLUTTER_WEB_ROOT / filename).resolve()
        if not requested_path.is_file() or not requested_path.is_relative_to(FLUTTER_WEB_ROOT):
             logging.warning(f"Attempted access to non-existent or outside-root file: {filename}")
             abort(404) # File not found or security risk

        return send_from_directory(FLUTTER_WEB_ROOT, filename)
    except FileNotFoundError:
        logging.warning(f"Static file not found: {filename}")
        abort(404, description=f"Resource not found: {filename}")
    except Exception as e:
        logging.error(f"Error serving static file {filename}: {e}")
        abort(500)

@app.get('/app_config')
def get_app_config():
    return Response(
        json.dumps(
        {
            "colorTheme": os.environ.get('COLOR_THEME', 'orange-dark'),
            "title":  os.environ.get('APP_TITLE', 'mosaicRAG'),
            "subTitle": os.environ.get('APP_SUBTITLE', ''),
            "pipelineConfigAllowed": os.environ.get('APP_PIPELINE_CONFIG_ALLOWED', True),
            "logsAllowed": os.environ.get('APP_LOGS_ALLOWED', True),
            "pipeline": json.loads(os.environ.get('APP_DEFAULT_PIPELINE', json.dumps({"1": {"id": "mosaic_datasource", "parameters": {"output_column": "full-text",
                                                                                      "url": "https://mosaic.ows.eu/service/api/",
                                                                                      "limit": "20",
                                                                                      "search_index": "simplewiki"}}}))),
            "aboutLinkText": os.environ.get('APP_ABOUT_LINK_TITLE', 'About MOSAIC'),
            "aboutLinkURL": os.environ.get('APP_ABOUT_LINK_URL', 'https://mosaic.ows.eu/'),
        }
    ),
        mimetype='application/json')

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


@app.post('/pipeline/save')
def save_pipeline():
    if not redis_client:
        print("Redis connection not available.")
        return Response("Service Unavailable: Redis connection not available.", status=503)

    pipeline_config = request.get_json()
    print(pipeline_config)
    if not pipeline_config:
        return Response("Bad Request: No JSON payload received.", status=400)

    pipeline_id = shortuuid.uuid()
    redis_key = f"pipeline:{pipeline_id}"

    try:
        redis_client.set(redis_key, json.dumps(pipeline_config))
    except redis.exceptions.RedisError as e:
        return Response("Internal Server Error: Could not save pipeline.", status=500)

    return Response(pipeline_id, mimetype='text/plain', status=201)


@app.get('/pipeline/restore/<string:pipeline_id>')
def restore_pipeline(pipeline_id: str):
    if not redis_client:
        return Response("Service Unavailable: Redis connection not available.", status=503)

    redis_key = f"pipeline:{pipeline_id}"

    try:
        pipeline_config_json = redis_client.get(redis_key)
    except redis.exceptions.RedisError as e:
        return Response("Internal Server Error: Could not retrieve pipeline.", status=500)

    if pipeline_config_json is None:
        return Response(f"Not Found: Pipeline with ID '{pipeline_id}' not found.", status=404)

    logging.info(f"Restored pipeline with ID: {pipeline_id}")
    return Response(pipeline_config_json, mimetype='application/json', status=200)


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
