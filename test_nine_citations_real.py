"""Real test of 9 citations with actual OpenAI API."""
import asyncio
import httpx


async def test_nine_citations():
    """Test validating 9 citations through the API."""
    # The exact HTML from the logs
    html_input = """<p>Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. <em>Linguistics</em>, <em>51</em>(3), 473-515.</p><p>Agarwal, D., Naaman, M., &amp; Vashistha, A. (2025, April). AI suggestions homogenize writing toward western styles and diminish cultural nuances. In <em>Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems</em> (pp. 1-21).</p><p>Airoldi, M. (2021). <em>Machine habitus: Toward a sociology of algorithms</em>. John Wiley &amp; Sons.</p><p>Airoldi 2022</p><p>Ajunwa, I. (2020). The "black box" at work. <em>Big Data &amp; Society</em>, <em>7</em>(2), 2053951720966181.</p><p>Ajunwa, I. (2023). <em>The quantified worker: Law and technology in the modern workplace</em>. Cambridge University Press.</p><p>Alvero, A. J., Pal, J., &amp; Moussavian, K. M. (2022). Linguistic, cultural, and narrative capital: computational and human readings of transfer admissions essays. <em>Journal of Computational Social Science</em>, <em>5</em>(2), 1709-1734.</p><p>Alvero, A. J., Lee, J., Regla-Vargas, A., Kizilcec, R. F., Joachims, T., &amp; Antonio, A. L. (2024). Large language models, social demography, and hegemony: comparing authorship in human and synthetic text. <em>Journal of Big Data</em>, <em>11</em>(1), 138.</p><p>Angwin, J., Larson, J., Mattu, S. and Kirchner, L. (2016) 'Machine bias', ProPublica, 23 May 2016, <a target="_blank" rel="noopener noreferrer nofollow" href="https://bit.ly/2NubAFX">https://bit.ly/2NubAFX</a>.</p>"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/validate",
            json={
                "citations": html_input,
                "style": "apa7"
            },
            timeout=60.0
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✓ Received {len(results)} citation results")

            if len(results) == 9:
                print("✓ SUCCESS: All 9 citations were validated!")
                for i, result in enumerate(results, 1):
                    print(f"  Citation #{result['citation_number']}: {result['source_type']}")
                return True
            else:
                print(f"✗ FAIL: Expected 9 citations, got {len(results)}")
                print(f"  Citation numbers returned: {[r['citation_number'] for r in results]}")
                return False
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(response.text)
            return False


if __name__ == "__main__":
    success = asyncio.run(test_nine_citations())
    exit(0 if success else 1)
