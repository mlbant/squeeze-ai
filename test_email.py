import os
import dotenv
from email_service import email_service

# Load environment variables
dotenv.load_dotenv()

def test_email_service():
    print("Testing email service...")
    print(f"SENDER_EMAIL: {os.getenv('SENDER_EMAIL')}")
    print(f"SENDER_APP_PASSWORD: {'*' * len(os.getenv('SENDER_APP_PASSWORD', '')) if os.getenv('SENDER_APP_PASSWORD') else 'NOT SET'}")
    print(f"SUPPORT_EMAIL: {email_service.support_email}")
    
    # Test sending a simple email
    try:
        result = email_service.send_contact_form_email(
            "Test User", 
            "test@example.com", 
            "Test Subject", 
            "This is a test message from the contact form.", 
            "Medium"
        )
        print(f"Email send result: {result}")
        return result
    except Exception as e:
        print(f"Error testing email: {str(e)}")
        return False

if __name__ == "__main__":
    test_email_service()