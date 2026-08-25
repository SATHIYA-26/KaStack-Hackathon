import sqlite3
import json
import os

DB_PATH = os.path.join("data", "semantic_comm.db")

def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the SQLite database schema if the tables do not exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_message TEXT NOT NULL,
            semantic_packet TEXT NOT NULL,
            decoded_message TEXT,
            original_bytes INTEGER,
            packet_bytes INTEGER,
            compression_percentage REAL,
            encoding_latency_ms REAL,
            decoding_latency_ms REAL,
            processing_mode TEXT,
            validation_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_message(
    original_message: str,
    semantic_packet: dict,
    decoded_message: str = None,
    original_bytes: int = None,
    packet_bytes: int = None,
    compression_percentage: float = None,
    encoding_latency_ms: float = None,
    decoding_latency_ms: float = None,
    processing_mode: str = None,
    validation_result: str = None
) -> int:
    """
    Saves a message transmission record to the database and returns the generated row ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    packet_json = json.dumps(semantic_packet)
    
    cursor.execute("""
        INSERT INTO messages (
            original_message, semantic_packet, decoded_message,
            original_bytes, packet_bytes, compression_percentage,
            encoding_latency_ms, decoding_latency_ms, processing_mode, validation_result
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        original_message, packet_json, decoded_message,
        original_bytes, packet_bytes, compression_percentage,
        encoding_latency_ms, decoding_latency_ms, processing_mode, validation_result
    ))
    
    conn.commit()
    generated_id = cursor.lastrowid
    conn.close()
    return generated_id

def update_message_decoding(semantic_packet: dict, decoded_message: str, decoding_latency_ms: float):
    """
    Updates the most recent message matching the semantic packet with its decoded text and latency.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    packet_json = json.dumps(semantic_packet)
    cursor.execute("""
        UPDATE messages
        SET decoded_message = ?, decoding_latency_ms = ?
        WHERE id = (
            SELECT id FROM messages 
            WHERE semantic_packet = ? 
            ORDER BY id DESC 
            LIMIT 1
        )
    """, (decoded_message, decoding_latency_ms, packet_json))
    conn.commit()
    conn.close()

def update_message_validation(original: str, reconstructed: str, validation_result: str):
    """
    Updates the most recent message matching original and reconstructed text with the validation result.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE messages
        SET validation_result = ?
        WHERE id = (
            SELECT id FROM messages 
            WHERE original_message = ? AND decoded_message = ? 
            ORDER BY id DESC 
            LIMIT 1
        )
    """, (validation_result, original, reconstructed))
    conn.commit()
    conn.close()

def get_history(limit: int = 100):
    """
    Fetches the history of message transmissions from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM messages 
        ORDER BY id DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        record = dict(row)
        try:
            record["semantic_packet"] = json.loads(record["semantic_packet"])
        except Exception:
            pass
        history.append(record)
    return history
