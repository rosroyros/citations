from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from html.parser import HTMLParser
from backend.logger import setup_logger
from backend.providers.openai_provider import OpenAIProvider

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("citation_validator")

# Initialize LLM provider
llm_provider = OpenAIProvider()


class HTMLToTextConverter(HTMLParser):
    """Convert HTML to text while preserving formatting indicators."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.in_italic = False
        self.in_bold = False
        self.in_underline = False

    def handle_starttag(self, tag, attrs):
        if tag in ['em', 'i']:
            self.in_italic = True
            self.text.append('[ITALIC]')
        elif tag in ['strong', 'b']:
            self.in_bold = True
            self.text.append('[BOLD]')
        elif tag == 'u':
            self.in_underline = True
            self.text.append('[UNDERLINE]')
        elif tag == 'p':
            if self.text and self.text[-1] != '\n':
                self.text.append('\n')

    def handle_endtag(self, tag):
        if tag in ['em', 'i']:
            self.in_italic = False
            self.text.append('[/ITALIC]')
        elif tag in ['strong', 'b']:
            self.in_bold = False
            self.text.append('[/BOLD]')
        elif tag == 'u':
            self.in_underline = False
            self.text.append('[/UNDERLINE]')
        elif tag == 'p':
            self.text.append('\n')

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ''.join(self.text).strip()


def html_to_text_with_formatting(html: str) -> str:
    """Convert HTML citations to text with formatting markers."""
    converter = HTMLToTextConverter()
    converter.feed(html)
    return converter.get_text()


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


class CitationError(BaseModel):
    """Model for a single citation error."""
    component: str
    problem: str
    correction: str


class CitationResult(BaseModel):
    """Model for a single citation validation result."""
    citation_number: int
    original: str
    source_type: str
    errors: list[CitationError]


class ValidationResponse(BaseModel):
    """Response model for citation validation."""
    results: list[CitationResult]


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
    Validate citations against APA 7th edition rules using LLM.

    Args:
        request: ValidationRequest with citations text and style

    Returns:
        ValidationResponse with validation results and errors
    """
    logger.info(f"Validation request received for style: {request.style}")
    logger.debug(f"Citations length: {len(request.citations)} characters")

    # Validate input
    if not request.citations or not request.citations.strip():
        logger.warning("Empty citations submitted")
        raise HTTPException(status_code=400, detail="Citations cannot be empty")

    # Convert HTML to text with formatting markers
    citations_text = html_to_text_with_formatting(request.citations)
    logger.debug(f"Converted HTML to text: {len(citations_text)} characters")
    logger.debug(f"Citation text preview: {citations_text[:200]}...")

    try:
        # Call LLM provider for validation
        logger.info("Calling LLM provider for validation")
        validation_results = await llm_provider.validate_citations(
            citations=citations_text,
            style=request.style
        )

        logger.info(f"Validation completed: {len(validation_results['results'])} result(s)")

        return ValidationResponse(results=validation_results["results"])

    except ValueError as e:
        # User-facing errors from LLM provider (rate limits, timeouts, auth errors)
        logger.error(f"Validation failed with user error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected validation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
