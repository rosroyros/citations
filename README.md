# Citation Validator MVP

APA 7th edition citation validator using LLM.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. Run backend:
```bash
cd backend
python3 -m uvicorn app:app --reload
```

5. Run frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

## Recent Updates

### Validation UX Improvements (Nov 2025)

Enhanced citation validation experience to handle GPT-5-mini's 45-60 second latency:

**New Features:**
- Progressive loading state with text reveal animation
- Rotating status messages during validation
- Table-based results with expand/collapse functionality
- Invalid citations expanded by default for quick scanning
- Keyboard navigation (Tab, Enter, Space)
- Full accessibility support (ARIA, screen readers)
- Mobile responsive layout
- Smooth error state transitions

**Design Documentation:**
- Design spec: `docs/plans/2025-11-19-validation-latency-ux-design.md`
- Implementation: `docs/plans/2025-11-19-validation-latency-ux-implementation.md`
- Mockup: `docs/plans/validation-table-mockup.html`
- Component docs: `frontend/frontend/src/components/README.md`

**Key Components:**
- `ValidationLoadingState` - Progressive reveal with status messages
- `ValidationTable` - Interactive results table with expand/collapse

## Project Structure
```
citations/
├── backend/       # FastAPI backend
├── frontend/      # React frontend
│   └── src/
│       └── components/  # See README.md for component docs
├── tests/         # Test files
├── docs/          # Documentation and design specs
└── logs/          # Application logs
```
