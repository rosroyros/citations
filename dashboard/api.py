#!/usr/bin/env python3
"""
FastAPI application for dashboard API
Serves validation data and static files for internal operational dashboard
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
from database import get_database

# Initialize FastAPI app
app = FastAPI(
    title="Citations Dashboard API",
    description="Internal operational dashboard for citation validation monitoring",
    version="1.0.0",
)

# Get database instance
db = get_database()

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    """Serve the main dashboard page"""
    static_file = "static/index.html"
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {
        "message": "Citations Dashboard API",
        "status": "running",
        "endpoints": {
            "validations": "/api/validations",
            "stats": "/api/stats",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Get recent parser errors for health status
        recent_errors = db.get_parser_errors(limit=5)
        last_parsed = db.get_metadata("last_parsed_timestamp")

        return {
            "status": "ok",
            "last_parsed": last_parsed,
            "recent_errors": recent_errors,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat() + "Z"
        }


@app.get("/api/validations/{job_id}")
async def get_validation(job_id: str):
    """Get details for a specific validation"""
    validation = db.get_validation(job_id)
    if not validation:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Format token usage if present
    if validation.get("token_usage_total"):
        validation["token_usage"] = {
            "prompt": validation.get("token_usage_prompt", 0),
            "completion": validation.get("token_usage_completion", 0),
            "total": validation["token_usage_total"]
        }

    return validation


@app.get("/api/validations")
async def get_validations(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    user_type: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    order_by: str = "created_at",
    order_dir: str = "DESC"
):
    """Get validations with filtering and pagination"""

    # Validate parameters
    if limit > 200:
        limit = 200
    if order_dir not in ["ASC", "DESC"]:
        order_dir = "DESC"
    if status and status not in ["completed", "failed", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    if user_type and user_type not in ["free", "paid"]:
        raise HTTPException(status_code=400, detail="Invalid user_type")

    validations = db.get_validations(
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

    # Get total count for pagination
    total = db.get_validations_count(
        status=status,
        user_type=user_type,
        search=search,
        from_date=from_date,
        to_date=to_date
    )

    # Format validations for frontend
    formatted_validations = []
    for validation in validations:
        # Format token usage
        token_usage = None
        if validation.get("token_usage_total"):
            token_usage = {
                "prompt": validation.get("token_usage_prompt", 0),
                "completion": validation.get("token_usage_completion", 0),
                "total": validation["token_usage_total"]
            }

        formatted_validation = {
            "job_id": validation["job_id"],
            "created_at": validation["created_at"],
            "completed_at": validation.get("completed_at"),
            "duration_seconds": validation.get("duration_seconds"),
            "citation_count": validation.get("citation_count"),
            "user_type": validation["user_type"],
            "status": validation["status"],
            "error_message": validation.get("error_message"),
            "token_usage": token_usage
        }
        formatted_validations.append(formatted_validation)

    return {
        "validations": formatted_validations,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/stats")
async def get_stats(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Get summary statistics for validations"""
    stats = db.get_stats(from_date=from_date, to_date=to_date)

    return {
        "total_validations": stats["total_validations"],
        "completed": stats["completed"],
        "failed": stats["failed"],
        "pending": stats["pending"],
        "total_citations": stats["total_citations"],
        "free_users": stats["free_users"],
        "paid_users": stats["paid_users"],
        "avg_duration_seconds": stats["avg_duration_seconds"],
        "avg_citations_per_validation": stats["avg_citations_per_validation"]
    }


@app.get("/api/parser-errors")
async def get_parser_errors(limit: int = 50):
    """Get recent parser errors"""
    if limit > 200:
        limit = 200

    errors = db.get_parser_errors(limit=limit)
    return {"errors": errors}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4646)