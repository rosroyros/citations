
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