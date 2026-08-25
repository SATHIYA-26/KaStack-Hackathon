import sqlite3
import json
import os
from typing import Any, Dict, List, Optional, Union

DB_NAME = "semantic.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Establish and return a connection to the SQLite database.
    Configures row_factory to sqlite3.Row for dict-like access.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """
    Initialize the SQLite database and create the 'messages' table if it does not exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_message TEXT,
        semantic_packet TEXT,
        decoded_message TEXT,
        original_bytes INTEGER,
        packet_bytes INTEGER,
        compression_percentage REAL,
        encoding_latency_ms REAL,
        decoding_latency_ms REAL,
        processing_mode TEXT,
        validation_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(create_table_sql)
    except sqlite3.Error as e:
        print(f"[Database Error] Failed to initialize database: {e}")
        raise
    finally:
        if conn:
            conn.close()


def insert_message(
    original_message: str,
    semantic_packet: Union[Dict[str, Any], str],
    decoded_message: str,
    original_bytes: int,
    packet_bytes: int,
    compression_percentage: float,
    encoding_latency_ms: float,
    decoding_latency_ms: float,
    processing_mode: str,
    validation_result: str,
    db_path: str = DB_PATH,
) -> int:
    """
    Insert one complete message record into the messages table.

    Args:
        original_message: Original natural-language input text.
        semantic_packet: Semantic packet dict or JSON string.
        decoded_message: Reconstructed natural-language text.
        original_bytes: Byte size of original message.
        packet_bytes: Byte size of semantic packet.
        compression_percentage: Compression ratio percentage.
        encoding_latency_ms: Time taken to encode in milliseconds.
        decoding_latency_ms: Time taken to decode in milliseconds.
        processing_mode: Mode used ('normal', 'low_resource', etc.).
        validation_result: Meaning validation status ('safe', 'review required', 'failed').
        db_path: Path to the SQLite database file.

    Returns:
        int: The auto-generated row ID of the inserted record.
    """
    # Ensure semantic_packet is serialized to JSON string
    if isinstance(semantic_packet, (dict, list)):
        packet_json = json.dumps(semantic_packet, ensure_ascii=False)
    elif isinstance(semantic_packet, str):
        # Validate that string is valid JSON or store formatted string
        try:
            parsed = json.loads(semantic_packet)
            packet_json = json.dumps(parsed, ensure_ascii=False)
        except (ValueError, TypeError):
            packet_json = semantic_packet
    else:
        packet_json = json.dumps(semantic_packet)

    insert_sql = """
    INSERT INTO messages (
        original_message,
        semantic_packet,
        decoded_message,
        original_bytes,
        packet_bytes,
        compression_percentage,
        encoding_latency_ms,
        decoding_latency_ms,
        processing_mode,
        validation_result
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            cursor = conn.execute(
                insert_sql,
                (
                    original_message,
                    packet_json,
                    decoded_message,
                    original_bytes,
                    packet_bytes,
                    compression_percentage,
                    encoding_latency_ms,
                    decoding_latency_ms,
                    processing_mode,
                    validation_result,
                ),
            )
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"[Database Error] Failed to insert message record: {e}")
        raise
    finally:
        if conn:
            conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Helper function to convert a sqlite3.Row object to a dictionary
    and deserialize the semantic_packet JSON string back to a Python dictionary.
    """
    record = dict(row)
    raw_packet = record.get("semantic_packet")
    if raw_packet and isinstance(raw_packet, str):
        try:
            record["semantic_packet"] = json.loads(raw_packet)
        except (ValueError, TypeError):
            # Fallback to raw string if not JSON
            record["semantic_packet"] = raw_packet
    return record


def get_message_history(
    limit: Optional[int] = None,
    order_desc: bool = True,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Retrieve message history from the database.

    Args:
        limit: Optional maximum number of records to return.
        order_desc: If True, returns most recent messages first (ORDER BY id DESC).
        db_path: Path to the SQLite database file.

    Returns:
        List[Dict[str, Any]]: List of message records with parsed semantic_packet dictionaries.
    """
    # Ensure database/table exists
    init_db(db_path)

    order_clause = "ORDER BY id DESC" if order_desc else "ORDER BY id ASC"
    query_sql = f"SELECT * FROM messages {order_clause}"

    params = []
    if limit is not None and limit > 0:
        query_sql += " LIMIT ?"
        params.append(limit)

    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Database Error] Failed to retrieve message history: {e}")
        raise
    finally:
        if conn:
            conn.close()


def get_message_by_id(
    message_id: int,
    db_path: str = DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single message record by its primary key ID.

    Args:
        message_id: The integer ID of the message.
        db_path: Path to the SQLite database file.

    Returns:
        Optional[Dict[str, Any]]: The message record with parsed semantic_packet dict, or None if not found.
    """
    init_db(db_path)

    query_sql = "SELECT * FROM messages WHERE id = ?;"

    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query_sql, (message_id,))
        row = cursor.fetchone()
        if row:
            return _row_to_dict(row)
        return None
    except sqlite3.Error as e:
        print(f"[Database Error] Failed to retrieve message with ID {message_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Initializing SQLite database...")
    init_db()

    print("\nInserting sample test record...")
    sample_packet = {
        "a": "send",
        "p": "Rahul",
        "o": "reports",
        "q": 5,
        "t": "18:00",
        "n": 1,
    }

    inserted_id = insert_message(
        original_message="Don't send 5 reports to Rahul before 6 PM.",
        semantic_packet=sample_packet,
        decoded_message="Do not send 5 reports to Rahul before 6 PM.",
        original_bytes=48,
        packet_bytes=65,
        compression_percentage=-35.42,
        encoding_latency_ms=2.31,
        decoding_latency_ms=1.72,
        processing_mode="normal",
        validation_result="safe",
    )
    print(f"Record successfully inserted with ID: {inserted_id}")

    print("\nRetrieving message by ID...")
    record = get_message_by_id(inserted_id)
    print("Retrieved record:")
    print(json.dumps(record, indent=2, default=str))

    print("\nRetrieving message history (limit 5)...")
    history = get_message_history(limit=5)
    print(f"Total records retrieved: {len(history)}")
    for item in history:
        print(f" - [{item['id']}] Mode: {item['processing_mode']} | Status: {item['validation_result']} | Message: \"{item['original_message']}\"")
