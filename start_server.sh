#!/bin/bash
# Start the Flask development server on Linux/Mac

echo "Starting SP Backend Server..."
echo ""

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo ""
echo "========================================"
echo "Starting Flask server on localhost:5000"
echo "========================================"
echo ""
echo "API will be available at: http://localhost:5000"
echo "API documentation: See README.md"
echo ""
echo "To stop the server, press Ctrl+C"
echo ""

python app.py
