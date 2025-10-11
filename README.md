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

## Project Structure
```
citations/
├── backend/       # FastAPI backend
├── frontend/      # React frontend
├── tests/         # Test files
├── docs/          # Documentation
└── logs/          # Application logs
```
