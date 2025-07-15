# mosaicRAG
ad
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


`documentation still in progress`


## PipelineIntermediate
The PipelineIntermediate object serves as the primary means of communication between pipeline steps. Each step in the pipeline receives a PipelineIntermediate object as input and returns the altered one as output. This object consists of three main components:
| Name | Description |
|--|--|
| Documents | This DataFrame contains the current data as modified by the most recent pipeline step, along with individual ranking scores, ranks, and additional metadata such as IDs and URLs.
| History | The history dictionary stores a copy of the documents DataFrame after each individual pipeline step. This allows for detailed analysis of how each step modifies the retrieved data. |
| Metadata | The `metadata` DataFrame contains information about each column in the `documents` DataFrame that has a specific role or purpose. Columns can have one or more of the following properties: `rank`, `text`, or `chip`. Columns marked with the `rank` property are used for ranking purposes. These columns consist of increasing integers starting from 1, where a value of 1 indicates the most relevant document. Relevance decreases as the rank number increases. Columns with the `rank` property are also displayed in the UI within the ranking dropdown menu. Columns with the `text`property contain text which can be used as an output in the UI. All columns with this property are shown in the text-drop-down field in the UI. In columns with the property `chip` are small bits of information (for example the result of a MetadataAnalysis step) which are then display in chip form in the UI for each individual retrieved result.|


## Categories

| Name | Description  |
|--|--|
| Data Sources | This category encompasses all pipeline steps, which bring new data into the RAG system. The steps itself gather data from external services (e.g. MOSAIC, ChromaDB, etc.), bring them into a unified format and save them in the [PipelineIntermediate](#pipelineintermediate). |
| Summarizers | Pipeline steps of this category are used to summarize the retrieved and/or processed text either on an individual level or to get an overall summarization of all returned results.   |
| Pre-Processing | This category hosts a number of basic NLP pre-processing steps which can be used to enhance/change the retrieved full texts from the sources.  |
| Rerankers | Rerankers are used to alter/enhance the ranking of the retrieved results. These rerankers can be based on simple ISR metrics (eg. Cosine, BM25, etc.) or also encompass LLM-Rag features. |
| Metadata Analysis | This category holds pipeline steps which are used for analysis purposes on each individual row.|


## Pipeline steps

### PipelineStep

This is the abstract base class for all pipeline steps. It must either be directly implemented by each step or be present somewhere in the class’s inheritance hierarchy (e.g., via [`RowProcessorPipelineStep`](#rowprocessorpipelinestep).

It defines the following abstract methods:

- `def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler) -> PipelineIntermediate:`

- `def get_info() -> dict:`

- `def get_name() -> str:`

The `transform` method is the core function of each pipeline step. It applies the specific modifications to the [`PipelineIntermediate`](#pipelineintermediate) object for that step.
The two static methods, `get_info()` and `get_name()`, provide metadata about the step. They are primarily used to supply descriptive information to the frontend.

----------


### RowProcessorPipelineStep

`RowProcessorPipelineStep` implements the [`PipelineStep`](#pipelinestep) interface but serves as a specialized base class meant to be extended by other pipeline steps. It overrides the `transform` method from [`PipelineStep`](#pipelinestep)  and introduces a new abstract method that must be implemented by any subclass deriving from it:

- `def transform_row(self, data, handler: PipelineStepHandler) -> (any, Optional[str]):`

`RowProcessorPipelineStep` provides a framework for iterating over the `PipelineIntermediate` object row by row, applying a transformation—defined in the `transform_row` method—to each string in a selected column.
It handles all responsibilities related to caching, updating the [`PipelineIntermediate`](#pipelineintermediate), and tracking progress. As a result, subclasses implementing `RowProcessorPipelineStep` only need to define the core transformation logic in `transform_row`, without worrying about the surrounding infrastructure.

----------


### MosaicDataSource
- **UI-Name:** `MosaicDataSource`
-   **Category:** [Data Sources](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

The `MosaicDataSource` is a [`PipelineStep`](#pipelinestep) used as the primary source of data, designed to integrate with the existing [MOSAIC tool](https://opencode.it4i.eu/openwebsearcheu-public/mosaic). It retrieves an initial result set of full-text documents from a specified MOSAIC instance. This step is typically used at the beginning of the pipeline.

#### Parameters

-   **`output_column`**  
    The name of the column in the `PipelineIntermediate` where the full texts of the retrieved documents will be stored.
    
-   **`url`**  
    The URL of the MOSAIC instance to query. This must be publicly accessible via the web.
    
-   **`limit`**  
    The number of initial results to retrieve from the MOSAIC instance. If the limit is higher than the number of documents in the respective index, all available documents will be returned. 
    
-   **`search_index`**  
    (Optional) Restrict the search to a specific index within the MOSAIC instance.

----------


### DocumentSummarizerStep
-   **UI-Name:** `LLM Summarizer`
-   **Category:** [Summarizers](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Summarizes each document in the result set using a large language model (LLM). This step allows you to specify which column to summarize (`input_column`) and where to store the results (`output_column`) within the [`PipelineIntermediate`](#pipelineintermediate). Regarding the LLM itself, MosaicRAG provides support for DeepSeekv3, gemma2, qwen2.5, and llama3.1, but it is possible to use any LLM which is accessible through the LiteLLM-Interface (for that additions to the specific files have to be made - documentation regarding this will come in the future). 

#### Parameters

-   **`model`**  
    The LLM instance used for summarization. the following models are currently supported: `DeepSeekv3`,`gemma2`, `qwen2.5`, `llama3.1`.
    
-   **`input_column`**  
    Column name in the `PipelineIntermediate` that contains the input text for summarization.
    
-   **`output_column`**  
    The column where the summarized text will be stored.
    
-   **`summarize_prompt`**  
    Optional instruction (system prompt) provided to the LLM to guide summarization.
    

----------

### ResultsSummarizerStep

-   **UI-Name:** `Query Summarizer`
-   **Category:** [Summarizers](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)

#### Description

Generates a overall summary that condenses the content of all remaining documents in the [`PipelineIntermediate`](#pipelineintermediate) at the time of the ResultSummarizerStep, based on the original search query. The summarized result gets then put into the metadata part of the [`PipelineIntermediate`](#pipelineintermediate) under the name of the `output_column`. For the summarization itself the texts of the `input_column` from the [`PipelineIntermediate`](#pipelineintermediate) are used. Regarding the LLM itself, MosaicRAG provides support for DeepSeekv3, gemma2, qwen2.5, and llama3.1, but it is possible to use any LLM which is accessible through the LiteLLM-Interface (for that additions to the specific files have to be made - documentation regarding this will come in the future).

#### Parameters

-   **`model`**  
    The LLM instance used for summarization. the following models are currently supported: `DeepSeekv3`,`gemma2`, `qwen2.5`, `llama3.1`.
    
-   **`input_column`**  
    Column in the [`PipelineIntermediate`](#pipelineintermediate) containing the text to summarize.
    
-   **`output_column`**  
    Column name in the metadata dataFrame in the [`PipelineIntermediate`](#pipelineintermediate) where the final summary is stored.
    

----------

### ContentExtractorStep
-   **UI-Name:** `Content Extractor`
-   **Category:** [Pre-Processing](#categories)
-   **Implements:** [`RowProcessorPipelineStep`](#rowprocessorpipelinestep)
    

#### Description

Extracts the main content from full-text documents, removing non-essential elements like navigation menus or filler content. Uses a moving average based on sentence length. This step will eventually be deprecated once cleaner indexes are available. It used the text data from the `input_column` and saves the cleaned text data in the `output_column` of the [`PipelineIntermediate`](#pipelineintermediate).

#### Parameters

-   **`input_column`**  
    Column containing the raw text for processing.
    
-   **`output_column`**  
    Column where the cleaned and extracted content will be saved.
    

----------

### StopWordRemovalStep

-   **UI-Name:** `Stopword Remover`
-   **Category:** [Pre-Processing](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Removes stop words from the input text based on the document's language (supports English, German, French, and Italian). The list of supported languages can change in the future. Stop words are sourced from the NLTK corpus. The language codes are based on the iso 639-2 alpha-3 norm.

#### Parameters

-   **`input_column`**  
    The column to clean in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`output_column`**  
    Where the stopword-cleaned text will be stored in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`language_column`**  
    Specifies the language of each document.
    

----------

### PunctuationRemovalStep

-   **UI-Name:** `Punctuation Remover`
-   **Category:** [Pre-Processing](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Removes punctuation from a given text column. First all words get expanded using the contractions python library, afterwards everything gets normalized using the unicodedata python library with the "NFKD" form. Then all remaining punctuation is filtered out and removed using Python’s `string.punctuation` list.

#### Parameters

-   **`input_column`**  
    Text column in the [`PipelineIntermediate`](#pipelineintermediate) to remove the punctuation.
    
-   **`output_column`**  
    Destination column for punctuation-free text in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`process_query`**  
    Boolean (`Yes`/`No`): Whether to also remove punctuation from the search query. Yes -> remove punctuation in the query, No -> do not remove punctuation in the query
    

----------

### TextStemmerStep

-   **UI-Name:** `Text Stemmer`
-   **Category:** [Pre-Processing](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Applies stemming to a text column using the `SnowballStemmer` from NLTK. Language-specific stemmers are used where supported; unsupported languages are left unchanged. Currently the following languages are supported: English, German, French, Italian. The language codes are based on the iso 639-2 alpha-3 norm.

#### Parameters

-   **`input_column`**  
    Column with the input texts in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`output_column`**  
    Column where the stemmed text will be saved in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`language_column`**  
    Contains the language code for each document.
    

----------

### TextLemmatizerStep _(Not currently functional)_

-   **UI-Name:** `Text Lemmatizer`
-   **Category:** [Pre-Processing](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Performs lemmatization on the input text using `WordNetLemmatizer` for English or spaCy models for other supported languages. Unsupported languages remain unchanged. Other supported languages are currently German, French, Italian. The language codes are based on the iso 639-2 alpha-3 norm.

#### Parameters

-   **`input_column`**  
    The column containing the input text in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`output_column`**  
    The column for where the lammatization results will be saved in the [`PipelineIntermediate`](#pipelineintermediate).
    
-   **`language_column`**  
    Column with the language codes.
    

----------

### ReductionStep

-   **UI-Name:** `Result Reduction`
-   **Category:** [Pre-Processing](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Reduces the number of documents in the [`PipelineIntermediate`](#pipelineintermediate) to the top `k` based on a `ranking column`. Either you choose the pre-selected '_original_ranking_' or enter the wanted ranking coumn name. The columns created by applying a reranker have the form '_reranking_rank_n_', where n is the reranking ID.

#### Parameters

-   **`ranking_column`**  
    Column containing the ranking in the [`PipelineIntermediate`](#pipelineintermediate) according to which the selection should happen.
    
-   **`k`**  
    Number of entries to keep.
    

----------

### WordCounterStep

-   **UI-Name:** `Word Counter`
-   **Category:** [Metadata Analysis](#categories)
-   **Implements:** [`RowProcessorPipelineStep`](#rowprocessorpipelinestep)
    

#### Description

Calculates the number of words in each document for a specified `input_column` in the [`PipelineIntermediate`](#pipelineintermediate) and stores ot in the respective `output_column`.

#### Parameters

-   **`input_column`**  
    Column in the [`PipelineIntermediate`](#pipelineintermediate) to analyze for word count.
    
-   **`output_column`**  
    Column to store the resulting word counts in the [`PipelineIntermediate`](#pipelineintermediate).
    

----------

### BasicSentimentAnalysisStep

-   **UI-Name:** `Basic Sentiment Analyser`
-   **Category:** [Metadata Analysis](#categories)
-   **Implements:** [`RowProcessorPipelineStep`](#rowprocessorpipelinestep)
    

#### Description

Uses the Hugging Face model `bhadresh-savani/distilbert-base-uncased-emotion` to return one of six emotions: _sadness, joy, love, anger, fear, surprise_. Works only on English texts and up to 512 tokens. It takes the text data from the `input_column` of the [`PipelineIntermediate`](#pipelineintermediate) and saves the sentiment in the `output_column`.

#### Parameters

-   **`input_column`**  
    Column of the [`PipelineIntermediate`](#pipelineintermediate) containing the input text.
    
-   **`output_column`**  
    Column to store the predicted sentiment for each document in the [`PipelineIntermediate`](#pipelineintermediate).
    

----------

### RelevanceMarkingStep

-   **UI-Name:** `Marking Relevance`
-   **Category:** [Metadata Analysis](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

The step highlights the most important text passages in a given text for a specific query. It does this using a LLM, which finds the most relevant text passages for the query and marks them with two asterisks on each side. The `model` parameter determines, which LLM is used for this step. Currently this step supports gemma2, qwen2.5, and llama3.1. The input text, in which the highlights should be found and marked are in the `input_column` column of the [`PipelineIntermediate`](#pipelineintermediate). The highlighted text is saved in the `output_column` of the [`PipelineIntermediate`](#pipelineintermediate). There is also the possibility to enter an optional new `query` which overwrites the overall query for this exact step.

#### Parameters

-   **`model`**  
    LLM which is used for detecting the most relevant passages in the input text. Currently gemma2, qwen2.5, and llama3.1 are supported. 

-   **`input_column`**  
    Column of the [`PipelineIntermediate`](#pipelineintermediate) containing the input text.
    
-   **`output_column`**  
    Column to store the highlighted text in the [`PipelineIntermediate`](#pipelineintermediate).

-   **`query`**  
    Optional: An additional query, different from the main query, used for the highlighting task.
    

----------

### EmbeddingRerankerStep

-   **UI-Name:** `EmbeddingReranker`
-   **Category:** [Rerankers](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Reranks documents using cosine similarity of dense embeddings generated from an embedding model. Per default the `Snowflake/snowflake-arctic-embed-s` embedding model is used. The text data is taken from the `input_column` of the [`PipelineIntermediate`](#pipelineintermediate) and the generated new ranks are saved in an new `_reranking_rank_n_` column, where `n` is the number of reranking steps already existing. Optionally you can also give a new `query`, which is then used during the reranking process.

#### Parameters

-   **`input_column`**  
    Column to generate embeddings from.
    
-   **`query`**  
    Optional: custom reranking query (defaults to the original query if not provided).
    
-   **`model`**  
    Embedding model used. Supported models:
    
    -   `Snowflake/snowflake-arctic-embed-s`
        
    -   `Snowflake/snowflake-arctic-embed-m`
        

----------

### TFIDFRerankerStep

-   **UI-Name:** `TF-IDF-Reranker`
-   **Category:** [Rerankers](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

Reranks documents using TF-IDF vectors and a configurable similarity metric. Currently MosaicRAG supports the following similarity metrics: Cosine, Euclidean distance, manhatten distance, BM25. The reranker takes the text data from the `input column` of the [`PipelineIntermediate`](#pipelineintermediate) and the generated new ranks are saved in an new `_reranking_rank_n_` column, where `n` is the number of reranking steps already existing. ptionally you can also give a new `query`, which is then used during the reranking process.

#### Parameters

-   **`input_column`**  
    Column to use for TF-IDF vectorization.
    
-   **`query`**  
    Optional: a different reranking query than the original.
    
-   **`similarity_metric`**  
    Metric for computing similarity. Supported values:
    
    -   `cosine-similarity`
        
    -   `euclidean distance`
        
    -   `manhattan distance`
        
    -   `BM25`
        

----------

### TournamentStyleLLMRerankerStep

-   **UI-Name:** `Tournament-Style Reranker Step`
-   **Category:** [Rerankers](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

A LLM-Reranker approach, which does not rerank the whole document set, but can be seen as an ranking-enhancement, as it uses the previously most current ranking and then builds a single elimination tournament tree out of it where the previously 1. document goes against the 2., the winner goes on against the winner from 3. against 4. and so on. This does mean, that a document, once it is eliminated, cannot move any higher in the ranking put it has the advantage, that after the reranking process, the top documents are for sure better then the once behind it. It uses a `model` to determine, which document is more suitable regarding a specific query. This can be either the overall query or a new `query` which is only active for this step. The model gets the texts given in the [`PipelineIntermediate`](#pipelineintermediate) in the column with the name given in `input_column`.

#### Parameters

-   **`model`**  
    LLM model instance to use for the reranking task. Currently gemma2, qwen2.5, and llama3.1 are supported. 

-   **`input_column`**  
    Column of the [`PipelineIntermediate`](#pipelineintermediate) containing the input texts.

-   **`query`**  
    Optional: An additional query, different from the main query, used for reranking.


----------

### GroupStyleLLMRerankerStep

-   **UI-Name:** `Group-Style Reranker Step`
-   **Category:** [Rerankers](#categories)
-   **Implements:** [`PipelineStep`](#pipelinestep)
    

#### Description

A LLM-Reranker approach, where we compare all possible combinations of documents for a specific `window_size` and reward the one document in each set, which is most suitable for a given query, with a point. After evaluating all combinations we rank the documents according to these points. A `window_size` of 2, would result in every document being compared to every other document, which in turn is a full LLM-Reranker. Higher `window_sizes` result in less LLM-comparisons and therefore less computation time, but they are then also less accurate. It uses a `model` to determine, which document is more suitable regarding a specific query. This can be either the overall query or a new `query` which is only active for this step. The model gets the texts given in the [`PipelineIntermediate`](#pipelineintermediate) in the column with the name given in `input_column`.

#### Parameters

-   **`model`**  
    LLM model instance to use for the reranking task. Currently gemma2, qwen2.5, and llama3.1 are supported. 

-   **`input_column`**  
    Column of the [`PipelineIntermediate`](#pipelineintermediate) containing the input texts.

-   **`window-size`**
    A positive integer > 1, indicating the size of the comparison window. 

-   **`query`**  
    Optional: An additional query, different from the main query, used for reranking.


----------

## Tutorial: How to implement your own Pipeline-Step

In this short tutorial we want to show you, how you can implement your own Pipeline-Step, what the structure of a pipeline step is, and what you need to consider. For that we have choosen to re-implement the [`WordCounter`](#wordcounterstep) in two ways, to show you both the [`PipelineStep`](#pipelinestep)-Variation as well as the [`RowProcessorPipelineStep`](#rowprocessorpipelinestep)-Variation of PipelineSteps. But first lets explain the difference between those two pipeline step variations: A [`PipelineStep`](#pipelinestep) is the abstract base class of all other pipeline steps, it defines three methods, that need to be implemented by every other pipeline step: 

- `def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler) -> PipelineIntermediate:`

- `def get_info() -> dict:`

- `def get_name() -> str:`

The `transform` method is the core function of each pipeline step. It applies the specific modifications to the [`PipelineIntermediate`](#pipelineintermediate) object for that step.
The two static methods, `get_info()` and `get_name()`, provide metadata about the step. They are primarily used to supply descriptive information to the frontend. 
The [`RowProcessorPipelineStep`](#rowprocessorpipelinestep) is a pileline step that implements the abstract base class [`PipelineStep`](#pipelinestep), but itself is also a abstract class itself. So in short, [`RowProcessorPipelineStep`](#rowprocessorpipelinestep) is a enhanced base class which implements the [`PipelineStep`](#pipelinestep) class and is meant to be extended by other pipeline steps. It overrides the `transform` method from [`PipelineStep`](#pipelinestep)  and introduces a new abstract method that must be implemented by any subclass deriving from it:

- `def transform_row(self, data, handler: PipelineStepHandler) -> (any, Optional[str]):`

`RowProcessorPipelineStep` provides a framework for iterating over the `PipelineIntermediate` object row by row, applying a transformation—defined in the `transform_row` method—to each string in a selected column.
It handles all responsibilities related to caching, updating the [`PipelineIntermediate`](#pipelineintermediate), and tracking progress. As a result, subclasses implementing `RowProcessorPipelineStep` only need to define the core transformation logic in `transform_row`, without worrying about the surrounding infrastructure. All pipeline steps, implementing [`RowProcessorPipelineStep`](#rowprocessorpipelinestep) still need to implement `def get_info() -> dict:` and `def get_name() -> str:`. 
The default implementation of the [`WordCounter`](#wordcounterstep)-Step is done via a [`RowProcessorPipelineStep`](#rowprocessorpipelinestep), so we will first show how this is done, and then show how it can be done via a standard [`PipelineStep`](#pipelinestep). 

### Variation 1: [`RowProcessorPipelineStep`](#rowprocessorpipelinestep)

```from typing import Optional
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep


class WordCounterStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str):
        super().__init__(input_column, output_column)

    def transform_row(self, data, handler) -> (str, Optional[str]):
        return str(len(str(data).split(' '))), 'chip'

    def get_cache_fingerprint(self) -> str:
        return ''

    @staticmethod
    def get_info() -> dict:
        return {
            "name": WordCounterStep.get_name(),
            "category": "Metadata Analysis",
            "description": "Count the number words, separated by spaces, in the text.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': '',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['wordCount', 'word_count'],
                    'default': 'wordCount',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        return 'Word counter'```