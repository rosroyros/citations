from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.logger import setup_logger

# Initialize logger
logger = setup_logger("citation_validator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    logger.info("Citation Validator API starting up")
    yield
    logger.info("Citation Validator API shutting down")


# Create FastAPI app
app = FastAPI(
    title="Citation Validator API",
    description="APA 7th edition citation validation using LLM",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


class ValidationRequest(BaseModel):
    """Request model for citation validation."""
    citations: str
    style: str


class ValidationResponse(BaseModel):
    """Response model for citation validation."""
    citations: list[str]


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status indicator
    """
    logger.debug("Health check endpoint called")
    return {"status": "ok"}


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_citations(request: ValidationRequest):
    """
    Validate citations against APA 7th edition rules.

    Args:
        request: ValidationRequest with citations text and style

    Returns:
        ValidationResponse with parsed citations
    """
    logger.info(f"Validation request received for style: {request.style}")
    logger.debug(f"Citations text length: {len(request.citations)} characters")

    # Parse citations by splitting on double newlines
    parsed_citations = [
        citation.strip()
        for citation in request.citations.split("\n\n")
        if citation.strip()
    ]

    logger.info(f"Parsed {len(parsed_citations)} citation(s)")
    logger.debug(f"Citations: {parsed_citations}")

    return ValidationResponse(citations=parsed_citations)
