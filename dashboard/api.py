from fastapi import FastAPI, HTTPException, Query, Depends, Request
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import sqlite3
import os

app = FastAPI(title="Citations Dashboard API", version="2.0")

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "validations.db")

# Database Manager
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

def get_db():
    return DatabaseManager()

# Pydantic Models
class ValidationResponse(BaseModel):
    job_id: str
    created_at: str
    validation_status: str
    citation_count: int
    user_type: Optional[str]
    provider: Optional[str]
    duration_seconds: Optional[float]
    error_message: Optional[str] = None
    results_gated: Optional[bool] = False
    paid_user_id: Optional[str] = None
    free_user_id: Optional[str] = None

class ValidationsListResponse(BaseModel):
    validations: List[ValidationResponse]
    total: int
    limit: int
    offset: int

class StatsResponse(BaseModel):
    total_validations: int
    completed: int
    failed: int
    pending: int
    total_citations: int
    free_users: int
    paid_users: int
    avg_duration_seconds: float
    avg_citations_per_validation: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database_connected: bool
    total_records: int

# Utility Functions
def validate_pagination_params(limit: int, offset: int):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

def validate_status(status: Optional[str]):
    valid_statuses = ['completed', 'failed', 'pending']
    if status and status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

def validate_user_type(user_type: Optional[str]):
    valid_user_types = ['free', 'paid']
    if user_type and user_type not in valid_user_types:
        raise HTTPException(status_code=400, detail=f"Invalid user_type. Must be one of: {valid_user_types}")

def validate_search_term(search: Optional[str]):
    if search and len(search.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")

def validate_date_format(date_str: Optional[str], field_name: str):
    if date_str:
        try:
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
            pass

def validate_order_by(order_by: str):
    valid_columns = ['created_at', 'job_id', 'duration_seconds', 'citation_count', 'user_type', 'provider', 'validation_status']
    if order_by not in valid_columns:
        raise HTTPException(status_code=400, detail=f"Invalid order_by. Must be one of: {valid_columns}")

# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {"message": "Citations Dashboard API v2.0", "docs": "/docs"}

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check API health status"""
    try:
        with get_db() as db:
            cursor = db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM validations")
            total_records = cursor.fetchone()[0]
        database_connected = True
    except Exception as e:
        print(f"Database connection failed: {e}")
        database_connected = False
        total_records = 0

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        database_connected=database_connected,
        total_records=total_records
    )

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(
    from_date: Optional[str] = Query(None, description="Filter validations created after this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="Filter validations created before this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    database: DatabaseManager = Depends(get_db)
):
    """Get validation statistics"""
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)

    try:
        cursor = database.conn.cursor()

        # Base query with optional date filtering
        query = "SELECT COUNT(*), validation_status FROM validations WHERE 1=1"
        params = []

        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Parse results
        stats = {row[1]: row[0] for row in results}
        total_validations = sum(stats.values())
        completed = stats.get('completed', 0)
        failed = stats.get('failed', 0)
        pending = stats.get('pending', 0)

        # Get citation statistics
        cursor.execute(
            "SELECT SUM(citation_count), AVG(citation_count), AVG(duration_seconds) FROM validations WHERE validation_status = 'completed'"
        )
        result = cursor.fetchone()
        total_citations = result[0] or 0
        avg_citations_per_validation = float(result[1] or 0)
        avg_duration_seconds = float(result[2] or 0)

        # Get user type statistics
        cursor.execute("SELECT COUNT(DISTINCT CASE WHEN paid_user_id IS NOT NULL THEN paid_user_id END) FROM validations")
        paid_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT CASE WHEN free_user_id IS NOT NULL THEN free_user_id END) FROM validations")
        free_users = cursor.fetchone()[0]

        return StatsResponse(
            total_validations=total_validations,
            completed=completed,
            failed=failed,
            pending=pending,
            total_citations=total_citations,
            free_users=free_users,
            paid_users=paid_users,
            avg_duration_seconds=avg_duration_seconds,
            avg_citations_per_validation=avg_citations_per_validation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/api/chart-data")
async def get_chart_data(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None)
):
    """Get simplified chart data without excludeTests"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

@app.get("/api/validations", response_model=ValidationsListResponse)
async def get_validations(
    limit: int = Query(50, description="Maximum number of records to return (1-1000)"),
    offset: int = Query(0, description="Number of records to skip"),
    status: Optional[str] = Query(None, description="Filter by status (completed, failed, pending)"),
    user_type: Optional[str] = Query(None, description="Filter by user type (free, paid)"),
    search: Optional[str] = Query(None, description="Search in job_id field (minimum 2 characters)"),
    from_date: Optional[str] = Query(None, description="Filter by created_at >= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="Filter by created_at <= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    order_by: str = Query("created_at", description="Column to sort by"),
    order_dir: str = Query("DESC", pattern="^(ASC|DESC)$", description="Sort direction")
):
    """Get validations with filtering and pagination"""
    # Input validation
    validate_pagination_params(limit, offset)
    validate_status(status)
    validate_user_type(user_type)
    validate_search_term(search)
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)
    validate_order_by(order_by)

    try:
        with get_db() as db:
            # Build query
            query = "SELECT * FROM validations WHERE 1=1"
            params = []

            # Add filters
            if status:
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

            # Add sorting
            query += f" ORDER BY {order_by} {order_dir}"

            # Add pagination
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = db.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM validations WHERE 1=1"
            count_params = []

            if status:
                count_query += " AND validation_status = ?"
                count_params.append(status)

            if user_type:
                count_query += " AND user_type = ?"
                count_params.append(user_type)

            if search:
                count_query += " AND job_id LIKE ?"
                count_params.append(f"%{search}%")

            if from_date:
                count_query += " AND created_at >= ?"
                count_params.append(from_date)

            if to_date:
                count_query += " AND created_at <= ?"
                count_params.append(to_date)

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]

            # Convert to response models
            validation_responses = []
            for validation in rows:
                validation_responses.append(ValidationResponse(**validation))

            return ValidationsListResponse(
                validations=validation_responses,
                total=total,
                limit=limit,
                offset=offset
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4646)