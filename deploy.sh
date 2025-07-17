#!/bin/bash

# Squeeze AI Deployment Script
# This script helps deploy the Squeeze AI application

set -e

echo "🚀 Squeeze AI Deployment Script"
echo "================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your production credentials."
    echo "See PRODUCTION_SETUP.md for details."
    exit 1
fi

# Check if required environment variables are set
required_vars=("STRIPE_SECRET_KEY" "XAI_API_KEY" "EMAIL_ADDRESS" "SECRET_KEY" "ADMIN_USERNAME" "ADMIN_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=your_" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing or placeholder values for required environment variables:"
    printf '%s\n' "${missing_vars[@]}"
    echo "Please update your .env file with actual production values."
    exit 1
fi

echo "✅ Environment variables check passed"

# Function to generate secure credentials
generate_credentials() {
    echo "🔐 Generating secure credentials..."
    
    # Generate secret key if not set
    if grep -q "^SECRET_KEY=your_secret_key_here" .env; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env
        echo "✅ Generated new SECRET_KEY"
    fi
    
    # Hash admin password if it's not already hashed
    if grep -q "^ADMIN_PASSWORD=[^$]" .env && ! grep -q "^ADMIN_PASSWORD=\$2b\$" .env; then
        echo "🔒 Hashing admin password..."
        ADMIN_PASS=$(grep "^ADMIN_PASSWORD=" .env | cut -d'=' -f2)
        HASHED_PASS=$(python3 -c "import bcrypt; print(bcrypt.hashpw('${ADMIN_PASS}'.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8'))")
        sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${HASHED_PASS}|" .env
        echo "✅ Admin password hashed"
    fi
}

# Function to initialize database
init_database() {
    echo "🗄️ Initializing database..."
    python3 database.py
    echo "✅ Database initialized"
}

# Function to test local setup
test_local() {
    echo "🧪 Testing local setup..."
    
    # Check if Python dependencies are installed
    if ! python3 -c "import streamlit" 2>/dev/null; then
        echo "📦 Installing Python dependencies..."
        pip3 install -r requirements.txt
    fi
    
    echo "✅ Dependencies check passed"
    
    # Test database connection
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('squeeze_ai.db')
    conn.close()
    print('✅ Database connection test passed')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"
}

# Function to deploy with Docker
deploy_docker() {
    echo "🐳 Deploying with Docker..."
    
    # Build and start containers
    docker-compose down
    docker-compose build
    docker-compose up -d
    
    echo "✅ Docker deployment completed"
    echo "🌐 Application should be available at http://localhost:8501"
}

# Function to deploy to cloud
deploy_cloud() {
    echo "☁️ Cloud deployment options:"
    echo "1. Streamlit Cloud (Recommended for beginners)"
    echo "2. Heroku"
    echo "3. AWS/GCP/Azure"
    echo "4. VPS/Dedicated Server"
    echo ""
    echo "Please refer to PRODUCTION_SETUP.md for detailed instructions."
}

# Main menu
show_menu() {
    echo ""
    echo "Please select deployment option:"
    echo "1. Generate secure credentials"
    echo "2. Initialize database"
    echo "3. Test local setup"
    echo "4. Deploy with Docker (local)"
    echo "5. Cloud deployment info"
    echo "6. Full local deployment (1+2+3+4)"
    echo "0. Exit"
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice [0-6]: " choice
    
    case $choice in
        1)
            generate_credentials
            ;;
        2)
            init_database
            ;;
        3)
            test_local
            ;;
        4)
            deploy_docker
            ;;
        5)
            deploy_cloud
            ;;
        6)
            echo "🚀 Starting full local deployment..."
            generate_credentials
            init_database
            test_local
            deploy_docker
            echo "🎉 Full deployment completed!"
            echo "🌐 Your Squeeze AI app is running at http://localhost:8501"
            break
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please try again."
            ;;
    esac
done
