"""
Quick debug script to test the API call hanging issue
"""
from dotenv import load_dotenv
import os
import openai
import time

load_dotenv('../backend/.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    exit(1)

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Test citation
test_citation = "Smith, J. (2023). _Article title_. Journal Name, 15(2), 123-145. https://doi.org/example"

prompt = f"""As an expert academic librarian specializing in citation validation, evaluate this citation according to APA 7th edition standards.

Consider:
- Required elements completeness (author, title, source, date)
- Format accuracy and consistency
- Source credibility and accessibility
- DOI/publisher information when applicable

Respond with exactly one word: "valid" or "invalid"

Citation: {test_citation}"""

print("🧪 Testing API call with reasoning_effort='minimal'...")
print(f"Prompt length: {len(prompt)} characters")

start_time = time.time()

try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        max_completion_tokens=10,
        temperature=1,
        reasoning_effort="minimal",
        messages=[{"role": "user", "content": prompt}]
    )

    end_time = time.time()
    predicted_text = response.choices[0].message.content.lower().strip()

    print(f"✅ API call successful!")
    print(f"Response: {predicted_text}")
    print(f"Duration: {end_time - start_time:.2f} seconds")

except Exception as e:
    end_time = time.time()
    print(f"❌ API call failed after {end_time - start_time:.2f} seconds")
    print(f"Error: {e}")