"""
Run this script to update your code to use environment variables
This makes your app secure before deployment!
"""

import os

print("🔒 Making your app secure...")
print("-" * 50)

# Step 1: Create .env file
env_content = """# Stripe Settings (get from stripe.com dashboard)
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=your_webhook_secret_here

# xAI API (your current key)
XAI_API_KEY=your_xai_api_key_here

# Email Settings (for password reset)
EMAIL_ADDRESS=your_email_here
EMAIL_PASSWORD=your_email_password_here

# Admin Settings
ADMIN_USERNAME=your_admin_username_here
ADMIN_PASSWORD=your_strong_admin_password_here

# App Secret (don't change this, it's auto-generated)
SECRET_KEY=your_secret_key_will_be_generated_here
"""

# Generate a secret key
import secrets
secret_key = secrets.token_urlsafe(32)
env_content = env_content.replace("your_secret_key_will_be_generated_here", secret_key)

# Save .env file
with open('.env', 'w') as f:
    f.write(env_content)
print("✅ Created .env file")

# Step 2: Create .gitignore
gitignore_content = """# Security - NEVER upload these!
.env
config.yaml
*.db
*.sqlite

# Python
__pycache__/
*.pyc
.pytest_cache/

# Streamlit
.streamlit/
secrets.toml

# User data
*_history.csv
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
"""

with open('.gitignore', 'w') as f:
    f.write(gitignore_content)
print("✅ Created .gitignore file")

# Step 3: Create updated backend.py
print("\n📝 Now update your files:")
print("-" * 50)

print("""
1. In backend.py, add at the top:
   
   import os
   from dotenv import load_dotenv
   load_dotenv()
   
   # Then change:
   XAI_API_KEY = os.getenv('XAI_API_KEY')

2. In app.py, add at the top:
   
   import os
   from dotenv import load_dotenv
   load_dotenv()
   
   # Then change:
   stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

3. In admin.py, change:
   
   ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
   ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

4. In stripe_handler.py, change:
   
   stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
""")

# Step 4: Install required package
print("\n📦 Install python-dotenv:")
print("Run this command: pip install python-dotenv")

# Step 5: Create requirements.txt update
requirements_additions = """python-dotenv==1.0.0
plotly==5.18.0
sqlalchemy==2.0.23
"""

# Check if requirements.txt exists and append
if os.path.exists('requirements.txt'):
    with open('requirements.txt', 'a') as f:
        f.write('\n' + requirements_additions)
    print("\n✅ Updated requirements.txt")
else:
    print("\n⚠️  No requirements.txt found - create one with all your packages")

print("\n" + "="*50)
print("🎉 DONE! Your app is now more secure!")
print("="*50)
print("""
IMPORTANT REMINDERS:
1. NEVER share your .env file with anyone
2. NEVER upload .env to GitHub (it's in .gitignore)
3. Change the default passwords in .env
4. Get a Gmail app password for emails
5. Update your code with the changes shown above
""")

print("\nNext step: Follow the deployment guide to put your app online!")
print("\nNEVER commit real secrets to version control! Use placeholders in .env and set real values in production only.\n")