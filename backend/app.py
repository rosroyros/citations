from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from html.parser import HTMLParser
from typing import Optional, Dict, Any
import os
import uuid
import json
import base64
import time
from polar_sdk import Polar
from polar_sdk.webhooks import validate_event, WebhookVerificationError
from logger import setup_logger
from providers.openai_provider import OpenAIProvider
from database import get_credits, deduct_credits

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("citation_validator")

# Free tier limit
FREE_LIMIT = 10

# Initialize LLM provider (mock for E2E tests, real for production)
if os.getenv('MOCK_LLM', '').lower() == 'true':
    from providers.mock_provider import MockProvider
    llm_provider = MockProvider()
    logger.info("Using MockProvider for LLM (fast E2E testing mode)")
else:
    llm_provider = OpenAIProvider()
    logger.info("Using OpenAIProvider for LLM (production mode)")

# Initialize Polar client
polar = Polar(
    access_token=os.getenv('POLAR_ACCESS_TOKEN')
    # No server parameter = production API
)

# Global in-memory job storage
jobs: Dict[str, Dict[str, Any]] = {}


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
            # Add newline at start of paragraph
            # Don't skip if last char is \n - we want blank lines between <p> tags
            if self.text:
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

    # Start background job cleanup task
    import asyncio
    asyncio.create_task(cleanup_old_jobs())
    logger.info("Started job cleanup task")

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
    free_used: Optional[int] = None
    free_used_total: Optional[int] = None  # NEW - authoritative count for frontend


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status indicator
    """
    logger.debug("Health check endpoint called")
    return {"status": "ok"}


@app.get("/debug-env")
async def debug_environment():
    """
    Debug endpoint to check environment variables.

    Returns:
        dict: Environment variables (masked for security)
    """
    return {
        "POLAR_ACCESS_TOKEN": f"{os.getenv('POLAR_ACCESS_TOKEN', 'NOT_SET')[:10]}..." if os.getenv('POLAR_ACCESS_TOKEN') else "NOT_SET",
        "POLAR_PRODUCT_ID": os.getenv('POLAR_PRODUCT_ID', 'NOT_SET'),
        "POLAR_WEBHOOK_SECRET": f"{os.getenv('POLAR_WEBHOOK_SECRET', 'NOT_SET')[:10]}..." if os.getenv('POLAR_WEBHOOK_SECRET') else "NOT_SET",
        "FRONTEND_URL": os.getenv('FRONTEND_URL', 'NOT_SET')
    }


@app.post("/api/create-checkout")
def create_checkout(request: dict):
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
        logger.info(f"Product ID being used: {os.getenv('POLAR_PRODUCT_ID')}")
        logger.info(f"Token: {token}")

        checkout_request = {
            "products": [os.getenv('POLAR_PRODUCT_ID')],
            "success_url": f"{os.getenv('FRONTEND_URL')}/success?token={token}",
            "metadata": {"token": token}
        }
        logger.info(f"Checkout request: {checkout_request}")

        checkout = polar.checkouts.create(request=checkout_request)

        logger.info(f"Checkout created successfully: {checkout.url}")
        logger.info(f"Checkout object details: {checkout}")
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
            # Free tier - enforce 10 citation limit
            free_used_header = http_request.headers.get('X-Free-Used', '')

            # Decode base64 header if present (as per design spec)
            if free_used_header:
                try:
                    import base64
                    decoded_bytes = base64.b64decode(free_used_header)
                    free_used = int(decoded_bytes.decode('utf-8'))
                except (ValueError, TypeError, base64.binascii.Error, UnicodeDecodeError):
                    logger.warning(f"Invalid X-Free-Used header: {free_used_header}")
                    raise HTTPException(
                        status_code=400,  # Bad Request
                        detail=f"Invalid X-Free-Used header: {free_used_header}. Must be a base64-encoded non-negative integer."
                    )
            else:
                free_used = 0

            FREE_LIMIT = 10
            citation_count = len(results)
            affordable = max(0, FREE_LIMIT - free_used)

            logger.info(f"Free tier: used={free_used}, submitting={citation_count}, affordable={affordable}")

            if affordable == 0:
                # Already at limit - return empty partial results to show locked teaser
                logger.info("Free tier limit reached - returning empty partial results")
                return ValidationResponse(
                    results=[],
                    partial=True,
                    citations_checked=0,
                    citations_remaining=citation_count,
                    free_used=FREE_LIMIT,
                    free_used_total=FREE_LIMIT
                )
            elif affordable >= citation_count:
                # Under limit - return all results
                return ValidationResponse(
                    results=results,
                    free_used=free_used + citation_count,
                    free_used_total=free_used + citation_count
                )
            else:
                # Over limit - partial results (same as paid tier)
                return ValidationResponse(
                    results=results[:affordable],
                    partial=True,
                    citations_checked=affordable,
                    citations_remaining=citation_count - affordable,
                    free_used=FREE_LIMIT,  # Capped at limit
                    free_used_total=FREE_LIMIT  # Authoritative total for frontend sync
                )

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


async def process_validation_job(job_id: str, citations: str, style: str):
    """
    Background task to process validation.
    No HTTP timeout applies here.
    """
    try:
        # Update status
        jobs[job_id]["status"] = "processing"
        logger.info(f"Job {job_id}: Starting validation")

        # Check credits BEFORE starting job (fail fast)
        token = jobs[job_id]["token"]
        free_used = jobs[job_id]["free_used"]

        if token:
            user_credits = get_credits(token)
            if user_credits == 0:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "You have 0 Citation Credits remaining. Purchase more to continue."
                logger.warning(f"Job {job_id}: Failed - user has zero credits")
                return
        else:
            # Free tier - check limit
            if free_used >= FREE_LIMIT:
                # Return partial results with all citations locked (user can see upgrade prompt)
                # We need to call LLM just to count citations properly, but return empty results
                logger.info(f"Job {job_id}: Free tier limit reached, counting citations to show partial results")

                try:
                    validation_results = await llm_provider.validate_citations(
                        citations=citations,
                        style=style
                    )
                    citation_count = len(validation_results["results"])
                    logger.debug(f"Job {job_id}: Counted {citation_count} citations via LLM")
                except Exception as e:
                    logger.error(f"Job {job_id}: Failed to count citations: {str(e)}")
                    # Fallback: estimate by splitting on double newlines
                    citation_count = len([c.strip() for c in citations.split('\n\n') if c.strip()])
                    logger.debug(f"Job {job_id}: Fallback citation count: {citation_count}")

                jobs[job_id]["status"] = "completed"
                jobs[job_id]["results"] = ValidationResponse(
                    results=[],  # Empty array - all locked
                    partial=True,
                    citations_checked=0,
                    citations_remaining=citation_count,
                    free_used=FREE_LIMIT,
                    free_used_total=FREE_LIMIT
                ).model_dump()
                logger.info(f"Job {job_id}: Completed - free tier limit reached, returning locked partial results with {citation_count} remaining")
                return

        # Call LLM (can take 120s+)
        logger.info(f"Job {job_id}: Calling LLM provider")
        validation_results = await llm_provider.validate_citations(
            citations=citations,
            style=style
        )

        results = validation_results["results"]
        citation_count = len(results)
        jobs[job_id]["citation_count"] = citation_count

        # Handle credit/free tier logic (same as existing /api/validate)
        if not token:
            # Free tier
            affordable = max(0, FREE_LIMIT - free_used)

            if affordable >= citation_count:
                # Return all results
                jobs[job_id]["results"] = {
                    "results": results,
                    "free_used_total": free_used + citation_count
                }
            else:
                # Partial results
                jobs[job_id]["results"] = {
                    "results": results[:affordable],
                    "partial": True,
                    "citations_checked": affordable,
                    "citations_remaining": citation_count - affordable,
                    "free_used_total": FREE_LIMIT
                }
        else:
            # Paid tier
            user_credits = get_credits(token)

            if user_credits >= citation_count:
                # Can afford all
                success = deduct_credits(token, citation_count)
                if not success:
                    raise ValueError(f"Failed to deduct {citation_count} credits from user {token[:8]}...")

                jobs[job_id]["results"] = {
                    "results": results,
                    "credits_remaining": user_credits - citation_count
                }
            else:
                # Partial results
                affordable = user_credits
                success = deduct_credits(token, affordable)
                if not success:
                    raise ValueError(f"Failed to deduct {affordable} credits from user {token[:8]}...")

                jobs[job_id]["results"] = {
                    "results": results[:affordable],
                    "partial": True,
                    "citations_checked": affordable,
                    "citations_remaining": citation_count - affordable,
                    "credits_remaining": 0
                }

        jobs[job_id]["status"] = "completed"
        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {str(e)}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


async def cleanup_old_jobs():
    """Delete jobs older than 30 minutes."""
    import asyncio
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes

        now = time.time()
        threshold = 30 * 60  # 30 minutes

        jobs_to_delete = [
            job_id for job_id, job in jobs.items()
            if now - job["created_at"] > threshold
        ]

        for job_id in jobs_to_delete:
            del jobs[job_id]
            logger.info(f"Cleaned up old job: {job_id}")


@app.post("/api/validate/async")
async def validate_citations_async(http_request: Request, request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Create async validation job.

    Returns immediately with job_id.
    Background worker processes validation.
    """
    # Extract token/free_used from headers
    token = http_request.headers.get('X-User-Token')
    free_used_header = http_request.headers.get('X-Free-Used', '')

    try:
        free_used = int(base64.b64decode(free_used_header).decode('utf-8'))
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        free_used = 0

    # Validate input
    if not request.citations or not request.citations.strip():
        logger.warning("Empty citations submitted to async endpoint")
        raise HTTPException(status_code=400, detail="Citations cannot be empty")

    # Generate job ID
    job_id = str(uuid.uuid4())
    logger.info(f"Creating async job {job_id} for {'paid' if token else 'free'} user")

    # Create job entry
    jobs[job_id] = {
        "status": "pending",
        "created_at": time.time(),
        "results": None,
        "error": None,
        "token": token,
        "free_used": free_used,
        "citation_count": 0
    }

    # Convert HTML to text with formatting markers
    citations_text = html_to_text_with_formatting(request.citations)

    # Start background processing
    background_tasks.add_task(process_validation_job, job_id, citations_text, request.style)

    return {"job_id": job_id, "status": "pending"}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get job status and results.

    Returns:
    - pending: Still processing
    - processing: LLM call in progress
    - completed: Results ready
    - failed: Error occurred
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] == "completed":
        return {
            "status": "completed",
            "results": job["results"]
        }
    elif job["status"] == "failed":
        return {
            "status": "failed",
            "error": job["error"]
        }
    else:
        return {
            "status": job["status"]
        }


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
    logger.info(f"Request headers: {dict(request.headers)}")

    # Get signature from headers
    # Polar sends signature as 'webhook-signature' header (not 'X-Polar-Signature')
    signature = request.headers.get('webhook-signature')
    if not signature:
        logger.warning("Webhook received without signature header")
        logger.warning(f"Available headers: {list(request.headers.keys())}")
        return Response(status_code=401, content='{"error": "Invalid signature"}')

    logger.info(f"Signature header found: {signature[:20]}...")

    # Get raw body for signature verification
    body = await request.body()
    logger.info(f"Body received, length: {len(body)} bytes")
    logger.info(f"Body preview: {body[:200]}")

    webhook_secret = os.getenv('POLAR_WEBHOOK_SECRET')
    logger.info(f"Using webhook secret: {webhook_secret[:20]}...")

    try:
        # Verify webhook signature and parse payload
        logger.info("Calling validate_event...")
        webhook = validate_event(
            body=body,
            headers=dict(request.headers),
            secret=webhook_secret
        )

        # Determine event type from the webhook payload object
        from polar_sdk.models.webhookordercreatedpayload import WebhookOrderCreatedPayload
        from polar_sdk.models.webhookcheckoutupdatedpayload import WebhookCheckoutUpdatedPayload

        if isinstance(webhook, WebhookOrderCreatedPayload):
            logger.info("Webhook signature verified: order.created")
            await handle_order_created(webhook)
        elif isinstance(webhook, WebhookCheckoutUpdatedPayload):
            logger.info("Webhook signature verified: checkout.updated")
            await handle_checkout_updated(webhook)
        else:
            event_type = type(webhook).__name__
            logger.debug(f"Ignoring webhook event type: {event_type}")

        return Response(status_code=200)

    except WebhookVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
        return Response(status_code=401, content='{"error": "Invalid signature"}')
    except Exception as e:
        logger.error(f"Unexpected webhook processing error: {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e)}")
        return Response(status_code=500, content='{"error": "Internal server error"}')


async def handle_order_created(webhook):
    """Handle order.created webhook by granting credits."""
    from database import add_credits

    order_id = webhook.data.id
    # metadata is a dict, not an object
    token = webhook.data.metadata.get('token') if isinstance(webhook.data.metadata, dict) else webhook.data.metadata.token

    logger.info(f"Processing order.created: order_id={order_id}, token={token[:8] if token else 'None'}...")

    if not token:
        logger.error(f"Order {order_id} missing token in metadata")
        return

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
    # metadata is a dict, not an object
    token = webhook.data.metadata.get('token') if isinstance(webhook.data.metadata, dict) else webhook.data.metadata.token

    logger.info(f"Processing checkout.updated: order_id={order_id}, token={token[:8] if token else 'None'}...")

    if not token:
        logger.error(f"Checkout {order_id} missing token in metadata")
        return

    # Grant 1,000 credits (idempotent)
    success = add_credits(token, 1000, order_id)

    if success:
        logger.info(f"Successfully granted 1000 credits for completed checkout {order_id}")
    else:
        logger.warning(f"Checkout order {order_id} already processed, skipping credit grant")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
