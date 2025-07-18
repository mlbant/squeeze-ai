#!/usr/bin/env python3
import os
import subprocess
import sys

# Initialize database first
try:
    subprocess.run([sys.executable, "init_db.py"], check=False)
except:
    print("DB init failed, continuing...")

# Get port from environment or use default
port = os.environ.get('PORT', '8501')

# Clear problematic streamlit environment variables
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        del os.environ[key]

# Set the correct port environment variable
os.environ['STREAMLIT_SERVER_PORT'] = port
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Run streamlit
subprocess.run([
    sys.executable, '-m', 'streamlit', 'run', 'app.py'
])