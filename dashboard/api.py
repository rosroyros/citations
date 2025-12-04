#!/usr/bin/env python3
"""
FastAPI application for operational dashboard
Provides REST API for querying validation data and serving frontend
"""
import os
import sys
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import re

from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# Add dashboard directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database, DatabaseManager

# Initialize FastAPI app
app = FastAPI(
    title="Citations Dashboard API",
    description="""
# Citations Dashboard API

Operational dashboard for monitoring citation validation activity and system performance.

## Features
- Real-time validation monitoring
- Comprehensive statistics and analytics
- Advanced filtering and pagination
- Parser error tracking
- System health monitoring

## Authentication
Currently requires no authentication for development. Production endpoints will be restricted by CORS configuration.

## Rate Limiting
No rate limiting implemented yet. Consider adding for production deployment.

## Database
Uses SQLite with WAL mode for optimal read/write performance.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
# In production, restrict to specific origins
if os.getenv("DASHBOARD_ENV") == "production":
    allowed_origins = [
        "https://citationformatchecker.com",
        "https://admin.citationformatchecker.com",
        "https://www.citationformatchecker.com"
    ]
else:
    # Allow all origins for development
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Input validation functions
def validate_date_format(date_str: str, field_name: str) -> None:
    """Validate ISO date format (YYYY-MM-DD)"""
    if date_str and not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$', date_str):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)")

def validate_date_range(from_date: str, to_date: str) -> None:
    """Validate that from_date is not after to_date"""
    if from_date and to_date:
        try:
            from_dt = datetime.fromisoformat(from_date.rstrip('Z'))
            to_dt = datetime.fromisoformat(to_date.rstrip('Z'))
            if from_dt > to_dt:
                raise HTTPException(status_code=400, detail="from_date cannot be after to_date")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format in range")

def validate_pagination_params(limit: int, offset: int) -> None:
    """Validate pagination parameters"""
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be at least 1")
    if limit > 1000:
        raise HTTPException(status_code=400, detail="limit cannot exceed 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset cannot be negative")

def validate_search_term(search: str) -> None:
    """Validate search term"""
    if search and len(search.strip()) < 2:
        raise HTTPException(status_code=400, detail="search term must be at least 2 characters")

def validate_status(status: Optional[str]) -> None:
    """Validate status parameter"""
    if status and status not in ['completed', 'failed', 'pending']:
        raise HTTPException(status_code=400, detail="status must be one of: completed, failed, pending")

def validate_user_type(user_type: Optional[str]) -> None:
    """Validate user_type parameter"""
    if user_type and user_type not in ['free', 'paid']:
        raise HTTPException(status_code=400, detail="user_type must be one of: free, paid")

def validate_order_by(order_by: str) -> None:
    """Validate order_by parameter"""
    valid_columns = ['created_at', 'completed_at', 'duration_seconds', 'citation_count', 'job_id']
    if order_by not in valid_columns:
        raise HTTPException(status_code=400, detail=f"order_by must be one of: {', '.join(valid_columns)}")

# Connection pool for better performance under load
class DatabaseConnectionPool:
    """Simple connection pool for database instances"""

    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self._pool = []
        self._in_use = set()

    def get_connection(self):
        """Get database connection from pool or create new one"""
        from database import DatabaseManager

        dashboard_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(dashboard_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "validations.db")

        # Return new connection for now (SQLite doesn't benefit much from connection pooling)
        # This is prepared for future migration to PostgreSQL/MySQL if needed
        return DatabaseManager(db_path)

# Global connection pool (disabled for SQLite, but ready for future use)
_connection_pool = None

def get_db():
    """
    Get database connection for the current request
    Ensures thread-safe database access with optimized SQLite settings
    """
    # For SQLite, create new connection per request (this is actually optimal)
    from database import DatabaseManager
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(dashboard_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "validations.db")

    db = DatabaseManager(db_path)
    try:
        yield db
    finally:
        # Close connection to prevent thread issues and free resources
        db.close()


# Pydantic models for API responses
class ValidationResponse(BaseModel):
    """Validation record response model"""
    job_id: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    citation_count: Optional[int] = None
    token_usage_prompt: Optional[int] = None
    token_usage_completion: Optional[int] = None
    token_usage_total: Optional[int] = None
    user_type: str
    status: str
    error_message: Optional[str] = None
    results_gated: Optional[bool] = Field(
        None,
        description="Whether results were gated behind paywall"
    )
    results_revealed_at: Optional[str] = Field(
        None,
        description="Timestamp when user revealed gated results (ISO 8601 format)"
    )
    time_to_reveal_seconds: Optional[int] = Field(
        None,
        description="Time between results being ready and user revealing them (seconds)"
    )
    gated_outcome: Optional[str] = Field(
        None,
        description="Outcome of gating interaction (revealed, dismissed, etc.)"
    )


class StatsResponse(BaseModel):
    """Statistics response model"""
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
    """Health check response model"""
    status: str
    timestamp: str
    database_connected: bool
    total_records: int


class CitationResponse(BaseModel):
    """Citation response model"""
    job_id: str
    citation_text: str
    created_at: str


class CitationsListResponse(BaseModel):
    """List of citations for a job"""
    job_id: str
    citations: List[CitationResponse]
    total: int


class ValidationError(BaseModel):
    """Parser error response model"""
    id: int
    timestamp: str
    error_message: str
    log_line: Optional[str] = None


class GatedStatsResponse(BaseModel):
    """Gated results engagement statistics response model"""
    total_gated: int
    revealed_count: int
    reveal_rate: float
    avg_time_to_reveal_seconds: float
    by_user_type: Dict[str, Dict[str, Any]]
    by_outcome: Dict[str, int]
    daily_trends: List[Dict[str, Any]]
    conversion_metrics: Dict[str, Any]


class ValidationsListResponse(BaseModel):
    """Validations list response model with pagination"""
    validations: List[ValidationResponse]
    total: int
    limit: int
    offset: int


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """
    Serve the main dashboard HTML page

    Returns dashboard frontend HTML. Serves from static/index.html
    if it exists, otherwise returns a basic HTML template.
    """
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            return HTMLResponse(content=f.read())

    # Fallback basic HTML if static/index.html doesn't exist
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Citations Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .status { padding: 20px; background: #f0f8ff; border-radius: 8px; }
            .api-link { color: #0066cc; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Citations Dashboard</h1>
            <div class="status">
                <h2>API Status</h2>
                <p>Dashboard API is running successfully!</p>
                <p><a href="/api/health" class="api-link">Check API Health</a></p>
                <p><a href="/api/stats" class="api-link">View Statistics</a></p>
                <p><a href="/api/validations?limit=10" class="api-link">Sample Validations</a></p>
            </div>
        </div>
    </body>
    </html>
    """)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="""
Check the operational status of the dashboard API service.

**Response includes:**
- Service health status
- Database connectivity verification
- Total validation records count
- Timestamp of health check

**Use Cases:**
- Load balancer health checks
- Monitoring and alerting systems
- Service discovery in containerized environments
- Application startup verification

**Status Codes:**
- `200 OK`: Service healthy
- `503 Service Unavailable`: Database connection failed
"""
)
async def health_check(database: DatabaseManager = Depends(get_db)):
    """Health check endpoint implementation"""
    try:
        # Test database connection
        total_records = database.get_validations_count()
        database_connected = True
    except Exception as e:
        print(f"Database connection failed: {e}")
        database_connected = False
        total_records = 0

    return HealthResponse(
        status="healthy" if database_connected else "unhealthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        database_connected=database_connected,
        total_records=total_records
    )


@app.get("/api/validations/{job_id}", response_model=ValidationResponse)
async def get_validation(job_id: str, database: DatabaseManager = Depends(get_db)):
    """
    Get a single validation by job ID

    Returns detailed information for a specific validation job.
    Used for drill-down views and debugging.

    Path Parameters:
    - job_id: The unique identifier for the validation job
    """
    try:
        validation = database.get_validation(job_id)
        if not validation:
            raise HTTPException(status_code=404, detail=f"Validation {job_id} not found")

        # Map database column names to API field names
        validation_data = {
            **validation
        }
        return ValidationResponse(**validation_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation: {str(e)}")


@app.get("/api/validations/{job_id}/citations", response_model=CitationsListResponse)
async def get_job_citations(job_id: str, database: DatabaseManager = Depends(get_db)):
    """
    Get citations for a specific validation job

    Returns all citations that were processed for this validation job from the
    citations_dashboard table.

    Path Parameters:
    - job_id: The unique identifier for the validation job
    """
    try:
        conn = database.conn
        cursor = conn.cursor()

        # Fetch citations for this job
        cursor.execute("""
            SELECT job_id, citation_text, created_at
            FROM citations_dashboard
            WHERE job_id = ?
            ORDER BY id ASC
        """, (job_id,))

        rows = cursor.fetchall()

        citations = [
            CitationResponse(
                job_id=row[0],
                citation_text=row[1],
                created_at=row[2]
            )
            for row in rows
        ]

        return CitationsListResponse(
            job_id=job_id,
            citations=citations,
            total=len(citations)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get citations: {str(e)}")


@app.get("/api/validations", response_model=ValidationsListResponse)
async def get_validations(
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    status: Optional[str] = Query(None, description="Filter by status (completed, failed, pending)"),
    user_type: Optional[str] = Query(None, description="Filter by user type (free, paid)"),
    search: Optional[str] = Query(None, description="Search in job_id field"),
    paid_user_id: Optional[str] = Query(None, description="Filter by paid user ID"),
    free_user_id: Optional[str] = Query(None, description="Filter by free user ID"),
    from_date: Optional[str] = Query(None, description="Filter by created_at >= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="Filter by created_at <= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    order_by: str = Query("created_at", description="Column to sort by"),
    order_dir: str = Query("DESC", pattern="^(ASC|DESC)$", description="Sort direction"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get validations with filtering and pagination

    Returns a list of validation records with optional filtering and pagination.

    Query Parameters:
    - limit: Maximum number of records (1-1000)
    - offset: Number of records to skip for pagination
    - status: Filter by validation status (completed, failed, pending)
    - user_type: Filter by user type (free/paid)
    - search: Search in job_id field (partial match, min 2 chars)
    - paid_user_id: Filter by paid user ID (exact match)
    - free_user_id: Filter by free user ID (exact match)
    - from_date: Include only validations created after this date (ISO 8601)
    - to_date: Include only validations created before this date (ISO 8601)
    - order_by: Column to sort by (created_at, duration_seconds, etc.)
    - order_dir: Sort direction (ASC/DESC)
    """
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
        validations = database.get_validations(
            limit=limit,
            offset=offset,
            status=status,
            user_type=user_type,
            search=search,
            paid_user_id=paid_user_id,
            free_user_id=free_user_id,
            from_date=from_date,
            to_date=to_date,
            order_by=order_by,
            order_dir=order_dir
        )

        # Get total count for pagination
        total = database.get_validations_count(
            status=status,
            user_type=user_type,
            search=search,
            paid_user_id=paid_user_id,
            free_user_id=free_user_id,
            from_date=from_date,
            to_date=to_date
        )

        # Convert to response models
        validation_responses = []
        for validation in validations:
            validation_responses.append(ValidationResponse(**validation))

        return ValidationsListResponse(
            validations=validation_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validations: {str(e)}")


@app.get("/api/validations/count")
async def get_validations_count(
    status: Optional[str] = Query(None, description="Filter by status (completed, failed, pending)"),
    user_type: Optional[str] = Query(None, description="Filter by user type (free, paid)"),
    search: Optional[str] = Query(None, description="Search in job_id field"),
    paid_user_id: Optional[str] = Query(None, description="Filter by paid user ID"),
    free_user_id: Optional[str] = Query(None, description="Filter by free user ID"),
    from_date: Optional[str] = Query(None, description="Filter by created_at >= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="Filter by created_at <= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get count of validations matching filters

    Returns the total count of validations that match the specified filters.
    Useful for pagination UI and analytics.
    """
    # Input validation
    validate_status(status)
    validate_user_type(user_type)
    validate_search_term(search)
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)

    try:
        count = database.get_validations_count(
            status=status,
            user_type=user_type,
            search=search,
            paid_user_id=paid_user_id,
            free_user_id=free_user_id,
            from_date=from_date,
            to_date=to_date
        )
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation count: {str(e)}")


@app.get("/api/dashboard")
async def get_dashboard_data(
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    status: Optional[str] = Query(None, description="Filter by status (completed, failed, pending)"),
    user_type: Optional[str] = Query(None, description="Filter by user type (free, paid)"),
    search: Optional[str] = Query(None, description="Search in job_id field"),
    from_date: Optional[str] = Query(None, description="Filter by created_at >= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="Filter by created_at <= date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    order_by: str = Query("created_at", description="Column to sort by"),
    order_dir: str = Query("DESC", pattern="^(ASC|DESC)$", description="Sort direction"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get dashboard data in format expected by frontend

    Returns validation data with field names mapped for frontend compatibility.
    Used by the React dashboard frontend.
    """
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
        validations = database.get_validations(
            limit=limit,
            offset=offset,
            status=status,
            user_type=user_type,
            search=search,
            from_date=from_date,
            to_date=to_date,
            order_by=order_by,
            order_dir=order_dir
        )

        # Map database fields to frontend expected format
        jobs = []
        for validation in validations:
            # Determine reveal status based on user_type and results_revealed_at
            reveal_status = "N/A"
            if validation.get("user_type") == "free":
                if validation.get("results_revealed_at"):
                    reveal_status = "Yes"
                elif validation.get("results_gated"):
                    reveal_status = "No"
                else:
                    reveal_status = "N/A"  # Not gated

            # Determine user identifier to display
            user_id = validation.get("paid_user_id") or validation.get("free_user_id") or "unknown"
            user_type = validation.get("user_type", "unknown")
            user_display = f"{user_id} ({user_type})" if user_id != "unknown" else user_type

            job_data = {
                "id": validation.get("job_id"),
                "timestamp": validation.get("created_at"),
                "status": validation.get("validation_status", validation.get("status", "unknown")),
                "user": user_display,
                "citations": validation.get("citation_count", 0),
                "errors": None,  # Extract from error_message if needed
                "processing_time": f"{validation.get('duration_seconds', 0):.1f}s" if validation.get("duration_seconds") else None,
                "revealed": reveal_status,
                # Include raw reveal fields for detailed view
                "results_gated": validation.get("results_gated"),
                "results_revealed_at": validation.get("results_revealed_at"),
                "time_to_reveal_seconds": validation.get("time_to_reveal_seconds"),
                "gated_outcome": validation.get("gated_outcome"),
                # Token usage fields
                "token_usage": {
                    "prompt": validation.get("token_usage_prompt"),
                    "completion": validation.get("token_usage_completion"),
                    "total": validation.get("token_usage_total")
                },
                # Additional fields for details modal
                "validation_id": validation.get("job_id"),
                "session_id": validation.get("job_id"),  # Use job_id as session_id for now
                "ip_address": "N/A",  # Not tracked in current schema
                "source_type": "N/A",  # Not tracked in current schema
                "api_version": "N/A"  # Not tracked in current schema
            }
            jobs.append(job_data)

        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(
    from_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get dashboard statistics

    Provides summary statistics for validations, including:
    - Total, completed, failed, pending counts
    - Citation metrics
    - User type breakdown
    - Average duration and citation count

    Query Parameters:
    - from_date: Filter validations created after this date
    - to_date: Filter validations created before this date
    """
    # Input validation
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)

    try:
        stats = database.get_stats(from_date=from_date, to_date=to_date)
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/api/errors", response_model=List[ValidationError])
async def get_parser_errors(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of errors to return"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get recent parser errors

    Returns a list of recent parsing errors for debugging and monitoring.
    Shows what went wrong during log parsing.

    Query Parameters:
    - limit: Maximum number of errors to return (1-200)
    """
    try:
        errors = database.get_parser_errors(limit=limit)
        return [ValidationError(**error) for error in errors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get parser errors: {str(e)}")


@app.get("/api/gated-stats", response_model=GatedStatsResponse)
async def get_gated_stats(
    from_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DDTHH:MM:SSZ)"),
    database: DatabaseManager = Depends(get_db)
):
    """
    Get gated results engagement statistics

    Provides comprehensive engagement metrics for gated validation results, including:
    - Overall gating and reveal rates
    - User type breakdowns (free vs paid)
    - Daily engagement trends
    - Conversion funnel metrics
    - Outcome analysis

    Query Parameters:
    - from_date: Filter validations created after this date
    - to_date: Filter validations created before this date
    """
    # Input validation
    validate_date_format(from_date, "from_date")
    validate_date_format(to_date, "to_date")
    validate_date_range(from_date, to_date)

    try:
        stats = database.get_gated_stats(from_date=from_date, to_date=to_date)
        return GatedStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get gated statistics: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions

    Returns a standardized error response for any unhandled exceptions.
    Prevents stack traces from leaking to clients in production.
    """
    print(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error. Check logs for details."
    )


if __name__ == "__main__":
    import uvicorn

    # Run API server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=4646,
        reload=False,  # Set to True for development
        log_level="info"
    )