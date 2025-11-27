#!/usr/bin/env python3
"""
SQLite database management for dashboard
Handles validations, parser metadata, and parser errors
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json


class DatabaseManager:
    """Manages SQLite database for operational dashboard"""

    def __init__(self, db_path: str):
        """
        Initialize database connection and create schema

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_schema()

    def _connect(self):
        """Establish database connection with optimizations"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows

        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        # Optimize for dashboard workloads
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=10000")
        self.conn.execute("PRAGMA temp_store=memory")

    def _create_schema(self):
        """Create database tables and indexes if they don't exist"""
        cursor = self.conn.cursor()

        # Create validations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validations (
                job_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds REAL,
                citation_count INTEGER,
                token_usage_prompt INTEGER,
                token_usage_completion INTEGER,
                token_usage_total INTEGER,
                user_type TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                citations_text TEXT
            )
        """)

        # Create parser_metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parser_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Create parser_errors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parser_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                error_message TEXT NOT NULL,
                log_line TEXT
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON validations(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON validations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_type ON validations(user_type)")

        # Add citations_text column to existing tables (migration)
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'citations_text' not in columns:
            cursor.execute("ALTER TABLE validations ADD COLUMN citations_text TEXT")
            print("Added citations_text column to validations table")

        # Create partial index for performance optimization on citations_text
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_citations_text
            ON validations(citations_text)
            WHERE citations_text IS NOT NULL AND length(citations_text) > 0
        """)

        self.conn.commit()

    def get_table_schema(self, table_name: str) -> List[str]:
        """
        Get column definitions for a table

        Args:
            table_name: Name of the table

        Returns:
            List of column definitions
        """
        # Validate table name to prevent SQL injection
        valid_tables = {'validations', 'parser_metadata', 'parser_errors'}
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table name: {table_name}")

        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        schema = []
        for col in columns:
            # Format: column_name TEXT PRIMARY KEY
            col_def = f"{col[1]} {col[2]}"
            if col[5] == 1:  # PRIMARY KEY
                col_def += " PRIMARY KEY"
                # Check if it's AUTOINCREMENT by examining the table SQL
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_sql = cursor.fetchone()
                if table_sql and 'AUTOINCREMENT' in table_sql[0]:
                    col_def += " AUTOINCREMENT"
            if col[3] == 1:  # NOT NULL
                col_def += " NOT NULL"
            if col[4]:  # DEFAULT value
                col_def += f" DEFAULT {col[4]}"

            schema.append(col_def)

        return schema

    def get_indexes(self) -> List[str]:
        """
        Get list of index names in the database

        Returns:
            List of index names
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        return [idx[0] for idx in indexes]

    def insert_validation(self, validation_data: Dict[str, Any]):
        """
        Insert or update a validation record (UPSERT)

        Args:
            validation_data: Dictionary with validation fields
        """
        cursor = self.conn.cursor()

        # Use INSERT OR REPLACE for UPSERT behavior
        cursor.execute("""
            INSERT OR REPLACE INTO validations (
                job_id, created_at, completed_at, duration_seconds,
                citation_count, token_usage_prompt, token_usage_completion,
                token_usage_total, user_type, status, error_message, citations_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            validation_data["job_id"],
            validation_data["created_at"],
            validation_data.get("completed_at"),
            validation_data.get("duration_seconds"),
            validation_data.get("citation_count"),
            validation_data.get("token_usage_prompt"),
            validation_data.get("token_usage_completion"),
            validation_data.get("token_usage_total"),
            validation_data["user_type"],
            validation_data["status"],
            validation_data.get("error_message"),
            validation_data.get("citations_text")
        ))

        self.conn.commit()

    def get_validation(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single validation by job_id

        Args:
            job_id: The job ID to retrieve

        Returns:
            Validation data as dict, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM validations WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_validations(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        user_type: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Get validations with filtering and pagination

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            status: Filter by status (completed, failed, pending)
            user_type: Filter by user_type (free, paid)
            search: Search in job_id field
            from_date: Filter by created_at >= from_date
            to_date: Filter by created_at <= to_date
            order_by: Column to order by
            order_dir: ASC or DESC

        Returns:
            List of validation records
        """
        query = "SELECT * FROM validations WHERE 1=1"
        params = []

        # Add filters
        if status:
            query += " AND status = ?"
            params.append(status)

        if user_type:
            query += " AND user_type = ?"
            params.append(user_type)

        if search:
            query += " AND job_id LIKE ?"
            params.append(f"%{search}%")

        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)

        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        # Add ordering
        query += f" ORDER BY {order_by} {order_dir}"

        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_validations_count(
        self,
        status: Optional[str] = None,
        user_type: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> int:
        """
        Get count of validations matching filters

        Args:
            Same filters as get_validations()

        Returns:
            Total count of matching validations
        """
        query = "SELECT COUNT(*) FROM validations WHERE 1=1"
        params = []

        # Add filters (same as get_validations)
        if status:
            query += " AND status = ?"
            params.append(status)

        if user_type:
            query += " AND user_type = ?"
            params.append(user_type)

        if search:
            query += " AND job_id LIKE ?"
            params.append(f"%{search}%")

        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)

        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()

        return result[0] if result else 0

    def set_metadata(self, key: str, value: str):
        """
        Set parser metadata value

        Args:
            key: Metadata key
            value: Metadata value
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO parser_metadata (key, value)
            VALUES (?, ?)
        """, (key, value))

        self.conn.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """
        Get parser metadata value

        Args:
            key: Metadata key

        Returns:
            Metadata value, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM parser_metadata WHERE key = ?", (key,))
        row = cursor.fetchone()

        return row[0] if row else None

    def insert_parser_error(self, timestamp: str, error_message: str, log_line: str):
        """
        Insert a parser error record

        Args:
            timestamp: Error timestamp
            error_message: Description of error
            log_line: The problematic log line
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO parser_errors (timestamp, error_message, log_line)
            VALUES (?, ?, ?)
        """, (timestamp, error_message, log_line))

        self.conn.commit()

    def get_parser_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent parser errors

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of parser error records
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM parser_errors
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for validations

        Args:
            from_date: Include only validations created after this date
            to_date: Include only validations created before this date

        Returns:
            Dictionary with summary statistics
        """
        query = """
            SELECT
                COUNT(*) as total_validations,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                SUM(citation_count) as total_citations,
                COUNT(CASE WHEN user_type = 'free' THEN 1 END) as free_users,
                COUNT(CASE WHEN user_type = 'paid' THEN 1 END) as paid_users,
                AVG(duration_seconds) as avg_duration_seconds,
                AVG(citation_count) as avg_citations_per_validation
            FROM validations
            WHERE 1=1
        """
        params = []

        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)

        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()

        return {
            "total_validations": result[0] or 0,
            "completed": result[1] or 0,
            "failed": result[2] or 0,
            "pending": result[3] or 0,
            "total_citations": result[4] or 0,
            "free_users": result[5] or 0,
            "paid_users": result[6] or 0,
            "avg_duration_seconds": round(result[7] or 0, 1),
            "avg_citations_per_validation": round(result[8] or 0, 1)
        }

    def delete_old_records(self, days: int = 90) -> int:
        """
        Delete validation records older than specified days

        Args:
            days: Number of days to keep records

        Returns:
            Number of deleted records
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat() + "Z"

        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM validations
            WHERE created_at < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        self.conn.commit()

        return deleted_count

    def vacuum_database(self):
        """Vacuum the database to reclaim space"""
        cursor = self.conn.cursor()
        cursor.execute("VACUUM")
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def explain_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Get execution plan for a query using EXPLAIN QUERY PLAN

        Args:
            query: SQL query to explain
            params: Query parameters

        Returns:
            List of execution plan steps
        """
        explain_query = f"EXPLAIN QUERY PLAN {query}"
        cursor = self.conn.cursor()
        cursor.execute(explain_query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def test_query_performance(self, test_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Test performance of common queries

        Args:
            test_queries: List of queries with parameters

        Returns:
            Performance test results
        """
        results = {
            "queries": [],
            "summary": {}
        }

        for test_case in test_queries:
            query = test_case["query"]
            params = test_case.get("params", ())
            description = test_case.get("description", query)

            # Get execution plan
            plan = self.explain_query(query, params)

            # Measure execution time
            start_time = datetime.now()
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            cursor.fetchall()  # Ensure query completes
            end_time = datetime.now()

            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            query_result = {
                "description": description,
                "query": query,
                "execution_time_ms": execution_time_ms,
                "execution_plan": plan,
                "uses_index": any("USING INDEX" in str(step) for step in plan),
                "table_scan": any("SCAN" in str(step) for step in plan)
            }

            results["queries"].append(query_result)

        # Calculate summary
        total_queries = len(results["queries"])
        queries_using_indexes = sum(1 for q in results["queries"] if q["uses_index"])
        table_scans = sum(1 for q in results["queries"] if q["table_scan"])
        avg_execution_time = sum(q["execution_time_ms"] for q in results["queries"]) / total_queries

        results["summary"] = {
            "total_queries": total_queries,
            "queries_using_indexes": queries_using_indexes,
            "queries_with_table_scans": table_scans,
            "index_usage_percentage": (queries_using_indexes / total_queries) * 100,
            "avg_execution_time_ms": avg_execution_time,
            "performance_good": avg_execution_time < 100 and (queries_using_indexes / total_queries) > 0.8
        }

        return results

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience function for getting database instance
def get_database(db_path: str = None) -> DatabaseManager:
    """
    Get database manager instance with default path

    Args:
        db_path: Custom database path, uses default if None

    Returns:
        DatabaseManager instance
    """
    if db_path is None:
        # Default path in dashboard/data directory
        dashboard_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(dashboard_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "validations.db")

    return DatabaseManager(db_path)