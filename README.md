# mosaicRAG
 
This is mosaicRAG, a retrieval system and retrieval augmented generation library for Mosaic (and other data sources).

#### Links:
- [mosaicRAG](https://mosaicrag.ows.eu)
- [mosaicRAG Repository](https://github.com/nextormer/mosaic-rag)
- [mosaicRAG-frontend Repository](https://github.com/nextormer/mosaic-rag-frontend)

#### Table of contents

- [Building and running](#building-and-running)
- [Features and roadmap](#features)
- [API documentation](#api)
- [Documentation of available pipeline steps](#pipeline-steps)

## Building and running

### Docker image (recommended)

We publish and maintain a docker image for the mosaicRAG service.
This is the recommended way to deploy the service for production use.
MosaicRAG exposes the API (see documentation) and the mosaicRAG Frontend interface.

**For ARM64:**
```shell
docker run -p 80:5000 --name mosaicrag -d git.felixholz.com/mosaicrs:latest
```

**For AMD64:**
```shell
docker run -p 80:5000 --name mosaicrag -d git.felixholz.com/mosaicrs-x64:latest
```

### Local using flask
MosaicRAG uses Flask as the webserver. 
During development, you can run moaicRAG with the following command from the `/app/` directory:

```shell
flask run
```

### Building the docker image

Build the docker image with this command:

```shell
docker build -t mosaicrag:latest
```

## Features:
- build your own retrieval pipeline
  - summarizers, rerankers, preprocessors, metadata analyzers
- (basic) conversational search
- public API
- analyze search data

### Future features:
- Topic modelling
- persistent pipeline 
- improve RAG features
- query enhancement
- explainability
- knowledge graphs


## API

The API supports running tasks synchronously, asynchronously, fetching status of asynchronous tasks, cancelling asynchronous tasks and fetching all available pipeline steps and configuration options.

### Serve Frontend

#### `GET /`
Serves the `index.html` of the Flutter web application.

#### `GET /<path:filename>`
Serves static files (JS, CSS, images, etc.) for the Flutter web application.
- `filename`: The path to the static file.

### Run task synchronously
Starts a RAG task on the server.
Returns response when task is complete, may take several minutes depending on the pipeline configuration.

`POST /task/run`

Parameters in request body as JSON:
- `query` Query string given to the DataSource (i.e. mosaic)
- `parameters` Map of parameters given to the DataSource (e.g. limit=10)
- `1` 1st pipeline step configuration
- `2` 2nd pipeline step configuration
- `n` nth pipeline step configuration

Each pipeline step is defined as follows:
- `id` Class ID for the PipelineStep (e.g. `mosaic_datasource`)
- `parameters` Key-value pairs of the parameters (see PipelineSteps documentation)

Returns a JSON object containing the task status and results upon completion. The structure is the same as the response from `GET /task/progress/<taskID:string>` when `has_finished` is
true.

### Run task asynchronously
Starts a RAG task on the server.
Returns a `taskID`, which is used to cancel or request the status of this task.

`POST /task/enqueue`

Parameters in request body as JSON:
- `query` Query string given to the DataSource
(i.e. mosaic)
- `parameters` Map of parameters given to the DataSource (e.g. limit=10)
- `1` 1st pipeline step configuration
- `2` 2nd pipeline step configuration
- `n` nth pipeline step configuration

Each pipeline step is defined
as follows:
- `id` Class ID for the PipelineStep (e.g. `mosaic_datasource`)
- `parameters` Key-value pairs of the parameters (see PipelineSteps documentation)

Returns:
- `taskID` (text/plain): The ID of the enqueued task.

### Fetch task progress
Request status updates and results for a task given the `taskID` from `POST /task/enqueue`.

`GET /task/progress/<taskID:string>`

- `taskID`: The ID of the task.

Returns task status as JSON:
- `has_finished`:
(boolean) Indicates if the task has completed.
- `progress`: (object) Contains detailed progress information:
  - `current_step`: (string) Name of the current pipeline step being processed.
  - `current_step_index`: (string) The key/identifier of the current step
as defined in the input pipeline (e.g., "1", "2").
  - `pipeline_progress`: (string) Progress formatted as `<steps_initiated_or_processing>/<total_steps>` (e.g., "0/3", "1/3").
  - `pipeline_percentage`: (float) Numeric representation of pipeline progress (0.0 to 1.0), calculated as `steps_initiated_or_processing / total_steps`.
  - `log`: (array of strings) Log messages from the overall pipeline execution and individual steps.
  - `step_output`: (object) A potentially fixed or example output structure related to steps (Note: its current implementation in `PipelineTask.py` shows a static example; dynamic per-step details are typically in `step_progress`).
  - `step_progress`: (object) Contains specific progress updates or log details for each pipeline step, keyed by the step's original identifier (e.g., "mosaic_datasource"). The value for each key is typically an array of strings or structured log entries for that step.
- `result`: (object, present if `has_finished` is true) Contains the final results:
  - `data`: (string) JSON string of the final documents DataFrame.
  - `result_description`: (string) A summary of the task execution (e.g., number of documents, time taken, cache hit ratio).
  - `aggregated_data`: (string) JSON string of aggregated data from the pipeline.
  - `metadata`: (string) JSON string of metadata from the pipeline.

Returns 404 if `taskID` is not found.

### Cancel task

Cancels an asynchronously running task.

`GET /task/cancel/<taskID:string>`

- `taskID`: The ID of the task to cancel.

Returns:
- `Success` (text/plain) if cancellation was initiated.
- `Task id not found` (404)
if the taskID is invalid.

### Chat with RAG results
Provides a conversational interface to interact with the results of a completed pipeline task.

`GET /task/chat/<chatID:string>`

- `chatID`:
    - Use `new` to start a new conversation.
    - Use the `chatID` returned from a previous `new` request to continue an existing conversation.

Query Parameters:
- If `chatID` is `new`:
    - `model`: (string, required) The language model to use for the chat (e.g., gemma2).
    - `column`: (string, required) The column name from the pipeline task's final DataFrame to use as context for the RAG.
    - `task_id`: (string, required) The ID of the completed `PipelineTask` whose results will be used for the conversation.

Returns: A new `chatID` (text/plain) for the created conversation.

- If `chatID` is an existing ID:
    - `message`: (string, required) The user's message/question for the RAG system.

Returns: The model's response (text/plain).

Error Responses:

- 404 Not Found: If `task_id` is not found when `chatID` is `new`.
- 500 Internal Server Error: If an invalid `chatID` is provided for an existing conversation (i.e., chat session not found in server memory).

### Get pipeline info

Fetches information about all available pipeline steps and their configurable parameters.

`GET /pipeline/info`

Returns a JSON object where keys are pipeline step IDs (e.g., `mosaic_datasource`, `llm_summarizer`) and values are objects containing:
- `name`: (string) Display
name of the step.
- `category`: (string) Category of the step (e.g., "Data Sources", "Summarizers").
- `description`: (string) A brief description of what the step does.
- `parameters`: (object) An object detailing the configurable parameters for the step. Each parameter key (e.g., `output_column`, `model`) maps to an object with attributes like:
    - `title`: (string) User-friendly title for the parameter.
    - `description`: (string) Explanation of the parameter.
    - `type`: (string) Input type for the frontend (e.g., `dropdown`, `text`). 
    - `enforce-limit`: (boolean) Whether the frontend should restrict input to `supported-values`.
    - `required`: (boolean) Whether the parameter is mandatory.
    - `supported-values`: (array of strings, optional) Predefined values if `type` is `dropdown`.
    - `default`: Default value for the parameter.


## Pipeline steps
`documentation still in progress`


- PipelineStep
  - Abstract base class for all other steps. It has to be implemented by each class or at least present in the inheritance hierarchy (RowProcessorPipelineStep). Defines the abstract methods:
    - def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler) -> PipelineIntermediate:
    - def get_info() -> dict:
    - def get_name() -> str:
  - The last two methods, “get_info()” and “get_name()” are also static and are mainly present to give the correct description of the respective steps to the frontend.
- RowProcessorPipelineStep
  - RowProcessorPipelineStep implements PipelineStep but elsewise is a special case, where itself is again a class which should be implemented by other steps. The class adapts the “transform” method of the base class PipelineStep and introduces a new method, which every sub-class, which derives from it has to implement:
    - def transform_row(self, data, handler: PipelineStepHandler) -> (any, Optional\[str\]):
  - The RowProcessorPipelineStep implements a way to iterate over the PipelineIntermediate row by row and apply a transformation (“transform_row”) on each of the strings of the selected column. It takes over all the responsibility for caching, PipelineIntermediate updating, and progress tracking, whilst the class which implements RowProcessorPipelineStep only has to do the “main operation” on the string and nothing else.
- MosaicDataSource
  - Name: „MosaicDataSource“
  - Category: „Data Sources“
  - Implements -> PipelineStep
  - Description: The MosaicDataSource is the PipelineStep which is used as the main source of data given the fact that we want to build upon the previous already created MOSAIC-Tool. We use this step to retrieve an initial result set of full texts from a MOSAIC instance.
  - Parameters:
    - output_column: The column in the PipelineIntermediate where the full texts of the retrieved documents are stored.
    - url: The URL of the MOSAIC instance to use. Must be accessible from the public web.
    - limit: The amount of initial results that should be retrieved from MOSAIC.
    - search_index: Limit the search to a specific index.
- DocumentSummarizer
  - Name: „LLM Summarizer“
  - Category: „Summarizers“
  - Implements -> PipelineStep
  - Description: Summarize each document in the result set using a LLM. Specify the input column (which data to summarize) and output column (where to save the summarization in the PipelineIntermediate) of the PipelineIntermediate. This step is used to create summarizations of given input strings.
  - Parameters:
    - model: LLM instance to use for summarization. In the current implementation it can be any T5 transformer or a usage of the DeepSeek API.
    - input_column: Column name of the PipelineIntermediate, which contains the data for summarization.
    - output_column: The column in the PipelineIntermediate where the summarized texts should be stored.
    - summarize_prompt: Additional instruction which you can give the LLM to summarize your text (system prompt).
- ResultSummarizerStep
  - Name: „Query Summarizer“
  - Category: „Summarizers“
  - Implements -> PipelineStep
  - Description: Summarizes the texts of all remaining documents in the PipelineIntermediate into one final summary given the search query defined in the beginning.
  - Parameters:
    - model: LLM instance to use for summarization. In the current implementation it can be any T5 transformer or a usage of the DeepSeek API.
    - input_column: Column name of the PipelineIntermediate, which contains the data for summarization.
    - output_column: The column name in the metadata data-frame in the PipelineIntermediate, where the summarization should be stored.
- ContentExtractorStep
  - Name: „Content Extractor“
  - Category: „Pre-Processing“
  - Implements -> RowProcessorPipelineStep
  - Description: This step is used to extract the main content of a full text and remove any non-important parts like menu-items, unnecessary headers or filler notes. This is based on a moving average approach on the full-text sentence length. This Step will become useless once we get the cleaned indexes with either the useful texts or the main-content with the html-tags so that we can extract the useful information ourselves.
  - Parameters:
    - input_column: Column name in the PipelineIntermediate, which contains the text data for the cleaning.
    - output_column: The column name in the PipelineIntermediate, where the extracted text should be stored.
- StopwordRemovalStep
  - Name: „Stopword Remover“
  - Category: „Pre-Processing“
  - Implements -> PipelineStep
  - Description: Removes stop words from a given text based on the respective language (given by the language column). Currently supported languages English, German, French, Italian. The stop words are retrieved from the nltk corpus.
  - Parameters:
    - input_column: The name of the column in the PipelineIntermediate on which this pre-processing step should be performed.
    - output_column: The name of the column in the PipelineIntermediate where the resulting cleaned texts should be stored.
    - language_column: The name of the column in the PipelineIntermediate which contains the language code for each of the respective retrieved documents.
- PunctuationRemovalStep
  - Name: “Punctuation Remover”
  - Category: “Pre-Processing”
  - Implements -> PipelineStep
  - Description: Removes punctuation from a given text column. Punctuation will be removed based on the string.punctuation list of python.
  - Parameters:
    - input_column: The name of the column in the PipelineIntermediate on which this pre-processing step should be performed.
    - output_column: The name of the column in the PipelineIntermediate where the resulting cleaned texts should be stored.
    - process_query: Boolean query (Yes/No), if the punctuation should also be removed from the query
- TextStemmerStep
  - Name: “Text Stemmer”
  - Category: “Pre-Processing”
  - Implements -> PipelineStep
  - Description: Text-based pre-processing of a given column of text. Stemming will be performed on the selected column, creating a new text consisting of the word stems of the original text. For Stemmers we selected the SnowballStemmer from the nltk library. We create stemmers for all the supported languages, which are used in the retrieved documents. If the language is not supported, we do not change anything in the respective document.
  - Parameters:
    - input_column: The name of the column in the PipelineIntermediate on which this pre-processing step should be performed.
    - output_column: The name of the column in the PipelineIntermediate where the resulting cleaned texts should be stored.
    - language_column: The name of the column in the PipelineIntermediate which contains the language code for each of the respective retrieved documents.
- TextLemmatizationStep (does not work currently)
  - Name: “Text Lemmatizer”
  - Category: “Pre-Processing”
  - Implements -> PipelineStep
  - Description: Text-based pre-processing of a given column of text. Lemmatization will be performed on the selected column, creating a new text consisting of the base form of each word of the original text. For the Lemmatizer we used the WordNetLemmatizer from nltk for all English texts and for all other texts we load respective spacy-lemmatization models. If the language is not supported, we do not change anything in the respective document.
  - Parameters:
    - input_column: The name of the column in the PipelineIntermediate on which this pre-processing step should be performed.
    - output_column: The name of the column in the PipelineIntermediate where the resulting cleaned texts should be stored.
    - language_column: The name of the column in the PipelineIntermediate which contains the language code for each of the respective retrieved documents.
- ReductionStep
  - Name: “Reduction Step”
  - Category: “Filtering”
  - Implements -> Pipelinesteps
  - Description: Reduces the number of entries in the PipelineIntermiediate to only the top-k entries based on a selected ranking column.
  - Parameters:
    - ranking_column: The column name of the column in the PipelineIntermediate, which should be used for the reduction to the top-k entries.
    - k: Number of entries the PipelineIntermediate should be reduced to.
    - reset_index: Boolean question (Yes/No). Should all ranking indexes be reseted to the new number of entries.
- WordCounterStep
  - Name: “Word Counter”
  - Category: “Metadata Analysis”
  - Implements -> RowProcessorPipelineStep
  - Descrption: Returns the number of words for each document for a selected column in the PipelineIntermediate.
  - Parameters:
    - input_column: The column name in the PipelineIntermediate, on which the word count should be calculated for each document.
    - output_column: The column name in the PipelineIntermediate, where the word could for each doucment should be stored.
- BasicSentimentAnalysisStep
  - Name: „Basic Sentiment Analyser“
  - Category: „Metadata Analysis“
  - Implements -> RowProcessorPipelineStep
  - Description: Uses the model „bhadresh-savani/distilbert-base-uncased-emotion“ from hugging face as a pre-trained sentiment analysis model and returns one of six emotions (sadness, joy, love, anger, fear, surprise). This is only a base version which should show that a sentiment analysis is possible. Currently it only works on English texts and up until a maximum word token count of 512.
  - Parameters:
    - input_column: The column name in the PipelineIntermediate, on which the sentiment analysis should be done.
    - output_column: The column name in the PipelineIntermediate, where the retrieved sentiment (emotion) of each document should be stored.
- EmbeddingRerankerStep
  - Name: „Embedding-Reranker“
  - Category: “Rerankers”
  - Implements -> PipelineStep
  - Description: performs reranking based in generated dense embeddings using Cosine-Similarity.
  - Parameters:
    - input_column: The column name in the PipelineIntermediate, on which we generate the document embeddings.
    - query: An additional query, different from the main query, used for reranking. If not provided, the standard query form the beginning will be used.
    - model: The embedding model used to generate the embeddings. We provide the following models: Snowflake/snowflake-arctic-embed-s,Snowflake/snowflake-arctic-embed-m
- TFIDFRerankerStep
  - Name: „TF-IDF-Reranker“
  - Category: “Rerankers”
  - Implements -> PipelineStep
  - Description: Perform reranking based on TF-IDF vectors and a selected similarity metric.
  - Parameters:
    - input_column: The column name in the PipelineIntermediate, on which we generate the TF-IDF-scores.
    - query: An additional query, different from the main query, used for reranking. If not provided, the standard query form the beginning will be used.
    - similarity_metric: The similarity metric used to compute the reranking on the TF-IDF-scores of the query and document. We provide the following metrics: Cosine-similarity, Euclidean distance, Manhatten distance, BM25.