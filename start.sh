#!/bin/bash

# Initialize database
python init_db.py || echo "DB init failed, continuing..."

# Set default port if PORT is not set
if [ -z "$PORT" ]; then
    export PORT=8501
fi

# Create Streamlit config with the correct port
mkdir -p .streamlit
cat > .streamlit/config.toml << EOF
[server]
port = $PORT
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
EOF

# Clear problematic environment variables
export STREAMLIT_SERVER_PORT=""
export STREAMLIT_SERVER_ADDRESS=""

# Start streamlit without port arguments (use config file)
streamlit run app.py