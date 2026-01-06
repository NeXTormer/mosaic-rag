import os
import pandas as pd
import chromadb
from tqdm import tqdm
import uuid
import sys
import numpy as np



PARQUET_FOLDER_PATH = './embedded_eng'
EMBEDDING_COLUMN_NAME = 'embedding'
COLLECTION_NAME = 'curlie_eng'
BATCH_SIZE = 50

chroma_client = chromadb.HttpClient(host='localhost', port=8000)

def validate_dataframe(df: pd.DataFrame) -> bool:
    if EMBEDDING_COLUMN_NAME not in df.columns:
        print(f"Error: Embedding column '{EMBEDDING_COLUMN_NAME}' not found in the DataFrame.", file=sys.stderr)
        return False
    if df[EMBEDDING_COLUMN_NAME].isnull().any():
        print(f"Error: The embedding column '{EMBEDDING_COLUMN_NAME}' contains null values.", file=sys.stderr)
        return False
    return True

def process_parquet_file(filepath: str, collection: chromadb.Collection):
    try:
        df = pd.read_parquet(filepath)
        print(f"\nProcessing file: {os.path.basename(filepath)} ({len(df)} rows)")

        if not validate_dataframe(df):
            print(f"Skipping file {os.path.basename(filepath)} due to validation errors.")
            return

        embeddings = df[EMBEDDING_COLUMN_NAME].tolist()
        metadata_df = df.drop(columns=[EMBEDDING_COLUMN_NAME])

        metadatas = metadata_df.to_dict('records')
        ids = [str(uuid.uuid4()) for _ in range(len(df))]

        # replace valeus that arent handled correctly by chromadb
        sanitized_metadatas = []
        for record in metadatas:
            sanitized_record = {}
            for key, value in record.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    sanitized_record[key] = str(value)

                elif isinstance(value, (str, int, float, bool)):
                    sanitized_record[key] = value

                else:
                    sanitized_record[key] = str(value)
            sanitized_metadatas.append(sanitized_record)

        metadatas = sanitized_metadatas



        # Add data to ChromaDB in batches to not overload the chroma server
        # (some documents are really really huge, so when multiple of them are in one batch it crashes)
        # (might have been better to truncate the documents to a smaller size)
        for i in tqdm(range(0, len(df), BATCH_SIZE), desc="    Ingesting batches"):
            batch_end = min(i + BATCH_SIZE, len(df))

            collection.add(
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end]
            )

    except Exception as e:
        print(f"An error occurred while processing {filepath}: {e}", file=sys.stderr)

def main():
    print("--- Starting Parquet to ChromaDB Ingestion ---")

    if not os.path.isdir(PARQUET_FOLDER_PATH):
        print(f"Error: The specified folder '{PARQUET_FOLDER_PATH}' does not exist.", file=sys.stderr)
        return

    try:
        parquet_files = [f for f in os.listdir(PARQUET_FOLDER_PATH) if f.endswith(('.parquet', '.parq'))]
        if not parquet_files:
            print(f"Warning: No .parquet files found in '{PARQUET_FOLDER_PATH}'.")
            return

        parquet_files.sort()

    except Exception as e:
        print(f"Error reading directory {PARQUET_FOLDER_PATH}: {e}", file=sys.stderr)
        return

    print(f"Found {len(parquet_files)} Parquet file(s) to process.")

    try:
        print(f"Connecting to ChromaDB and ensuring collection '{COLLECTION_NAME}' exists...")
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        print("Successfully connected to ChromaDB.")
    except Exception as e:
        print(f"Error connecting to ChromaDB or getting collection: {e}", file=sys.stderr)
        return

    for filename in tqdm(parquet_files, desc="Processing files", unit="file"):
        filepath = os.path.join(PARQUET_FOLDER_PATH, filename)
        process_parquet_file(filepath, collection)

    print("\n--- Ingestion Complete ---")
    print(f"All files have been processed. Total items in collection '{COLLECTION_NAME}': {collection.count()}")

if __name__ == "__main__":
    main()

