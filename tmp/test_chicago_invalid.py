#!/usr/bin/env python3
"""Quick test of 10 invalid Chicago citations against the API."""

import requests
import time
import json

API_URL = "http://localhost:8000"

# 10 invalid citations from golden set with their error types
INVALID_CITATIONS = [
    {
        "citation": 'Lobb, R. L. "Military Rations." In _Encyclopedia of Food and Culture_, edited by Solomon H. Katz and William Woys Weaver, 2:159–60. New York: Charles Scribner\'s Sons, 2003.',
        "error_type": "author_initials"
    },
    {
        "citation": 'Idle, Eric. "Just a Flesh Wound." _Hamster Moms_ (blog). June 25, 2014. Retrieved from http://omgitsadeadparrot.com/2014/06/25/hamstermoms.',
        "error_type": "retrieved_from"
    },
    {
        "citation": 'Li, Lillian. Nothing Is More American Than Chinese Food on Christmas. _New York Times (Online)_, December 25, 2018. ProQuest.',
        "error_type": "missing_quotes"
    },
    {
        "citation": 'Rodriguez, Richard. "Aria: A Memoir of a Bilingual Childhood." In _The Best American Essays of the Century_, edited by Joyce Carol Oates. Boston: Houghton Mifflin Co., 2000.',
        "error_type": "missing_page_range"
    },
    {
        "citation": '"Illinois Governor Wants to \'Fumigate\' State\'s Government." _CNN_ online. January 30, 2009. https://edition.cnn.com/2009/POLITICS/01/30/illinois.governor.quinn/',
        "error_type": "missing_period"
    },
    {
        "citation": 'Nye, Bill (@BillNye). "While I\'m not much for skipping school, I sure am in favor of calling attention to the seriousness of climate change..." Twitter, March 14, 2019. Retrieved from https://twitter.com/BillNye/status/1106242216123486209.',
        "error_type": "retrieved_from"
    },
    {
        "citation": 'Bouman, Katie. "How to Take a Picture of a Black Hole." Filmed November 2016 at TEDxBeaconStreet, Brookline, MA. Video, 12:51. Retrieved from https://www.ted.com/talks/katie_bouman_what_does_a_black_hole_look_like.',
        "error_type": "retrieved_from"
    },
    {
        "citation": 'Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84',
        "error_type": "missing_period"
    },
    {
        "citation": 'Pérez, Patricia A, ed. _The Tenure-Track Process for Chicana & Latina Faculty: Experiences of Resisting and Persisting in the Academy_. New York: Routledge, 2019. https://doi.org/10.4324/9780429275784.',
        "error_type": "ampersand"
    },
    {
        "citation": 'Bundy, McGeorge: Interview by Robert MacNeil. _MacNeil/Lehrer NewsHour_. PBS. February 7, 1990.',
        "error_type": "colon_after_author"
    },
]

def test_citation(citation_data):
    """Test a single citation and return result."""
    citation = citation_data["citation"]
    error_type = citation_data["error_type"]
    
    # Submit job
    response = requests.post(
        f"{API_URL}/api/validate/async",
        json={"citations": citation, "style": "chicago17"}
    )
    job_id = response.json().get("job_id")
    
    if not job_id:
        return {"error_type": error_type, "status": "failed_to_submit", "detected": False}
    
    # Poll for result
    for _ in range(30):
        time.sleep(1)
        result = requests.get(f"{API_URL}/api/jobs/{job_id}")
        data = result.json()
        if data.get("status") == "completed":
            results = data.get("results", {}).get("results", [])
            if results:
                errors = results[0].get("errors", [])
                detected = len(errors) > 0
                return {
                    "error_type": error_type,
                    "detected": detected,
                    "errors_found": errors[:1] if errors else [],
                    "citation_short": citation[:60] + "..."
                }
            break
    
    return {"error_type": error_type, "status": "timeout", "detected": False}

def main():
    print("Testing 10 invalid Chicago citations...")
    print("=" * 60)
    
    results = []
    detected_count = 0
    
    for i, citation_data in enumerate(INVALID_CITATIONS, 1):
        print(f"[{i}/10] Testing {citation_data['error_type']}...", end=" ", flush=True)
        result = test_citation(citation_data)
        results.append(result)
        
        if result.get("detected"):
            print("✅ DETECTED")
            detected_count += 1
        else:
            print("❌ MISSED")
    
    print("=" * 60)
    print(f"\nRESULTS: {detected_count}/10 errors detected ({detected_count * 10}%)")
    print("\nDetailed results:")
    
    for r in results:
        status = "✅" if r.get("detected") else "❌"
        print(f"  {status} {r['error_type']}: {'Found' if r.get('detected') else 'Missed'}")
        if r.get("errors_found"):
            print(f"      → {r['errors_found'][0][:80]}...")

if __name__ == "__main__":
    main()
