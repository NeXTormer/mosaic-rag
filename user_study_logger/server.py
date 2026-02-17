import sqlite3
import json
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

DB_NAME = "/app/database/study_data.db"


def get_db_connection():
    """Opens a connection to the database."""
    # timeout=20 means: "Try to write for 20 seconds before giving up and throwing an error"
    conn = sqlite3.connect(DB_NAME, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database with the specific schema for your study."""
    conn = get_db_connection()

    # 1. Enable Write-Ahead Logging (WAL) for concurrency safety
    conn.execute('PRAGMA journal_mode=WAL;')

    # 2. Create the single wide table
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS user_study_events
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,

                     -- Common Fields
                     timestamp
                     TEXT,
                     user_id
                     TEXT,
                     pipeline_id
                     TEXT,
                     pipeline_state
                     TEXT,
                     event_type
                     TEXT,

                     -- Search
                     query
                     TEXT,

                     -- Documents & Links
                     document_id
                     TEXT,
                     document_url
                     TEXT,
                     link_url
                     TEXT,

                     -- Chat (mapped from 'documents' and 'chat_message')
                     chat_documents
                     TEXT,
                     chat_message
                     TEXT,

                     -- UI Column Changes
                     previous_text_column
                     TEXT,
                     next_text_column
                     TEXT,
                     previous_rank_column
                     TEXT,
                     next_rank_column
                     TEXT,
                     step_name TEXT
                 )
                 ''')
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_NAME}")


# Initialize DB on startup
init_db()


@app.route('/api/logs', methods=['POST'])
def log_event():
    data = request.json

    # 1. Prepare the data for insertion
    # We use .get() for everything so it returns None (NULL) if the field is missing

    # Handle timestamp: use client's if provided, else server time
    timestamp = data.get('timestamp') or datetime.datetime.now().isoformat()

    # Handle JSON object for pipeline_state (ensure it is stored as string)
    pipeline_state = data.get('pipeline_state')
    if isinstance(pipeline_state, (dict, list)):
        pipeline_state = json.dumps(pipeline_state)

    # 2. Map JSON keys to DB columns
    # (Left = DB Column, Right = JSON Key)
    record = {
        'timestamp': timestamp,
        'user_id': data.get('user_id'),
        'pipeline_id': data.get('pipeline_id'),
        'pipeline_state': pipeline_state,
        'event_type': data.get('event_type'),

        'query': data.get('query'),
        'document_id': data.get('document_id'),
        'document_url': data.get('document_url'),
        'link_url': data.get('link_url'),

        # Map 'documents' from JSON to 'chat_documents' in DB
        'chat_documents': data.get('documents') or data.get('chat_documents'),
        'chat_message': data.get('chat_message'),

        'previous_text_column': data.get('previous_text_column'),
        'next_text_column': data.get('next_text_column'),
        'previous_rank_column': data.get('previous_rank_column'),
        'next_rank_column': data.get('next_rank_column'),
        'step_name': data.get('step_name'),
    }

    try:
        conn = get_db_connection()

        # 3. Dynamic SQL Construction
        columns = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))
        values = list(record.values())

        sql = f'INSERT INTO user_study_events ({columns}) VALUES ({placeholders})'

        conn.execute(sql, values)
        conn.commit()
        conn.close()

        print(f"[{timestamp}] Logged: {record['event_type']}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error logging event: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)