from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, Dict, Any
import sqlite3
import os

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "validations.db")

app = FastAPI(title="Citations Dashboard API")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {"message": "Citations Dashboard API"}

@app.get("/api/chart-data")
async def get_chart_data(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None)
):
    """Get simplified chart data"""
    try:
        conn = get_db()
        cursor = conn.cursor()

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

        conn.close()

        return {"daily": daily_data, "providers": provider_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chart data: {str(e)}")

# Keep all other endpoints from the original API
# Import the original API and mount it
try:
    import api as original_api

    @app.get("/api/stats")
    async def get_stats_original():
        from api import get_database_manager
        db = get_database_manager()
        return await original_api.get_stats(database=db)

    @app.get("/api/validations")
    async def get_validations_original(
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        user_type: Optional[str] = None,
        search: Optional[str] = None
    ):
        from api import get_database_manager
        db = get_database_manager()
        return await original_api.get_validations(
            limit=limit,
            offset=offset,
            status=status,
            user_type=user_type,
            search=search,
            database=db
        )

except ImportError:
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4646)