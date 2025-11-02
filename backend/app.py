from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from html.parser import HTMLParser
from typing import Optional
import os
import uuid
import json
from polar_sdk import Polar
from polar_sdk.webhooks import validate_event, WebhookVerificationError
from logger import setup_logger
from providers.openai_provider import OpenAIProvider

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("citation_validator")

# Initialize LLM provider with GEPA-optimized prompt
llm_provider = OpenAIProvider()

# Initialize Polar client
polar = Polar(access_token=os.getenv('POLAR_ACCESS_TOKEN'))


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
            self.text.append('_')  # Markdown italic format
        elif tag in ['strong', 'b']:
            self.in_bold = True
            self.text.append('**')  # Markdown bold format
        elif tag == 'u':
            self.in_underline = True
            self.text.append('_')  # Markdown underline as italic
        elif tag == 'p':
            if self.text and self.text[-1] != '\n':
                self.text.append('\n')

    def handle_endtag(self, tag):
        if tag in ['em', 'i']:
            self.in_italic = False
            self.text.append('_')  # Markdown italic format
        elif tag in ['strong', 'b']:
            self.in_bold = False
            self.text.append('**')  # Markdown bold format
        elif tag == 'u':
            self.in_underline = False
            self.text.append('_')  # Markdown underline as italic
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
    partial: bool = False
    citations_checked: Optional[int] = None
    citations_remaining: Optional[int] = None
    credits_remaining: Optional[int] = None


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status indicator
    """
    logger.debug("Health check endpoint called")
    return {"status": "ok"}


@app.post("/api/create-checkout")
async def create_checkout(request: dict):
    """
    Create a Polar checkout for purchasing citation credits.

    Args:
        request: Dict with optional 'token' field

    Returns:
        dict: {'checkout_url': str, 'token': str}
    """
    logger.info("Checkout creation request received")

    # Get or generate token
    token = request.get('token') or str(uuid.uuid4())
    logger.debug(f"Token for checkout: {token[:8]}...")

    try:
        # Create Polar checkout
        logger.info("Creating Polar checkout")
        checkout = await polar.checkouts.create({
            "product_id": os.getenv('POLAR_PRODUCT_ID'),
            "success_url": f"{os.getenv('FRONTEND_URL')}/success?token={token}",
            "metadata": {"token": token}
        })

        logger.info(f"Checkout created successfully: {checkout.url}")
        return {"checkout_url": checkout.url, "token": token}

    except Exception as e:
        logger.error(f"Failed to create checkout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create checkout: {str(e)}")


@app.get("/api/credits")
async def get_credits_balance(token: str):
    """
    Get credit balance for a user token.

    Args:
        token: User token to look up credits for

    Returns:
        dict: {"token": str, "credits": int}
    """
    if not token:
        raise HTTPException(status_code=400, detail="Token required")

    logger.debug(f"Getting credits balance for token: {token[:8]}...")

    try:
        from database import get_credits
        balance = get_credits(token)
        logger.debug(f"Retrieved balance: {balance} credits")
        return {"token": token, "credits": balance}

    except Exception as e:
        logger.error(f"Error getting credits balance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve credits balance")


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_citations(http_request: Request, request: ValidationRequest):
    """
    Validate citations against APA 7th edition rules using LLM.

    Args:
        http_request: FastAPI Request object containing headers
        request: ValidationRequest with citations text and style

    Returns:
        ValidationResponse with validation results and errors
    """
    logger.info(f"Validation request received for style: {request.style}")
    logger.debug(f"Citations length: {len(request.citations)} characters")

    # Extract token from headers
    token = http_request.headers.get('X-User-Token')
    logger.debug(f"Token present: {bool(token)}")
    if token:
        logger.debug(f"Token preview: {token[:8]}...")

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

        results = validation_results["results"]
        citation_count = len(results)
        logger.debug(f"Citation count: {citation_count}")

        # Handle credit logic
        if not token:
            # Free tier - return everything (frontend enforces 10 limit)
            logger.info("Free tier request - returning all results")
            return ValidationResponse(results=results)

        # Paid tier - check credits
        from database import get_credits, deduct_credits
        user_credits = get_credits(token)
        logger.debug(f"User credits: {user_credits}")

        if user_credits == 0:
            logger.warning("User has zero credits - returning 402 error")
            raise HTTPException(
                status_code=402,  # Payment Required
                detail="You have 0 Citation Credits remaining. Purchase more to continue."
            )

        if user_credits >= citation_count:
            # Can afford all citations
            logger.info(f"Sufficient credits ({user_credits} >= {citation_count}) - returning all results")
            success = deduct_credits(token, citation_count)
            if not success:
                logger.error("Failed to deduct credits")
                raise HTTPException(status_code=500, detail="Failed to deduct credits")

            return ValidationResponse(
                results=results,
                credits_remaining=user_credits - citation_count
            )
        else:
            # Partial results
            affordable = user_credits
            logger.info(f"Insufficient credits ({user_credits} < {citation_count}) - returning {affordable} results")
            success = deduct_credits(token, affordable)
            if not success:
                logger.error("Failed to deduct credits")
                raise HTTPException(status_code=500, detail="Failed to deduct credits")

            return ValidationResponse(
                results=results[:affordable],
                partial=True,
                citations_checked=affordable,
                citations_remaining=citation_count - affordable,
                credits_remaining=0
            )

    except ValueError as e:
        # User-facing errors from LLM provider (rate limits, timeouts, auth errors)
        logger.error(f"Validation failed with user error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException as e:
        # Re-raise HTTPExceptions (like 402 Payment Required)
        raise e

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected validation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/api/polar-webhook")
async def handle_polar_webhook(request: Request):
    """
    Handle Polar webhooks for payment processing.

    Verifies webhook signature and grants credits when payments are completed.

    Args:
        request: FastAPI Request object containing webhook payload

    Returns:
        Response: 200 OK for all processed webhooks
    """
    logger.info("Polar webhook received")

    # Get signature from headers
    signature = request.headers.get('X-Polar-Signature')
    if not signature:
        logger.warning("Webhook received without signature header")
        return Response(status_code=401, content='{"error": "Invalid signature"}')

    # Get raw body for signature verification
    body = await request.body()

    try:
        # Verify webhook signature and parse payload
        webhook = validate_event(
            body=body,
            headers=dict(request.headers),
            secret=os.getenv('POLAR_WEBHOOK_SECRET')
        )

        logger.info(f"Webhook signature verified: {webhook.type}")

        # Process only order.created and checkout.updated events
        if webhook.type == "order.created":
            await handle_order_created(webhook)
        elif webhook.type == "checkout.updated":
            await handle_checkout_updated(webhook)
        else:
            logger.debug(f"Ignoring webhook event type: {webhook.type}")

        return Response(status_code=200)

    except WebhookVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return Response(status_code=401, content='{"error": "Invalid signature"}')
    except Exception as e:
        logger.error(f"Unexpected webhook processing error: {str(e)}", exc_info=True)
        return Response(status_code=500, content='{"error": "Internal server error"}')


async def handle_order_created(webhook):
    """Handle order.created webhook by granting credits."""
    from database import add_credits

    order_id = webhook.data.id
    token = webhook.data.metadata.token

    logger.info(f"Processing order.created: order_id={order_id}, token={token[:8]}...")

    # Grant 1,000 credits (idempotent - add_credits checks for duplicate order_id)
    success = add_credits(token, 1000, order_id)

    if success:
        logger.info(f"Successfully granted 1000 credits for order {order_id}")
    else:
        logger.warning(f"Order {order_id} already processed, skipping credit grant")


async def handle_checkout_updated(webhook):
    """Handle checkout.updated webhook when status is completed."""
    from database import add_credits

    if webhook.data.status != "completed":
        logger.debug(f"Ignoring checkout.updated with status: {webhook.data.status}")
        return

    order_id = webhook.data.order_id
    token = webhook.data.metadata.token

    logger.info(f"Processing checkout.updated: order_id={order_id}, token={token[:8]}...")

    # Grant 1,000 credits (idempotent)
    success = add_credits(token, 1000, order_id)

    if success:
        logger.info(f"Successfully granted 1000 credits for completed checkout {order_id}")
    else:
        logger.warning(f"Checkout order {order_id} already processed, skipping credit grant")
