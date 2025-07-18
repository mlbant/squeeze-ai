#!/usr/bin/env python3
"""
Stripe Integration Test Script
Test your Stripe integration before going live
"""

import os
import sys
import dotenv
from stripe_handler import StripeHandler

# Load environment variables
dotenv.load_dotenv()

def test_stripe_setup():
    """Test basic Stripe setup"""
    print("Testing Stripe Integration")
    print("=" * 50)
    
    # Check environment variables
    stripe_secret = os.getenv('STRIPE_SECRET_KEY')
    stripe_public = os.getenv('STRIPE_PUBLISHABLE_KEY')
    
    print(f"Stripe Secret Key: {'sk_test_' in stripe_secret if stripe_secret else 'NOT FOUND'}")
    print(f"Stripe Public Key: {'pk_test_' in stripe_public if stripe_public else 'NOT FOUND'}")
    
    if not stripe_secret or not stripe_public:
        print("ERROR: Stripe keys not found in environment")
        print("Make sure your .env file contains:")
        print("STRIPE_SECRET_KEY=sk_test_...")
        print("STRIPE_PUBLISHABLE_KEY=pk_test_...")
        return False
    
    # Test Stripe handler
    try:
        handler = StripeHandler()
        print("StripeHandler initialized successfully")
        
        # Test checkout session creation
        session = handler.create_checkout_session(
            user_id=999,  # Test user ID
            email="test@example.com",
            success_url="http://localhost:8501?test=success",
            cancel_url="http://localhost:8501?test=cancel"
        )
        
        if session:
            print("Checkout session created successfully")
            print(f"Session URL: {session.url}")
            print(f"Session ID: {session.id}")
            print("\nSUCCESS! Your Stripe integration is working!")
            print("\nNext steps:")
            print("1. Copy the session URL above")
            print("2. Open it in your browser")
            print("3. Use test card: 4242424242424242")
            print("4. Use any future date and CVC")
            print("5. Complete the test payment")
            
            return True
        else:
            print("ERROR: Failed to create checkout session")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def print_test_cards():
    """Print test card information"""
    print("\nSTRIPE TEST CARDS")
    print("=" * 50)
    print("SUCCESS CARDS:")
    print("   Visa: 4242424242424242")
    print("   Visa (debit): 4000056655665556")
    print("   Mastercard: 5555555555554444")
    print("   American Express: 378282246310005")
    print("\nDECLINE CARDS:")
    print("   Generic decline: 4000000000000002")
    print("   Insufficient funds: 4000000000009995")
    print("   Lost card: 4000000000009987")
    print("\nTEST DETAILS:")
    print("   Expiry: Any future date (e.g., 12/25)")
    print("   CVC: Any 3-digit number (e.g., 123)")
    print("   ZIP: Any 5-digit number (e.g., 12345)")

if __name__ == "__main__":
    print("SQUEEZE AI - STRIPE TEST SUITE")
    print("=" * 50)
    
    success = test_stripe_setup()
    print_test_cards()
    
    if success:
        print("\nREADY TO TEST!")
        print("Run: streamlit run app.py")
        print("Then try to upgrade to Pro using the test cards above")
        sys.exit(0)
    else:
        print("\nSETUP INCOMPLETE")
        print("Fix the errors above before testing")
        sys.exit(1)