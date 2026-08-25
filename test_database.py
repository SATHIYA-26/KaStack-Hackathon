import os
import unittest
import json
import sqlite3
from database import (
    init_db,
    insert_message,
    get_message_history,
    get_message_by_id,
    get_connection,
    DB_PATH,
)

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_semantic.db")


class TestSQLiteDatabase(unittest.TestCase):

    def setUp(self):
        # Use a temporary test database file for isolated testing
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        init_db(TEST_DB_PATH)

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_schema_and_columns(self):
        """Verify that the messages table has the exact required schema and columns."""
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(messages);")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        expected_columns = {
            "id": "INTEGER",
            "original_message": "TEXT",
            "semantic_packet": "TEXT",
            "decoded_message": "TEXT",
            "original_bytes": "INTEGER",
            "packet_bytes": "INTEGER",
            "compression_percentage": "REAL",
            "encoding_latency_ms": "REAL",
            "decoding_latency_ms": "REAL",
            "processing_mode": "TEXT",
            "validation_result": "TEXT",
            "created_at": "TIMESTAMP",
        }

        for col, col_type in expected_columns.items():
            self.assertIn(col, columns, f"Column '{col}' is missing from messages table.")
            self.assertEqual(
                columns[col].upper(),
                col_type,
                f"Column '{col}' has type {columns[col]}, expected {col_type}.",
            )

    def test_insert_and_retrieve_dict_packet(self):
        """Test inserting a record with a Python dict for semantic_packet."""
        sample_packet = {
            "a": "send",
            "p": "Rahul",
            "o": "reports",
            "q": 5,
            "t": "18:00",
            "n": 1,
        }

        record_id = insert_message(
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
            db_path=TEST_DB_PATH,
        )

        self.assertIsInstance(record_id, int)
        self.assertGreater(record_id, 0)

        record = get_message_by_id(record_id, db_path=TEST_DB_PATH)
        self.assertIsNotNone(record)
        self.assertEqual(record["id"], record_id)
        self.assertEqual(record["original_message"], "Don't send 5 reports to Rahul before 6 PM.")
        self.assertEqual(record["decoded_message"], "Do not send 5 reports to Rahul before 6 PM.")
        self.assertEqual(record["original_bytes"], 48)
        self.assertEqual(record["packet_bytes"], 65)
        self.assertAlmostEqual(record["compression_percentage"], -35.42, places=2)
        self.assertAlmostEqual(record["encoding_latency_ms"], 2.31, places=2)
        self.assertAlmostEqual(record["decoding_latency_ms"], 1.72, places=2)
        self.assertEqual(record["processing_mode"], "normal")
        self.assertEqual(record["validation_result"], "safe")

        # Verify semantic_packet is returned as a Python dict
        self.assertIsInstance(record["semantic_packet"], dict)
        self.assertEqual(record["semantic_packet"], sample_packet)
        self.assertIsNotNone(record["created_at"])

    def test_insert_and_retrieve_json_string_packet(self):
        """Test inserting a record when semantic_packet is already a JSON string."""
        sample_packet = {"intent": "alert", "level": "critical"}
        packet_str = json.dumps(sample_packet)

        record_id = insert_message(
            original_message="Fire alarm triggered in sector 4.",
            semantic_packet=packet_str,
            decoded_message="Fire alarm in sector 4.",
            original_bytes=35,
            packet_bytes=28,
            compression_percentage=20.0,
            encoding_latency_ms=1.85,
            decoding_latency_ms=1.12,
            processing_mode="low_resource",
            validation_result="safe",
            db_path=TEST_DB_PATH,
        )

        record = get_message_by_id(record_id, db_path=TEST_DB_PATH)
        self.assertIsNotNone(record)
        self.assertIsInstance(record["semantic_packet"], dict)
        self.assertEqual(record["semantic_packet"]["intent"], "alert")

    def test_message_history(self):
        """Test retrieving message history with order and limit."""
        for i in range(5):
            insert_message(
                original_message=f"Message {i}",
                semantic_packet={"index": i},
                decoded_message=f"Decoded {i}",
                original_bytes=10 + i,
                packet_bytes=8 + i,
                compression_percentage=15.0,
                encoding_latency_ms=1.5,
                decoding_latency_ms=1.2,
                processing_mode="normal",
                validation_result="safe",
                db_path=TEST_DB_PATH,
            )

        # Retrieve all (descending order by default)
        history = get_message_history(db_path=TEST_DB_PATH)
        self.assertEqual(len(history), 5)
        self.assertEqual(history[0]["original_message"], "Message 4")
        self.assertEqual(history[-1]["original_message"], "Message 0")

        # Test limit
        history_limited = get_message_history(limit=2, db_path=TEST_DB_PATH)
        self.assertEqual(len(history_limited), 2)
        self.assertEqual(history_limited[0]["original_message"], "Message 4")
        self.assertEqual(history_limited[1]["original_message"], "Message 3")

    def test_nonexistent_record(self):
        """Test retrieving a non-existent record ID returns None."""
        record = get_message_by_id(99999, db_path=TEST_DB_PATH)
        self.assertIsNone(record)


if __name__ == "__main__":
    unittest.main()
