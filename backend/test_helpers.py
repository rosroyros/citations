"""
Test helper endpoints for E2E testing
These endpoints are only available when TESTING=true
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import sqlite3
import sys
import logging
from datetime import datetime, timedelta

# Import database path helper
from database import get_validations_db_path

# Import dashboard components
# Note: sys.path should be configured by app.py to include project root
try:
    from dashboard.log_parser import parse_logs
    from dashboard.database import DatabaseManager
except ImportError:
    # Fallback for when running tests in isolation without app.py setup
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from dashboard.log_parser import parse_logs
    from dashboard.database import DatabaseManager

logger = logging.getLogger("citation_validator.tests")

# Request models
class GrantCreditsRequest(BaseModel):
    user_id: str
    amount: int

class GrantPassRequest(BaseModel):
    user_id: str
    days: int = 7

class SetDailyUsageRequest(BaseModel):
    user_id: str
    usage: int

class ClearEventsRequest(BaseModel):
    user_id: str

def get_test_db():
    """Get database connection for testing"""
    db_path = os.path.join(os.path.dirname(__file__), 'credits.db')
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn

def register_test_helpers(app):
    """Register all test helper endpoints with the FastAPI app"""

    @app.post("/test/grant-credits")
    async def test_grant_credits(request: GrantCreditsRequest):
        """Grant credits to a user for testing"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()

        # Create user if not exists
        conn.execute(
            "INSERT OR IGNORE INTO users (token, credits) VALUES (?, ?)",
            (request.user_id, 0)
        )

        # Add credits
        conn.execute(
            "UPDATE users SET credits = credits + ? WHERE token = ?",
            (request.amount, request.user_id)
        )

        conn.commit()
        conn.close()
        return {"success": True}

    @app.post("/test/grant-pass")
    async def test_grant_pass(request: GrantPassRequest):
        """Grant a pass to a user for testing"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()
        
        # Calculate expiration
        import time
        now = int(time.time())
        expiration = now + (request.days * 86400)
        
        # We need an order_id for the schema constraint
        order_id = f"test_grant_{int(time.time())}_{request.user_id[:8]}"
        
        conn.execute(
            """
            INSERT OR REPLACE INTO user_passes 
            (token, expiration_timestamp, pass_type, purchase_date, order_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (request.user_id, expiration, f"{request.days}day", now, order_id)
        )

        conn.commit()
        
        # Force WAL checkpoint to ensure write is visible to other connections
        # This is critical for E2E tests where frontend immediately queries for pass
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        conn.close()
        return {"success": True}

    @app.post("/test/set-daily-usage")
    async def test_set_daily_usage(request: SetDailyUsageRequest):
        """Set daily usage for a user for testing"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()

        # Calculate today's reset timestamp (next UTC midnight)
        from pricing_config import get_next_utc_midnight
        reset_timestamp = get_next_utc_midnight()

        # Insert or update daily usage record
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_usage
            (token, reset_timestamp, citations_count)
            VALUES (?, ?, ?)
            """,
            (request.user_id, reset_timestamp, request.usage)
        )

        conn.commit()
        
        # Force WAL checkpoint to ensure write is visible to other connections
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        conn.close()
        return {"success": True}

    @app.get("/test/get-user")
    async def test_get_user(user_id: str):
        """Get user data for testing"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()

        # Get user info from users table
        user = conn.execute(
            "SELECT * FROM users WHERE token = ?",
            (user_id,)
        ).fetchone()

        user_data = dict(user) if user else {"token": user_id, "credits": 0}

        # Get daily usage from daily_usage table
        from pricing_config import get_next_utc_midnight
        reset_timestamp = get_next_utc_midnight()

        daily_usage = conn.execute(
            "SELECT citations_count FROM daily_usage WHERE token = ? AND reset_timestamp = ?",
            (user_id, reset_timestamp)
        ).fetchone()

        user_data["daily_usage"] = daily_usage["citations_count"] if daily_usage else 0

        # Get pass info from user_passes table
        import time
        now = int(time.time())
        user_pass = conn.execute(
            "SELECT * FROM user_passes WHERE token = ? AND expiration_timestamp > ?",
            (user_id, now)
        ).fetchone()

        user_data["has_pass"] = user_pass is not None
        if user_pass:
            user_data["pass_expires"] = user_pass["expiration_timestamp"]

        conn.close()

        return user_data

    @app.get("/test/get-validation")
    async def test_get_validation(job_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Get validation record for testing, forcing log parse first.
        Used to verify upgrade flow events and other metadata.
        Supports lookup by job_id or user_id (latest job).
        """
        if os.getenv('TESTING') != 'true':
             raise HTTPException(status_code=404, detail="Not found")
        
        if not job_id and not user_id:
            raise HTTPException(status_code=400, detail="Either job_id or user_id is required")
        
        # 1. Force parse logs (stateless full parse to ensure latest events are picked up)
        log_path = os.getenv('APP_LOG_PATH', '/opt/citations/logs/app.log')
        if os.path.exists(log_path):
            try:
                # Parse logs
                parsed_jobs = parse_logs(log_path)
                
                # 2. Sync to DB (validations_test.db if in test mode)
                db_path = get_validations_db_path()
                # Ensure db directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                with DatabaseManager(db_path) as db:
                    for job in parsed_jobs:
                        db.insert_validation(job)
            except Exception as e:
                # Log error but try to return from DB anyway (maybe synced previously)
                logger.error(f"Error syncing logs in test helper: {e}", exc_info=True)
                pass
        
        # 3. Retrieve job
        db_path = get_validations_db_path()
        if os.path.exists(db_path):
            with DatabaseManager(db_path) as db:
                if job_id:
                    validation = db.get_validation(job_id)
                    if validation:
                        return validation
                elif user_id:
                    # Look up by paid_user_id (token[:8]) or free_user_id
                    # Note: validations.db stores token[:8] for paid users
                    paid_id = user_id[:8] if len(user_id) >= 8 else user_id
                    
                    # Try paid user first
                    results = db.get_validations(paid_user_id=paid_id, limit=1)
                    if results:
                        return results[0]
                        
                    # Try free user
                    results = db.get_validations(free_user_id=user_id, limit=1)
                    if results:
                        return results[0]

        # Not found
        return {"error": "Validation not found", "job_id": job_id, "user_id": user_id}

    @app.post("/test/reset-user")
    async def test_reset_user(request: ClearEventsRequest):
        """Reset a user to initial state"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()

        # Reset credits in users table
        conn.execute(
            "UPDATE users SET credits = 0 WHERE token = ?",
            (request.user_id,)
        )

        # Delete user passes
        conn.execute(
            "DELETE FROM user_passes WHERE token = ?",
            (request.user_id,)
        )

        # Delete daily usage records
        conn.execute(
            "DELETE FROM daily_usage WHERE token = ?",
            (request.user_id,)
        )

        # Note: We do NOT delete from validations.db (history is preserved)
        # UPGRADE_EVENT table is deprecated/removed

        conn.commit()
        conn.close()
        return {"success": True}

    @app.get("/test/health")
    async def test_health():
        """Health check for test environment"""
        return {
            "status": "ok",
            "testing": os.getenv('TESTING') == 'true'
        }
