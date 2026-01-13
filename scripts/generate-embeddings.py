# generate embeddings from OWI
# file by Felix Holz and Gemini 2.5


import os
import pandas as pd
import requests
from multiprocessing import Pool, cpu_count, Manager
import time
from tqdm import tqdm
from transformers import AutoTokenizer
import numpy as np

INPUT_FOLDER = 'soup_eng'
OUTPUT_FOLDER = 'embedded_eng'
OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "jina/jina-embeddings-v2-base-en"

MAX_TOKENS = 8192
CHUNK_SIZE = 8000 # TODO: maybe a smaller chunk size performs better
OVERLAP_PERCENT = 0.3
CHUNK_OVERLAP = int(CHUNK_SIZE * OVERLAP_PERCENT)


tokenizer = None

# might not work with newer version of ollama, the API has been pretty inconsistent in my experieince
def get_embedding(text, ollama_url, model_name):
    try:
        response = requests.post(
            ollama_url,
            json={"model": model_name, "prompt": text},
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return response.json().get("embedding")
    except requests.exceptions.RequestException as e:
        print(f"\nError getting embedding: {e}")
        return None

def process_parquet_file(file_path_tuple):
    input_file_path, output_folder = file_path_tuple
    file_name = os.path.basename(input_file_path)
    output_file_path = os.path.join(output_folder, file_name)

    try:
        df = pd.read_parquet(input_file_path)
        processed_rows = []

        for _, row in df.iterrows():
            if 'plain_text' not in row or not isinstance(row['plain_text'], str):
                continue

            text = row['plain_text']
            tokens = tokenizer.encode(text)

            # If the text is within the limit, process it as a single chunk
            if len(tokens) <= CHUNK_SIZE:
                embedding = get_embedding(text, OLLAMA_URL, OLLAMA_MODEL)
                if embedding:
                    new_row = row.to_dict()
                    new_row['embedding'] = np.array(embedding, dtype=np.float32)
                    new_row['chunk_text'] = text
                    processed_rows.append(new_row)
            else:
                # If the text exceeds the limit, split it into overlapping chunks
                start = 0
                chunk_index = 0
                while start < len(tokens):
                    end = start + CHUNK_SIZE
                    chunk_tokens = tokens[start:end]

                    # Decode the chunk tokens back to text
                    chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)

                    if not chunk_text.strip():
                        start = end - CHUNK_OVERLAP
                        continue

                    embedding = get_embedding(chunk_text, OLLAMA_URL, OLLAMA_MODEL)
                    if embedding:
                        new_row = row.to_dict()
                        # Add a unique ID for the chunk
                        if 'id' in new_row:
                            new_row['id'] = f"{new_row['id']}_{chunk_index}"
                        new_row['embedding'] = np.array(embedding, dtype=np.float32)
                        new_row['chunk_text'] = chunk_text
                        processed_rows.append(new_row)

                    start = end - CHUNK_OVERLAP
                    chunk_index += 1

        if processed_rows:
            new_df = pd.DataFrame(processed_rows)
            new_df.to_parquet(output_file_path, index=False)

        return f"Success: {file_name}"

    except Exception as e:
        print(f"\nAn error occurred while processing {input_file_path}: {e}")
        return f"Error: {file_name} ({e})"


if __name__ == '__main__':
    start_time = time.time()

    print("Initializing tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained('jinaai/jina-embeddings-v2-base-en')
    print("Tokenizer initialized.")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    try:
        files_to_process = [
            os.path.join(INPUT_FOLDER, f)
            for f in os.listdir(INPUT_FOLDER)
            if f.endswith('.parquet')
        ]
    except FileNotFoundError:
        files_to_process = []
        print(f"Error: Input folder '{INPUT_FOLDER}' not found.")

    if not files_to_process:
        print(f"No .parquet files found in '{INPUT_FOLDER}'. Exiting.")
    else:
        tasks = [(file_path, OUTPUT_FOLDER) for file_path in files_to_process]

        num_processes = cpu_count()
        print(f"\nFound {len(files_to_process)} files. Starting processing with {num_processes} workers...")

        with Pool(num_processes) as pool:
            results = list(tqdm(pool.imap_unordered(process_parquet_file, tasks), total=len(tasks)))

        end_time = time.time()
        print("\n--- Processing Complete ---")

        error_count = sum(1 for r in results if r.startswith('Error'))
        if error_count > 0:
            print(f"Completed with {error_count} error(s). Please check the console output above.")

        print(f"Total time taken: {end_time - start_time:.2f} seconds.")
