#!/bin/bash

# Initialize database
python init_db.py || echo "DB init failed, continuing..."

# Set default port if PORT is not set
if [ -z "$PORT" ]; then
    export PORT=8501
fi

# Start streamlit
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true