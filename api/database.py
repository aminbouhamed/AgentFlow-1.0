import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class HistoryDB:
    """Simple SQLite database for email processing history"""
    
    def __init__(self, db_path: str = "data/history.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE,
                    email_text TEXT,
                    decision TEXT,
                    confidence REAL,
                    response_subject TEXT,
                    response_body TEXT,
                    processing_time REAL,
                    quality_approved BOOLEAN,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_entry(self, result: Dict) -> bool:
        """Add a new history entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO email_history 
                    (request_id, email_text, decision, confidence, 
                     response_subject, response_body, processing_time, 
                     quality_approved, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.get('request_id'),
                    result.get('email_text', ''),
                    result.get('decision'),
                    result.get('confidence'),
                    result.get('response_subject'),
                    result.get('response_body'),
                    result.get('processing_time'),
                    result.get('quality_approved'),
                    json.dumps(result.get('metadata', {}))
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate request_id
            return False
        except Exception as e:
            print(f"Error adding history entry: {e}")
            return False
    
    def get_all_entries(self, limit: int = 100) -> List[Dict]:
        """Get all history entries (newest first)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM email_history 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            entries = []
            for row in cursor:
                entry = dict(row)
                entry['metadata'] = json.loads(entry['metadata'])
                entries.append(entry)
            
            return entries
    
    def get_entry(self, request_id: str) -> Optional[Dict]:
        """Get a specific entry by request_id"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM email_history 
                WHERE request_id = ?
            """, (request_id,))
            
            row = cursor.fetchone()
            if row:
                entry = dict(row)
                entry['metadata'] = json.loads(entry['metadata'])
                return entry
            return None
    
    def delete_entry(self, request_id: str) -> bool:
        """Delete an entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM email_history 
                    WHERE request_id = ?
                """, (request_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting entry: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM email_history")
                conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(confidence) as avg_confidence,
                    AVG(processing_time) as avg_processing_time,
                    SUM(CASE WHEN quality_approved = 1 THEN 1 ELSE 0 END) as approved_count
                FROM email_history
            """)
            row = cursor.fetchone()
            
            return {
                'total_processed': row[0],
                'avg_confidence': round(row[1] or 0, 2),
                'avg_processing_time': round(row[2] or 0, 2),
                'quality_approval_rate': round((row[3] / row[0] * 100) if row[0] > 0 else 0, 1)
            }