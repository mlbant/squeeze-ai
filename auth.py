import streamlit as st
from database import UserDatabase
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import re

class Authentication:
    def __init__(self):
        self.db = UserDatabase()
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        return True, "Password is strong"
    
    def login(self):
        """Display login form"""
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    result = self.db.verify_user(username, password)
                    if result['success']:
                        st.session_state.authenticated = True
                        st.session_state.user_id = result['user_id']
                        st.session_state.username = username
                        st.session_state.full_name = result['full_name']
                        st.session_state.email = result['email']
                        
                        # Check subscription
                        sub = self.db.get_user_subscription(result['user_id'])
                        st.session_state.subscription = sub
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result['error'])
                else:
                    st.error("Please enter both username and password")
    
    def register(self):
        """Display registration form"""
        with st.form("register_form"):
            st.subheader("Create Account")
            
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name")
                username = st.text_input("Username")
            with col2:
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
            
            confirm_password = st.text_input("Confirm Password", type="password")
            terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submit = st.form_submit_button("Create Account")
            
            if submit:
                # Validate inputs
                errors = []
                
                if not all([full_name, username, email, password]):
                    errors.append("All fields are required")
                
                if not self.validate_email(email):
                    errors.append("Invalid email format")
                
                valid_password, msg = self.validate_password(password)
                if not valid_password:
                    errors.append(msg)
                
                if password != confirm_password:
                    errors.append("Passwords do not match")
                
                if not terms:
                    errors.append("You must agree to the terms")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Create user
                    result = self.db.create_user(username, email, password, full_name)
                    if result['success']:
                        st.success("Account created successfully! Please check your email to verify your account.")
                        # Send verification email
                        self.send_verification_email(email, result['verification_token'])
                    else:
                        st.error(result['error'])
    
    def forgot_password(self):
        """Password reset functionality"""
        with st.form("forgot_password_form"):
            st.subheader("Reset Password")
            email = st.text_input("Enter your email address")
            submit = st.form_submit_button("Send Reset Link")
            
            if submit and email:
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                # In production, save this token to database with expiry
                
                # Send reset email
                self.send_reset_email(email, reset_token)
                st.success("Password reset link sent to your email!")
    
    def send_verification_email(self, email, token):
        """Send email verification"""
        # In production, use proper email service
        verification_link = f"http://localhost:8501/?verify={token}"
        
        subject = "Verify your Squeeze AI account"
        body = f"""
        Welcome to Squeeze AI!
        
        Please verify your email address by clicking the link below:
        {verification_link}
        
        This link will expire in 24 hours.
        
        Best regards,
        Squeeze AI Team
        """
        
        # Send email (implement with your SMTP settings)
        st.info(f"Verification email would be sent to {email}")
    
    def send_reset_email(self, email, token):
        """Send password reset email"""
        reset_link = f"http://localhost:8501/?reset={token}"
        
        subject = "Reset your Squeeze AI password"
        body = f"""
        You requested a password reset for your Squeeze AI account.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Squeeze AI Team
        """
        
        # Send email (implement with your SMTP settings)
        st.info(f"Reset email would be sent to {email}")
    
    def logout(self):
        """Logout user"""
        for key in ['authenticated', 'user_id', 'username', 'full_name', 'email', 'subscription']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Session management
def require_auth():
    """Decorator to require authentication"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("Please login to access this feature")
        st.stop()

def require_pro():
    """Decorator to require pro subscription"""
    require_auth()
    if not st.session_state.subscription or st.session_state.subscription['plan_type'] != 'pro':
        st.warning("This feature requires a Pro subscription")
        if st.button("Upgrade to Pro"):
            st.switch_page("pages/upgrade.py")
        st.stop()