#!/bin/bash

# Initialize database
python init_db.py || echo "DB init failed, continuing..."

# Set default port if PORT is not set
if [ -z "$PORT" ]; then
    export PORT=8501
fi

# Clear the problematic STREAMLIT_SERVER_PORT environment variable
unset STREAMLIT_SERVER_PORT

# Start streamlit with explicit port
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true