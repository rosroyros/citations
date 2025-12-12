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
    return sqlite3.connect(db_path)

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
            "INSERT OR IGNORE INTO user (id, credits) VALUES (?, ?)",
            (request.user_id, 0)
        )

        # Add credits
        conn.execute(
            "UPDATE user SET credits = credits + ? WHERE id = ?",
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

        # Create user if not exists
        conn.execute(
            "INSERT OR IGNORE INTO user (id, pass_end_date) VALUES (?, ?)",
            (request.user_id, None)
        )

        # Set pass end date
        end_date = (datetime.utcnow() + timedelta(days=request.days)).isoformat()
        conn.execute(
            "UPDATE user SET pass_end_date = ? WHERE id = ?",
            (end_date, request.user_id)
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

        # Create user if not exists
        conn.execute(
            "INSERT OR IGNORE INTO user (id, daily_usage, daily_usage_date) VALUES (?, ?, ?)",
            (request.user_id, 0, datetime.utcnow().date().isoformat())
        )

        # Set daily usage
        conn.execute(
            "UPDATE user SET daily_usage = ?, daily_usage_date = ? WHERE id = ?",
            (request.usage, datetime.utcnow().date().isoformat(), request.user_id)
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
        user = conn.execute(
            "SELECT * FROM user WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(user)

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

        # Reset user to initial state
        conn.execute(
            """
            UPDATE user SET
                credits = 0,
                pass_end_date = NULL,
                daily_usage = 0,
                daily_usage_date = ?
            WHERE id = ?
            """,
            (datetime.utcnow().date().isoformat(), request.user_id)
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