You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-xnp6

Oracle previously recommended: "Simplify to frontend-only tracking using GA4 events, eliminating database dependencies entirely while maintaining the engagement measurement capability."

### Current Problem:
Despite our fixes (commits 16bdd1b, b587ba6), production users still report seeing 0 citations after clicking reveal, though our testing shows success.

### Specific Technical Questions:

1. **Frontend-Only Implementation**: Should we eliminate the `/api/reveal-results` endpoint and handle reveals purely client-side?

2. **Production Debugging**: What's the most likely cause of users seeing 0 citations when our API testing shows results (9 citations) working?

3. **Immediate Fix**: What's the minimal change needed to resolve the production issue right now?

Please provide specific technical guidance for implementation approach.

