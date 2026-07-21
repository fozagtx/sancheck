#!/bin/bash

# Start the landing page dev server
echo "Starting landing page on http://localhost:5173..."
cd /Users/kaizen/Desktop/seccheck
npm run dev &
LANDING_PID=$!

# Wait a bit for it to start
sleep 3

# Start the docs dev server
echo "Starting docs on http://localhost:3333/docs..."
cd /Users/kaizen/Desktop/seccheck/docs
npm run dev &
DOCS_PID=$!

echo ""
echo "✓ Both servers started!"
echo "  Landing page: http://localhost:5173"
echo "  Documentation: http://localhost:3333/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $LANDING_PID $DOCS_PID
