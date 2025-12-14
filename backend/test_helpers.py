"""
Test helper endpoints for E2E testing
These endpoints are only available when TESTING=true
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import sqlite3
from datetime import datetime, timedelta

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

    @app.get("/test/get-events")
    async def test_get_events(user_id: str):
        """Get tracking events for a user"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()
        events = conn.execute(
            "SELECT * FROM UPGRADE_EVENT WHERE user_id = ? ORDER BY timestamp",
            (user_id,)
        ).fetchall()
        conn.close()

        return [dict(e) for e in events]

    @app.post("/test/clear-events")
    async def test_clear_events(request: ClearEventsRequest):
        """Clear tracking events for a user"""
        if os.getenv('TESTING') != 'true':
            raise HTTPException(status_code=404, detail="Not found")

        conn = get_test_db()
        conn.execute(
            "DELETE FROM UPGRADE_EVENT WHERE user_id = ?",
            (request.user_id,)
        )
        conn.commit()
        conn.close()

        return {"success": True}

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

        # Clear events
        conn.execute(
            "DELETE FROM UPGRADE_EVENT WHERE user_id = ?",
            (request.user_id,)
        )

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