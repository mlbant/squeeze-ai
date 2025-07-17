import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Test environment variable loading
stripe_key = os.getenv('STRIPE_SECRET_KEY')
print(f"Stripe key loaded: {stripe_key[:20]}..." if stripe_key else "Stripe key not found")

if stripe_key and stripe_key.startswith('sk_live_'):
    print("✅ Stripe key is properly configured")
else:
    print("❌ Stripe key is not properly configured")
    print(f"Current value: {stripe_key}")

# Test other important variables
print(f"Admin username: {os.getenv('ADMIN_USERNAME')}")
print(f"Secret key: {os.getenv('SECRET_KEY')[:20]}..." if os.getenv('SECRET_KEY') else "Secret key not found")
