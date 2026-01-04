#!/usr/bin/env python3
"""Test full ValidationResponse conversion like app.py does."""

import os
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from dotenv import load_dotenv
load_dotenv('/Users/roy/Documents/Projects/citations/backend/.env')

# Get raw provider result
from providers.gemini_provider import GeminiProvider
import asyncio

CITATION = 'Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84'

async def get_raw_result():
    provider = GeminiProvider()
    result = await provider.validate_citations(citations=CITATION, style="chicago17")
    return result["results"]

results = asyncio.run(get_raw_result())

print("="*60)
print("RAW RESULTS FROM PROVIDER:")
print("="*60)
print(f"Number of results: {len(results)}")
for r in results:
    print(f"  errors: {r.get('errors')}")

# Build response_data like app.py line 1066
response_data = {
    "results": results,
    "free_used_total": 1,
    "limit_type": "none"
}

print("\n" + "="*60)
print("BUILDING ValidationResponse LIKE APP.PY:")
print("="*60)

from pydantic import BaseModel
from typing import Optional, List

# Copy exact models from app.py
class CitationError(BaseModel):
    component: str
    problem: str
    correction: str

class CitationResult(BaseModel):
    citation_number: int
    original: str
    source_type: str
    errors: list[CitationError]
    corrected_citation: Optional[str] = None

class UserStatus(BaseModel):
    type: str
    days_remaining: Optional[int] = None
    daily_used: Optional[int] = None
    daily_limit: Optional[int] = None
    reset_time: Optional[int] = None
    hours_remaining: Optional[float] = None
    pass_product_name: Optional[str] = None
    balance: Optional[int] = None
    validations_used: Optional[int] = None
    limit: Optional[int] = None

class ValidationResponse(BaseModel):
    results: list[CitationResult]
    partial: bool = False
    citations_checked: Optional[int] = None
    citations_remaining: Optional[int] = None
    credits_remaining: Optional[int] = None
    free_used: Optional[int] = None
    free_used_total: Optional[int] = None
    results_gated: Optional[bool] = None
    job_id: Optional[str] = None
    user_status: Optional[UserStatus] = None
    limit_type: Optional[str] = None
    experiment_variant: Optional[str] = None

try:
    response = ValidationResponse(**response_data)
    print("SUCCESS! ValidationResponse created.")
    print(f"Number of results: {len(response.results)}")
    for res in response.results:
        print(f"  Citation #{res.citation_number}:")
        print(f"    errors count: {len(res.errors)}")
        print(f"    errors: {res.errors}")
    
    # Now call model_dump() like line 1155
    dumped = response.model_dump()
    print("\n" + "="*60)
    print("AFTER model_dump():")
    print("="*60)
    print(f"dumped['results'][0]['errors']: {dumped['results'][0]['errors']}")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
