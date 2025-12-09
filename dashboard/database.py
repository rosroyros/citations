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
                results_gated BOOLEAN,
                results_revealed_at TEXT,
                gated_outcome TEXT,
                paid_user_id TEXT,
                free_user_id TEXT,
                upgrade_state TEXT,
                provider TEXT
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_type ON validations(user_type)")

        # Create user ID indexes only if columns exist (for backward compatibility)
        cursor.execute("PRAGMA table_info(validations)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        if 'paid_user_id' in existing_columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_paid_user_id ON validations(paid_user_id)")

        if 'free_user_id' in existing_columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_free_user_id ON validations(free_user_id)")

        # Create provider index if column exists
        if 'provider' in existing_columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider ON validations(provider)")

        # Check for is_test_job column and add if missing
        if 'is_test_job' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE validations ADD COLUMN is_test_job BOOLEAN DEFAULT FALSE")
                self.conn.commit()
            except sqlite3.OperationalError:
                # Column might have been added concurrently
                pass

        # Handle status vs validation_status compatibility
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'status' in columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON validations(status)")
        if 'validation_status' in columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_status ON validations(validation_status)")

  
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
        Handles both status and validation_status columns for backward compatibility
        
        Uses UPDATE for existing records to support partial updates (e.g. from incremental logs)
        Uses INSERT for new records

        Args:
            validation_data: Dictionary with validation fields
        """
        cursor = self.conn.cursor()
        job_id = validation_data.get("job_id")
        
        if not job_id:
            return

        # Check what columns exist in the database
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        has_status = 'status' in columns
        has_validation_status = 'validation_status' in columns
        has_gating_columns = all(col in columns for col in ['results_gated', 'results_revealed_at', 'gated_outcome'])
        has_upgrade_state = 'upgrade_state' in columns

        # Check if record exists
        cursor.execute("SELECT 1 FROM validations WHERE job_id = ?", (job_id,))
        exists = cursor.fetchone()

        if exists:
            # UPDATE strategy: Only update fields that are present and not None in validation_data
            # This allows partial updates (like upgrade_state) without wiping other fields
            update_clauses = []
            update_params = []

            # Simple fields mapping
            simple_fields = [
                'created_at', 'completed_at', 'duration_seconds', 'citation_count',
                'token_usage_prompt', 'token_usage_completion', 'token_usage_total',
                'user_type', 'error_message', 'paid_user_id', 'free_user_id',
                'results_gated', 'results_revealed_at', 'gated_outcome', 'upgrade_state',
                'provider', 'is_test_job'
            ]
            
            for field in simple_fields:
                if field in columns and field in validation_data and validation_data[field] is not None:
                    update_clauses.append(f"{field} = ?")
                    update_params.append(validation_data[field])

            # Status fields handling
            status_val = validation_data.get("status")
            if status_val is not None:
                if has_status:
                    update_clauses.append("status = ?")
                    update_params.append(status_val)
                if has_validation_status:
                    update_clauses.append("validation_status = ?")
                    update_params.append(status_val)
            
            if update_clauses:
                query = f"UPDATE validations SET {', '.join(update_clauses)} WHERE job_id = ?"
                update_params.append(job_id)
                cursor.execute(query, update_params)
                self.conn.commit()

        else:
            # INSERT strategy for new records
            # Build dynamic column and value lists
            base_columns = ['job_id', 'created_at', 'user_type', 'error_message']
            optional_columns = ['completed_at', 'duration_seconds', 'citation_count',
                              'token_usage_prompt', 'token_usage_completion', 'token_usage_total']
    
            # Add user ID columns if they exist
            if all(col in columns for col in ['paid_user_id', 'free_user_id']):
                optional_columns.extend(['paid_user_id', 'free_user_id'])
    
            # Determine which status column to use
            if has_status and has_validation_status:
                status_columns = ['status', 'validation_status']
            elif has_status:
                status_columns = ['status']
            else:
                status_columns = ['validation_status']
    
            # Add gating columns if they exist
            if has_gating_columns:
                optional_columns.extend(['results_gated', 'results_revealed_at', 'gated_outcome'])
    
            # Add upgrade_state column if it exists
            if has_upgrade_state:
                optional_columns.append('upgrade_state')

            # Add provider column if it exists
            if 'provider' in columns:
                optional_columns.append('provider')

            # Add is_test_job column if it exists
            if 'is_test_job' in columns:
                optional_columns.append('is_test_job')

            # Build final column list and values
            insert_columns = base_columns + status_columns
            for col in optional_columns:
                if col in columns:
                    insert_columns.append(col)
    
            # Build values tuple
            values = []
            for col in insert_columns:
                if col == 'job_id':
                    values.append(validation_data["job_id"])
                elif col == 'created_at':
                    values.append(validation_data["created_at"])
                elif col == 'user_type':
                    values.append(validation_data["user_type"])
                elif col == 'error_message':
                    values.append(validation_data.get("error_message"))
                elif col in ['status', 'validation_status']:
                    values.append(validation_data["status"])  # Map to both if present
                elif col in ['completed_at', 'duration_seconds', 'citation_count',
                            'token_usage_prompt', 'token_usage_completion', 'token_usage_total',
                            'results_gated', 'results_revealed_at', 'gated_outcome',
                            'paid_user_id', 'free_user_id', 'upgrade_state', 'provider', 'is_test_job']:
                    values.append(validation_data.get(col))
    
            # Build the INSERT statement dynamically
            placeholders = ', '.join(['?'] * len(insert_columns))
            column_list = ', '.join(insert_columns)
    
            cursor.execute(f"""
                INSERT OR REPLACE INTO validations ({column_list})
                VALUES ({placeholders})
            """, values)
    
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
            row_dict = dict(row)
            # Always provide 'status' in the result, map from validation_status if needed
            if 'status' not in row_dict and 'validation_status' in row_dict:
                row_dict['status'] = row_dict['validation_status']
            return row_dict
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
        paid_user_id: Optional[str] = None,
        free_user_id: Optional[str] = None,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Get validations with filtering and pagination
        Handles both status and validation_status columns

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            status: Filter by status (completed, failed, pending)
            user_type: Filter by user_type (free, paid)
            search: Search in job_id field
            from_date: Filter by created_at >= from_date
            to_date: Filter by created_at <= to_date
            paid_user_id: Filter by paid_user_id
            free_user_id: Filter by free_user_id
            order_by: Column to order by
            order_dir: ASC or DESC

        Returns:
            List of validation records
        """
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        query = "SELECT * FROM validations WHERE 1=1"
        params = []

        # Handle status filtering - check which column exists
        if status:
            has_status = 'status' in columns
            has_validation_status = 'validation_status' in columns

            if has_status and has_validation_status:
                query += " AND (status = ? OR validation_status = ?)"
                params.extend([status, status])
            elif has_status:
                query += " AND status = ?"
                params.append(status)
            elif has_validation_status:
                query += " AND validation_status = ?"
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

        # Add user ID filtering if columns exist
        if 'paid_user_id' in columns and paid_user_id:
            query += " AND paid_user_id = ?"
            params.append(paid_user_id)

        if 'free_user_id' in columns and free_user_id:
            query += " AND free_user_id = ?"
            params.append(free_user_id)

        # Add ordering
        query += f" ORDER BY {order_by} {order_dir}"

        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Normalize status column in results
        results = []
        for row in rows:
            row_dict = dict(row)
            # Always provide 'status' in the result, map from validation_status if needed
            if 'status' not in row_dict and 'validation_status' in row_dict:
                row_dict['status'] = row_dict['validation_status']
            results.append(row_dict)

        return results

    def get_validations_count(
        self,
        status: Optional[str] = None,
        user_type: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        paid_user_id: Optional[str] = None,
        free_user_id: Optional[str] = None
    ) -> int:
        """
        Get count of validations matching filters
        Handles both status and validation_status columns

        Args:
            Same filters as get_validations()

        Returns:
            Total count of matching validations
        """
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        query = "SELECT COUNT(*) FROM validations WHERE 1=1"
        params = []

        # Add filters (same as get_validations)
        if status:
            has_status = 'status' in columns
            has_validation_status = 'validation_status' in columns

            if has_status and has_validation_status:
                query += " AND (status = ? OR validation_status = ?)"
                params.extend([status, status])
            elif has_status:
                query += " AND status = ?"
                params.append(status)
            elif has_validation_status:
                query += " AND validation_status = ?"
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

        # Add user ID filtering if columns exist
        if 'paid_user_id' in columns and paid_user_id:
            query += " AND paid_user_id = ?"
            params.append(paid_user_id)

        if 'free_user_id' in columns and free_user_id:
            query += " AND free_user_id = ?"
            params.append(free_user_id)

        cursor.execute(query, params)
        result = cursor.fetchone()

        return result[0] if result else 0

    def get_user_journey(
        self,
        paid_user_id: Optional[str] = None,
        free_user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get validation journey for a specific user
        Supports both paid and free user IDs

        Args:
            paid_user_id: Paid user ID to filter by
            free_user_id: Free user ID to filter by
            limit: Maximum number of validations to return

        Returns:
            List of validation records for the user, ordered chronologically
        """
        if not paid_user_id and not free_user_id:
            return []

        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        query = "SELECT * FROM validations WHERE 1=1"
        params = []

        # Add user ID filtering if columns exist
        if 'paid_user_id' in columns and paid_user_id:
            query += " AND paid_user_id = ?"
            params.append(paid_user_id)

        if 'free_user_id' in columns and free_user_id:
            query += " AND free_user_id = ?"
            params.append(free_user_id)

        # Order chronologically to show journey
        query += " ORDER BY created_at ASC"
        query += " LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_user_analytics(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user analytics and behavior patterns
        Returns data about distinct users and their validation patterns

        Args:
            from_date: Include only validations created after this date
            to_date: Include only validations created before this date

        Returns:
            Dictionary with user analytics data
        """
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        # Check if user ID columns exist
        has_paid_user_id = 'paid_user_id' in columns
        has_free_user_id = 'free_user_id' in columns

        if not has_paid_user_id and not has_free_user_id:
            # Return basic analytics if user ID columns don't exist
            return self.get_stats(from_date, to_date)

        query = """
            SELECT
                COUNT(*) as total_validations,
                COUNT(DISTINCT CASE WHEN paid_user_id IS NOT NULL THEN paid_user_id END) as distinct_paid_users,
                COUNT(DISTINCT CASE WHEN free_user_id IS NOT NULL THEN free_user_id END) as distinct_free_users
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

        cursor.execute(query, params)
        basic_stats = cursor.fetchone()

        # Get repeat user statistics
        analytics = {
            "total_validations": basic_stats[0] or 0,
            "distinct_paid_users": basic_stats[1] or 0,
            "distinct_free_users": basic_stats[2] or 0,
            "repeat_users": {},
            "power_users": {}
        }

        # Get repeat user statistics for free users
        if has_free_user_id:
            repeat_query = """
                SELECT COUNT(*) as repeat_free_users
                FROM (
                    SELECT free_user_id, COUNT(*) as validation_count
                    FROM validations
                    WHERE free_user_id IS NOT NULL
            """
            query_params = []

            if from_date:
                repeat_query += " AND created_at >= ?"
                query_params.append(from_date)
            if to_date:
                repeat_query += " AND created_at <= ?"
                query_params.append(to_date)

            repeat_query += """
                    GROUP BY free_user_id
                    HAVING COUNT(*) > 1
                )
            """

            cursor.execute(repeat_query, query_params)
            repeat_result = cursor.fetchone()
            analytics["repeat_users"]["free"] = repeat_result[0] if repeat_result else 0

        # Get repeat user statistics for paid users
        if has_paid_user_id:
            repeat_query = """
                SELECT COUNT(*) as repeat_paid_users
                FROM (
                    SELECT paid_user_id, COUNT(*) as validation_count
                    FROM validations
                    WHERE paid_user_id IS NOT NULL
            """
            query_params = []

            if from_date:
                repeat_query += " AND created_at >= ?"
                query_params.append(from_date)
            if to_date:
                repeat_query += " AND created_at <= ?"
                query_params.append(to_date)

            repeat_query += """
                    GROUP BY paid_user_id
                    HAVING COUNT(*) > 1
                )
            """

            cursor.execute(repeat_query, query_params)
            repeat_result = cursor.fetchone()
            analytics["repeat_users"]["paid"] = repeat_result[0] if repeat_result else 0

        return analytics

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

    def insert_citation_to_dashboard(self, citation_data: Dict[str, Any]):
        """
        Insert a citation record into the citations_dashboard table

        Args:
            citation_data: Dictionary with citation fields including:
                - job_id: Job identifier
                - citation_text: The citation content
                - citation_type: Type of citation (optional)
                - user_type: User type (optional)
                - processing_time_ms: Processing time in milliseconds (optional)
        """
        cursor = self.conn.cursor()

        # Check if citations_dashboard table exists, create if it doesn't
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citations_dashboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                citation_text TEXT NOT NULL,
                citation_type TEXT,
                validation_status TEXT,
                error_details TEXT,
                processing_time_ms REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_type TEXT,
                gating_applied INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            INSERT INTO citations_dashboard (
                job_id, citation_text, citation_type, user_type,
                processing_time_ms, validation_status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            citation_data.get('job_id'),
            citation_data.get('citation_text'),
            citation_data.get('citation_type'),
            citation_data.get('user_type'),
            citation_data.get('processing_time_ms'),
            citation_data.get('validation_status', 'processed')
        ))

        self.conn.commit()

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
        Handles both status and validation_status columns

        Args:
            from_date: Include only validations created after this date
            to_date: Include only validations created before this date

        Returns:
            Dictionary with summary statistics
        """
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        has_status = 'status' in columns
        has_validation_status = 'validation_status' in columns

        if has_status and has_validation_status:
            # Both columns exist, use COALESCE to prioritize status but fallback to validation_status
            status_condition = "COALESCE(status, validation_status)"
        elif has_status:
            status_condition = "status"
        else:
            status_condition = "validation_status"

        query = f"""
            SELECT
                COUNT(*) as total_validations,
                COUNT(CASE WHEN {status_condition} = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN {status_condition} = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN {status_condition} = 'pending' THEN 1 END) as pending,
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