#!/bin/bash

# Kill any existing processes on ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Start Backend
echo "Starting Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
export TESTING=true
export MOCK_LLM=true
export PORT=8000
python3 database.py
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "Waiting for backend..."
sleep 5

# Start Frontend
echo "Starting Frontend..."
cd frontend/frontend
export VITE_MOCK_MODE=false
export VITE_API_URL=http://localhost:8000
npm run dev -- --port 5173 &
FRONTEND_PID=$!
cd ../..

# Wait for frontend
echo "Waiting for frontend..."
sleep 5

# Run Tests
echo "Running E2E Tests..."
cd frontend/frontend
npx playwright test tests/e2e/checkout/pricing_variants.spec.cjs
TEST_EXIT_CODE=$?

# Cleanup
echo "Cleaning up..."
kill $BACKEND_PID
kill $FRONTEND_PID

exit $TEST_EXIT_CODE
