from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import os

app = FastAPI(title="Citations Dashboard API")

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "validations.db")

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

def get_db():
    db = DatabaseManager()
    try:
        yield db
    finally:
        db.conn.close()

def validate_date_format(date_str: Optional[str], field_name: str):
    if date_str:
        try:
            # Try parsing the ISO format
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid {field_name} format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ")

def validate_date_range(from_date: Optional[str], to_date: Optional[str]):
    if from_date and to_date:
        try:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            if from_dt >= to_dt:
                raise HTTPException(status_code=400, detail="from_date must be earlier than to_date")
        except ValueError:
            pass  # Already validated above

@app.get("/")
async def root():
    return {"message": "Citations Dashboard API"}

@app.get("/api/chart-data")
async def get_chart_data(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db)
):
    """Get simplified chart data without excludeTests"""
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)

    try:
        query = """
            SELECT
                DATE(created_at) as date,
                COUNT(*) as total_validations,
                COUNT(CASE WHEN validation_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN validation_status = 'failed' THEN 1 END) as failed,
                SUM(CASE WHEN validation_status = 'completed' THEN citation_count ELSE 0 END) as successful_citations,
                SUM(CASE WHEN validation_status = 'failed' THEN citation_count ELSE 0 END) as failed_citations,
                SUM(citation_count) as total_citations,
                COUNT(CASE WHEN provider = 'model_a' OR provider = 'openai' THEN 1 END) as model_a_jobs,
                COUNT(CASE WHEN provider = 'model_b' OR provider = 'gemini' THEN 1 END) as model_b_jobs
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

        query += " GROUP BY DATE(created_at) ORDER BY date ASC"

        cursor = db.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        daily_data = []
        for row in rows:
            daily_data.append({
                "date": row[0],
                "total_validations": row[1],
                "completed": row[2],
                "failed": row[3],
                "successful_citations": row[4] or 0,
                "failed_citations": row[5] or 0,
                "total_citations": row[6] or 0,
                "model_a_jobs": row[7] or 0,
                "model_b_jobs": row[8] or 0
            })

        # Get provider distribution
        provider_query = """
            SELECT provider, COUNT(*) as count
            FROM validations
            WHERE 1=1
        """
        provider_params = []

        if from_date:
            provider_query += " AND created_at >= ?"
            provider_params.append(from_date)

        if to_date:
            provider_query += " AND created_at <= ?"
            provider_params.append(to_date)

        provider_query += " GROUP BY provider"

        cursor.execute(provider_query, provider_params)
        provider_rows = cursor.fetchall()

        provider_data = {}
        for row in provider_rows:
            provider = row[0] or 'unknown'
            provider_data[provider] = row[1]

        return {"daily": daily_data, "providers": provider_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chart data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4646)