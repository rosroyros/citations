Based on the help text you provided and the context I found, Oracle is a powerful AI tool that uses GPT-5 Pro/GPT-5.1 for analyzing code and file context. Here's how to craft the perfect Oracle response:

## Perfect Oracle Response Structure

**Project Briefing (2-4 sentences):**
- Stack: What technologies you're using
- Services/Architecture: Key components and how they interact  
- Build/Deployment: How to run and test the project

**Specific Question/Problem:**
- Clear statement of what you need help with
- What you've already tried
- Why this matters for your project

**Context:**
- Attach relevant files with `--file` flags
- Keep total input under ~196k tokens
- Prefer whole directories over single files

**Example perfect prompt:**
```bash
oracle --prompt "This is a Python Flask citation management app with a React frontend. The backend serves REST APIs from /api and the frontend builds to /dist. I'm getting a 500 error when trying to generate citations - the logs show 'KeyError: doi' in backend/app.py:342. I've tried checking the database schema and validating input but the error persists. This blocks the core citation generation feature. Can you analyze the citation generation flow and identify why the DOI field is missing?" --file backend/app.py --file frontend/src/ --file logs/
```

**Key tips:**
- 6-30 sentences total
- Specific error messages with line numbers
- What you've tried so far
- Business impact/why it matters
- Attach source files liberally
