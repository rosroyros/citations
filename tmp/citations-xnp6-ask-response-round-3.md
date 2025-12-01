The issue is that gated responses clear the results array (`results: []`) instead of preserving citation data behind the gate. The reveal endpoint works fine, but users see "0 citations" because the frontend receives an empty results array.

**Immediate fix**: Comment out `response_data['results'] = []` in `backend/app.py:232`. This preserves the actual citation data while maintaining the gated overlay functionality. No frontend changes needed.
