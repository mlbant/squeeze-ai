import streamlit as st
from backend import get_squeeze_stocks, get_single_squeeze_score, get_historical_data
import stripe
import altair as alt
import pandas as pd
import random
import csv
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import dotenv
import hashlib
import time
import bcrypt
import yfinance as yf
from email_service import email_service
from postgresql_auth import authenticator
from stripe_handler import StripeHandler
from subscription_handler import SubscriptionHandler
from session_manager import session_manager
dotenv.load_dotenv()

# Initialize subscription handler
subscription_handler = SubscriptionHandler()

# Stripe key (test mode)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Stripe handler
stripe_handler = StripeHandler()

# Get current domain for URLs
def get_current_domain():
    """Get current domain for Stripe URLs"""
    # Check environment variable first
    if os.getenv('ENVIRONMENT') == 'production':
        return 'https://squeeze-ai.com'
    # Check if we're on Render
    elif os.getenv('RENDER'):
        return 'https://squeeze-ai.onrender.com'
    # Default to localhost for development
    else:
        return 'http://localhost:8501'

def get_user_email():
    """Get the user's actual email address from their account"""
    # First try to get email from session state
    email = st.session_state.get('email', '')
    if email:
        return email
    
    # Get the user's actual email from the database
    username = st.session_state.get('username', '')
    if username:
        try:
            user = authenticator.get_user_by_username(username)
            if user and hasattr(user, 'email') and user.email:
                return user.email
        except:
            pass
    
    # Final fallback if no email found
    return "user@example.com"

# Page config
st.set_page_config(
    page_title="Squeeze Ai - Stock Squeeze Analysis", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# PostgreSQL authentication is now imported from postgresql_auth
# No need to load config.yaml anymore - using persistent database

# Enhanced dark mode styling
st.markdown("""
<style>
    .main { 
        background-color: #0e1117; 
        color: #fafafa; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stButton > button { 
        background-color: #00D564; 
        color: #0e1117; 
        border: none; 
        border-radius: 8px; 
        padding: 0.5rem 1.5rem; 
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #00E56F;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 213, 100, 0.3);
    }
    .stSelectbox > div, .stTextInput > div > div > input { 
        background-color: #1f2937; 
        color: #fafafa;
        border-radius: 8px; 
        border: 1px solid #374151;
    }
    small { 
        color: #9ca3af; 
        font-size: 0.875rem; 
    }
    h1, h2, h3 { 
        color: #00D564; 
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: transparent;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f2937;
        color: #00D564;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 1rem;
    }
    .disclaimer-box {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
    }
    .stock-card {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .stock-card:hover {
        border-color: #00D564;
        box-shadow: 0 4px 12px rgba(0, 213, 100, 0.1);
    }
    .login-button {
        width: 200px !important;
        margin: 0 auto !important;
        display: block !important;
    }
    /* Delete button styling */
    .delete-button > button {
        background-color: #dc2626 !important;
        color: #ffffff !important;
        border: 1px solid #dc2626 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .delete-button > button:hover {
        background-color: #b91c1c !important;
        border-color: #b91c1c !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(220, 38, 38, 0.3) !important;
    }
    .delete-button > button:focus {
        background-color: #b91c1c !important;
        border-color: #b91c1c !important;
        box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to get browser fingerprint
def get_browser_fingerprint():
    """Create a browser fingerprint using JavaScript"""
    fingerprint_js = """
    <script>
    function getBrowserFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Browser fingerprint', 2, 2);
        
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset(),
            canvas.toDataURL()
        ].join('|');
        
        const hash = fingerprint.split('').reduce((a,b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        return Math.abs(hash).toString();
    }
    
    const fingerprint = getBrowserFingerprint();
    window.parent.postMessage({type: 'fingerprint', value: fingerprint}, '*');
    </script>
    """
    return fingerprint_js

# Function to check guest usage limits
def check_guest_limits():
    """Check if guest has exceeded usage limits using browser fingerprinting"""
    # Create a simple fingerprint based on user agent and screen info
    # This is a basic implementation - in production you'd want more sophisticated fingerprinting
    import hashlib
    
    # Get basic browser info (this is a simplified approach)
    # In a real implementation, you'd use JavaScript to get more detailed fingerprinting
    user_agent = st.context.headers.get("user-agent", "unknown")
    
    # Create a hash of the user agent as a simple fingerprint
    fingerprint = hashlib.md5(user_agent.encode()).hexdigest()[:16]
    
    # Check if usage files exist for this fingerprint
    scan_file = f"guest_scan_{fingerprint}.txt"
    search_file = f"guest_search_{fingerprint}.txt"
    
    scan_used = os.path.exists(scan_file)
    search_used = os.path.exists(search_file)
    
    return scan_used, search_used, fingerprint

# Function to mark guest usage
def mark_guest_usage(fingerprint, usage_type):
    """Mark that guest has used a feature"""
    if usage_type == "scan":
        with open(f"guest_scan_{fingerprint}.txt", "w") as f:
            f.write(str(time.time()))
    elif usage_type == "search":
        with open(f"guest_search_{fingerprint}.txt", "w") as f:
            f.write(str(time.time()))

# Initialize session state and check guest limits
if "guest_scan_used" not in st.session_state:
    st.session_state.guest_scan_used = False
if "guest_search_used" not in st.session_state:
    st.session_state.guest_search_used = False
if "free_scan_used" not in st.session_state:
    st.session_state.free_scan_used = False
if "free_search_used" not in st.session_state:
    st.session_state.free_search_used = False

# Check guest usage limits on page load
try:
    scan_used, search_used, fingerprint = check_guest_limits()
    if scan_used:
        st.session_state.guest_scan_used = True
    if search_used:
        st.session_state.guest_search_used = True
    st.session_state.browser_fingerprint = fingerprint
except:
    # Fallback if fingerprinting fails
    st.session_state.browser_fingerprint = "fallback"

# Initialize session state for authentication if not already set
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = False
if "name" not in st.session_state:
    st.session_state.name = None
if "username" not in st.session_state:
    st.session_state.username = None

# Database-backed session persistence
import json
import time

# Initialize session ID from query params or cookies
if 'session_id' not in st.session_state:
    # Check for session ID in query params
    session_id = st.query_params.get('session_id')
    if session_id:
        st.session_state.session_id = session_id
    else:
        st.session_state.session_id = None

def save_session(username):
    """Save session to database"""
    try:
        session_data = {
            'username': username,
            'name': username,  # Use username as name for now
            'email': st.session_state.get('email', None),
            'subscribed': st.session_state.get('subscribed', False),
            'subscription_cancelled': st.session_state.get('subscription_cancelled', False),
            'subscription_start_date': st.session_state.get('subscription_start_date', None),
            'last_scan_results': st.session_state.get('last_scan_results', None),
            'last_scan_filters': st.session_state.get('last_scan_filters', None),
            'last_analysis_result': st.session_state.get('last_analysis_result', None),
            'last_analysis_ticker': st.session_state.get('last_analysis_ticker', None),
            'last_analysis_period': st.session_state.get('last_analysis_period', None),
            'free_scan_used': st.session_state.get('free_scan_used', False),
            'free_search_used': st.session_state.get('free_search_used', False),
            'portfolio_holdings': st.session_state.get('portfolio_holdings', [])
        }
        
        if st.session_state.get('session_id'):
            # Update existing session
            success = session_manager.update_session(st.session_state.session_id, session_data)
        else:
            # Create new session
            session_id = session_manager.create_session(username, session_data)
            if session_id:
                st.session_state.session_id = session_id
                # Add session ID to URL for persistence
                st.query_params['session_id'] = session_id
    except Exception as e:
        pass

def load_session():
    """Load session from database"""
    try:
        session_id = st.session_state.get('session_id')
        if not session_id:
            return None
            
        session_info = session_manager.get_session(session_id)
        
        if session_info:
            # Check if user exists in PostgreSQL
            if authenticator.get_user_by_username(session_info['username']):
                # Merge session data
                session_data = session_info['session_data']
                session_data['username'] = session_info['username']
                return session_data
            else:
                # Invalidate session
                session_manager.invalidate_session(session_id)
    except Exception as e:
        pass
    return None

def clear_session():
    """Clear session from database"""
    try:
        session_id = st.session_state.get('session_id')
        if session_id:
            session_manager.invalidate_session(session_id)
            st.session_state.session_id = None
            # Clear session ID from URL
            if 'session_id' in st.query_params:
                del st.query_params['session_id']
    except:
        pass

# Check for existing session on page load (always check for persistence)
session_data = load_session()

# Check if there's a mismatch between authenticated and authentication_status
if st.session_state.get('authenticated') and not st.session_state.get('authentication_status'):
    st.session_state.authentication_status = True

# Check if user is actually logged in but authentication_status is wrong
if st.session_state.get('username') and st.session_state.get('username') != 'Not set':
    # Fix authentication_status if it's wrong
    if not st.session_state.get('authentication_status'):
        st.session_state.authentication_status = True
    
    # Force save session
    save_session(st.session_state.username)

# Safe session restoration with proper None checks
if session_data and isinstance(session_data, dict):
    if not st.session_state.get('authentication_status', False):
        st.session_state.authentication_status = True
        st.session_state.authenticated = True  # Also set authenticated flag
        st.session_state.username = session_data.get('username', 'Unknown')
        st.session_state.name = session_data.get('name', session_data.get('username', 'User'))
    
    # Always restore subscription status if available
    if 'subscribed' not in st.session_state:
        st.session_state.subscribed = session_data.get('subscribed', False)
    
    # Restore subscription cancellation status
    if 'subscription_cancelled' not in st.session_state:
        st.session_state.subscription_cancelled = session_data.get('subscription_cancelled', False)
    
    # Restore subscription start date
    if 'subscription_start_date' not in st.session_state:
        st.session_state.subscription_start_date = session_data.get('subscription_start_date', None)
    
    # Restore user email
    if 'email' not in st.session_state or not st.session_state.email:
        st.session_state.email = session_data.get('email', None)
    
    # Restore scan and analysis results
    if 'last_scan_results' not in st.session_state:
        st.session_state.last_scan_results = session_data.get('last_scan_results', None)
    if 'last_scan_filters' not in st.session_state:
        st.session_state.last_scan_filters = session_data.get('last_scan_filters', None)
    if 'last_analysis_result' not in st.session_state:
        st.session_state.last_analysis_result = session_data.get('last_analysis_result', None)
    if 'last_analysis_ticker' not in st.session_state:
        st.session_state.last_analysis_ticker = session_data.get('last_analysis_ticker', None)
    if 'last_analysis_period' not in st.session_state:
        st.session_state.last_analysis_period = session_data.get('last_analysis_period', None)
    
    # Restore free usage limits and portfolio
    if 'free_scan_used' not in st.session_state:
        st.session_state.free_scan_used = session_data.get('free_scan_used', False)
    if 'free_search_used' not in st.session_state:
        st.session_state.free_search_used = session_data.get('free_search_used', False)
    if 'portfolio_holdings' not in st.session_state:
        st.session_state.portfolio_holdings = session_data.get('portfolio_holdings', [])
else:
    # Initialize default values when no session exists
    if 'subscribed' not in st.session_state:
        st.session_state.subscribed = False
    if 'last_analysis_period' not in st.session_state:
        st.session_state.last_analysis_period = None
    # Initialize free usage limits with default values
    if 'free_scan_used' not in st.session_state:
        st.session_state.free_scan_used = False
    if 'free_search_used' not in st.session_state:
        st.session_state.free_search_used = False
    
    # Initialize portfolio holdings
    if 'portfolio_holdings' not in st.session_state:
        st.session_state.portfolio_holdings = []

# Initialize subscribed status if not set by session loading
if 'subscribed' not in st.session_state:
    st.session_state.subscribed = False

# Check for URL parameters for navigation
query_params = st.query_params

# Handle successful subscription from Stripe redirect
if 'subscribed' in query_params and query_params['subscribed'] == 'true':
    # Check if we have a user session ID in the URL
    if 'user_session' in query_params:
        # Restore session ID, clean it from Stripe's appended session_id
        raw_session_id = query_params['user_session']
        # Split at '?session_id=' to remove Stripe's checkout session ID
        clean_session_id = raw_session_id.split('?session_id=')[0] if '?session_id=' in raw_session_id else raw_session_id
        st.session_state.session_id = clean_session_id
        
        # Load session data
        session_data = load_session()
        
        if session_data:
            # Restore authentication
            st.session_state.authentication_status = True
            st.session_state.authenticated = True
            st.session_state.username = session_data['username']
            st.session_state.name = session_data.get('name', session_data.get('username', 'User'))
            
            # Activate subscription
            st.session_state.subscribed = True
            # Store subscription start date for proper billing calculation
            st.session_state.subscription_start_date = pd.Timestamp.now().isoformat()
            
            # Save updated session with subscription status
            save_session(st.session_state.username)
            
            st.success("🎉 Welcome to Squeeze AI Pro! Your 14-day free trial has started.")
            st.info("✅ You now have access to all premium features!")
            
            # Clear URL parameters but keep session_id
            st.query_params.clear()
            st.query_params['session_id'] = st.session_state.session_id
            
            time.sleep(2)  # Give user time to see the message
            st.rerun()
        else:
            st.error("Session expired. Please log in again to activate your subscription.")
    else:
        st.error("Session lost. Please log in again to activate your subscription.")

if 'page' in query_params:
    page = query_params['page']
    if page == 'terms':
        st.query_params.clear()
        st.switch_page("pages/terms.py")
    elif page == 'privacy':
        st.query_params.clear()
        st.switch_page("pages/privacy.py")
    elif page == 'contact':
        st.query_params.clear()
        st.switch_page("pages/contact.py")

# Check for password reset token in URL parameters
if 'reset_token' in query_params:
    reset_token = query_params['reset_token']
    
    # Validate token exists in database
    try:
        from database_config import get_db, ResetToken
        from datetime import datetime
        db = next(get_db())
        token_exists = db.query(ResetToken).filter(ResetToken.token == reset_token).first()
        
        if token_exists:
            current_time = datetime.utcnow()
            token_valid = not token_exists.used and token_exists.expires_at > current_time
        else:
            token_valid = False
            
        db.close()
    except Exception as e:
        st.error("Database connection error. Please try again later.")
        st.stop()
    
    # Password reset form
    st.markdown("## Reset Your Password")
    st.markdown("Enter your new password below:")
    
    # Initialize success state
    if 'password_reset_success' not in st.session_state:
        st.session_state.password_reset_success = False
    
    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Reset Password"):
            if new_password and confirm_password:
                if new_password == confirm_password:
                    if len(new_password) >= 6:
                        # Use direct password reset if token is valid
                        if token_valid and token_exists:
                            try:
                                from database_config import get_db, User
                                from datetime import datetime
                                
                                db = next(get_db())
                                user = db.query(User).filter(User.username == token_exists.username).first()
                                
                                if user:
                                    # Update password using the authenticator's hash method
                                    user.password_hash = authenticator.hash_password(new_password)
                                    user.updated_at = datetime.utcnow()
                                    
                                    # Mark token as used
                                    token_exists.used = True
                                    
                                    db.commit()
                                    db.close()
                                    
                                    st.session_state.password_reset_success = True
                                    st.success("✅ Password reset successful!")
                                    st.info("You can now log in with your new password.")
                                else:
                                    st.error("User not found.")
                            except Exception as e:
                                st.error(f"Password reset failed: {str(e)}")
                        else:
                            st.error("❌ Password reset failed. The token may be expired or invalid.")
                            st.info("Please request a new password reset link if needed.")
                    else:
                        st.error("Password must be at least 6 characters long.")
                else:
                    st.error("Passwords don't match.")
            else:
                st.error("Please fill in both password fields.")
    
    # Show back to homepage button (outside the form)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.session_state.password_reset_success:
            # Show primary button after successful reset
            if st.button("🏠 Back to Homepage", type="primary", use_container_width=True):
                # Clear the reset token from URL and redirect to homepage
                st.query_params.clear()
                st.session_state.password_reset_success = False
                st.rerun()
        else:
            # Show secondary button before reset
            if st.button("← Back to Homepage", type="secondary", use_container_width=True):
                st.query_params.clear()
                st.session_state.password_reset_success = False
                st.rerun()
    
    st.stop()

# Password reset section complete - continue with main app

# Initialize free usage limits if not set by session loading (only when no session data exists)
if not session_data:
    if 'free_scan_used' not in st.session_state:
        st.session_state.free_scan_used = False
    if 'free_search_used' not in st.session_state:
        st.session_state.free_search_used = False
else:
    # Session data exists, make sure we have default values
    if 'free_scan_used' not in st.session_state:
        st.session_state.free_scan_used = False
    if 'free_search_used' not in st.session_state:
        st.session_state.free_search_used = False

# If not authenticated, show login/sign up
if not authenticator.is_authenticated():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Squeeze-Ai.com 🚀")
        st.markdown("### Ai Powered Short Squeeze Tool")
        st.markdown("Identify high-potential squeeze opportunities with advanced metrics")
        
    tab_login, tab_signup, tab_guest = st.tabs(["Login", "Sign Up", "Try as Guest"])

    with tab_login:
        st.subheader("Login to Your Account")
        
        # Custom login form
        login_identifier = st.text_input("Username or Email", placeholder="Enter your username or email")
        login_password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", type="primary"):
            if login_identifier and login_password:
                # Try to authenticate with username first
                success = authenticator.login(login_identifier, login_password)
                
                if not success:
                    # Try to find user by email and authenticate with username
                    user = authenticator.get_user_by_email(login_identifier)
                    if user:
                        success = authenticator.login(user.username, login_password)
                
                if success:
                    # Store user email in session state for Stripe
                    user = authenticator.get_user_by_username(login_identifier)
                    if not user and '@' in login_identifier:
                        # If they logged in with email, get user by email
                        user = authenticator.get_user_by_email(login_identifier)
                    
                    if user and hasattr(user, 'email'):
                        st.session_state.email = user.email
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Username or email not found. Please check your credentials.")
            else:
                st.error("Please enter both username/email and password")

        # Initialize forgot password state
        if 'show_forgot_password' not in st.session_state:
            st.session_state.show_forgot_password = False
        
        if st.button("Forgot Password?"):
            st.session_state.show_forgot_password = True
            st.rerun()
        
        if st.session_state.show_forgot_password:
            st.markdown("---")
            st.markdown("### Reset Your Password")
            forgot_identifier = st.text_input("Enter your username or email", placeholder="Username or email address")
            
            if st.button("Send Password Reset Link", type="primary"):
                if forgot_identifier:
                    try:
                        # Find user by username or email
                        user = authenticator.get_user_by_username(forgot_identifier)
                        if not user:
                            user = authenticator.get_user_by_email(forgot_identifier)
                        
                        if user:
                            # Generate reset token
                            reset_token = authenticator.create_reset_token(user.username)
                            
                            if reset_token:
                                # Send password reset email
                                user_name = f"{user.first_name} {user.last_name}".strip() or user.username
                                email_sent = email_service.send_password_reset_email(user.email, user_name, reset_token)
                                
                                # Always show success message for security
                                st.success("Password reset email sent! If this account exists, you'll receive an email with instructions.")
                            else:
                                st.error("❌ Failed to generate reset token. Please try again.")
                        else:
                            # Show generic message to prevent username/email enumeration
                            st.success("Password reset email sent! If this account exists, you'll receive an email with instructions.")
                    except Exception as e:
                        st.error(f"❌ Password reset failed: {str(e)}")
                else:
                    st.error("Please enter your username or email address first.")

    with tab_signup:
        st.subheader("Create Your Account")
        
        # Custom registration form
        col1, col2 = st.columns(2)
        with col1:
            reg_first_name = st.text_input("First Name", placeholder="Enter your first name")
            reg_email = st.text_input("Email", placeholder="Enter your email address")
            reg_password = st.text_input("Password", type="password", placeholder="Create a password")
        with col2:
            reg_last_name = st.text_input("Last Name", placeholder="Enter your last name")
            reg_username = st.text_input("Username", placeholder="Choose a username")
            reg_confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        if st.button("Create Account", type="primary", use_container_width=True):
            if all([reg_first_name, reg_last_name, reg_email, reg_username, reg_password, reg_confirm_password]):
                if reg_password == reg_confirm_password:
                    # Check if username or email already exists
                    username_exists = authenticator.get_user_by_username(reg_username)
                    email_exists = authenticator.get_user_by_email(reg_email)
                    
                    if username_exists:
                        st.error("Username already exists. Please choose a different username.")
                    elif email_exists:
                        st.error("Email already registered. Please use a different email or log in.")
                    else:
                        try:
                            # Create new user in PostgreSQL
                            success = authenticator.create_user(
                                username=reg_username,
                                email=reg_email,
                                password=reg_password,
                                first_name=reg_first_name,
                                last_name=reg_last_name
                            )
                            
                            if success:
                                # Send welcome email
                                email_sent = email_service.send_welcome_email(reg_email, reg_username)
                                
                                if email_sent:
                                    st.success("✅ Account created successfully! Welcome to Squeeze Ai! Check your email for getting started tips.")
                                else:
                                    st.success("✅ Account created successfully! Welcome to Squeeze Ai!")
                                
                                # Automatically log in the user
                                authenticator.login(reg_username, reg_password)
                                st.rerun()
                            else:
                                st.error("❌ Failed to create account. Please try again.")
                                
                        except Exception as e:
                            st.error(f"Registration failed: {str(e)}")
                else:
                    st.error("Passwords don't match. Please try again.")
            else:
                st.error("Please fill in all fields.")

    with tab_guest:
        st.subheader("🎯 Limited Guest Access")
        st.info("Try our features with limited access. Sign up for full functionality!")
        
        guest_col1, guest_col2 = st.columns(2)
        
        with guest_col1:
            st.markdown("### Top Squeeze Preview")
            if not st.session_state.guest_scan_used:
                if st.button("Get Free Preview", key="guest_scan"):
                    with st.spinner("Analyzing market data..."):
                        stocks = get_squeeze_stocks()
                        st.session_state.guest_scan_used = True
                        # Mark usage persistently
                        mark_guest_usage(st.session_state.browser_fingerprint, "scan")
                        
                        if stocks and len(stocks) > 0:
                            stock = stocks[0]
                            st.markdown(f"""
                            <div class='stock-card'>
                                <h4>{stock['ticker']} - Score: {stock['score']}/100</h4>
                                <p>Short %: {stock['short_percent']}% | Borrow Fee: {stock['borrow_fee']}%</p>
                                <p>{stock['why']}</p>
                                <small>Sign up to see all 5 stocks + filters!</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.warning("Guest preview used. Sign up for unlimited access!")

        with guest_col2:
            st.markdown("### Single Stock Analysis")
            if not st.session_state.guest_search_used:
                ticker = st.text_input("Enter ticker (e.g., TSLA)", key="guest_ticker")
                if st.button("Analyze Free", key="guest_analyze"):
                    if ticker:
                        with st.spinner(f"Analyzing {ticker.upper()}..."):
                            score_data = get_single_squeeze_score(ticker.upper())
                            st.session_state.guest_search_used = True
                            # Mark usage persistently
                            mark_guest_usage(st.session_state.browser_fingerprint, "search")
                            
                            if score_data['score'] != "ERROR":
                                st.markdown(f"""
                                <div class='stock-card'>
                                    <h4>{score_data['ticker']} - Score: {score_data['score']}/100</h4>
                                    <p>{score_data['why']}</p>
                                    <small>Sign up for charts + unlimited searches!</small>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(f"❌ **'{ticker.upper()}' is not a valid stock ticker symbol.**")
                                st.info("💡 **Tip:** Try valid ticker symbols like AAPL, TSLA, MSFT, GOOGL, or AMZN")
            else:
                st.warning("Guest search used. Sign up for unlimited access!")

else:
    # Logged in - show main app
    
    # Header
    st.title("Squeeze-Ai.com 🚀")
    st.markdown("### Ai-Powered Squeeze Detection Tool")

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Top Squeezes", "🔍 Stock Analysis", "💼 Portfolio", "📈 Dashboard", "⚙️ Settings"])

    with tab1:
        st.subheader("Real-Time Squeeze Scanner")
        
        # Primary filters row
        col1, col2, col3 = st.columns(3)
        with col1:
            sector = st.selectbox("Sector Filter", ["All", "Tech", "Biotech", "Retail", "Energy", "Finance"])
        with col2:
            market_cap = st.selectbox("Market Cap", ["All", "Small (<$1B)", "Mid ($1B-$10B)", "Large (>$10B)"])
        with col3:
            short_interest = st.selectbox("Short Interest", ["All", "High (>20%)", "Very High (>30%)", "Extreme (>40%)"])

        # Advanced filters row (Pro only)
        if st.session_state.get('subscribed', False):
            st.markdown("**Advanced Filters**")
            col4, col5, col6 = st.columns(3)
            with col4:
                volatility = st.checkbox("High Volatility Only")
            with col5:
                high_borrow_fee = st.checkbox("High Borrow Fee (>5%)")
            with col6:
                recent_momentum = st.checkbox("Recent Price Momentum")

            # Additional filters row
            col7, col8, col9 = st.columns(3)
            with col7:
                low_float = st.checkbox("Low Float (<50M shares)")
            with col8:
                high_volume = st.checkbox("High Volume Today")
            with col9:
                st.empty()  # Empty column for better spacing
        else:
            st.markdown("**Advanced Filters** 🔒")
            st.info("🚀 **Pro Feature:** Advanced filtering options are available with Pro subscription")
            # Set default values for non-subscribers
            volatility = False
            high_borrow_fee = False
            recent_momentum = False
            low_float = False
            high_volume = False

        filters = []
        if sector != "All":
            filters.append(f"Sector: {sector}")
        if market_cap != "All":
            filters.append(f"Market Cap: {market_cap}")
        if short_interest != "All":
            filters.append(f"Short Interest: {short_interest}")
        if volatility:
            filters.append("High Volatility")
        if high_borrow_fee:
            filters.append("High Borrow Fee")
        if recent_momentum:
            filters.append("Recent Momentum")
        if low_float:
            filters.append("Low Float")
        if high_volume:
            filters.append("High Volume")
        filters_str = ", ".join(filters) if filters else None

        # Check if user wants to perform a new scan
        scan_button_clicked = st.button("🚀 Scan Market", type="primary")
        
        # Show limit message for free users who have used their scan
        if (not st.session_state.subscribed and st.session_state.free_scan_used and 
            not scan_button_clicked):
            st.warning("🔒 Free scan limit reached!")
            st.markdown("""
            <div class='stock-card'>
                <h3>Upgrade to Pro for Unlimited Access</h3>
                <p>You've used your free market scan. Upgrade to Pro to get:</p>
                <ul>
                    <li>✅ Unlimited market scans</li>
                    <li>✅ All 5 daily squeeze picks</li>
                    <li>✅ Advanced filtering options</li>
                    <li>✅ Historical performance data</li>
                    <li>✅ Priority support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔓 Upgrade to Pro - $29/month (14-day FREE trial)", type="primary", key="top_squeezes_upgrade"):
                try:
                    domain = get_current_domain()
                    # Include session ID in success URL for proper session restoration
                    session_id = st.session_state.get('session_id', '')
                    success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                    
                    session = stripe_handler.create_checkout_session(
                        user_id=st.session_state.get('user_id', 1),
                        email=get_user_email(),
                        success_url=success_url,
                        cancel_url=domain
                    )
                    if session:
                        st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                        st.info("✅ 14-day FREE trial - No charge until trial ends!")
                    else:
                        st.error("Unable to create checkout session")
                        # Show the actual Stripe error if available
                        if hasattr(stripe_handler, 'last_error') and stripe_handler.last_error:
                            st.error(f"Payment Error: {stripe_handler.last_error}")
                except Exception as e:
                    st.error(f"Payment setup error: {str(e)}")
                    import traceback
                    st.error(f"Debug traceback: {traceback.format_exc()}")
                    # Fallback to direct activation
                    st.session_state.subscribed = True
                    save_session(st.session_state.username)
                    st.success("🎉 Pro activated! (Stripe unavailable)")
                    st.rerun()
        
        # Display previous scan results if available and no new scan requested
        # Only show saved results for subscribed users (free users can't access saved results)
        elif (st.session_state.get('last_scan_results') and not scan_button_clicked and 
            st.session_state.subscribed):
            st.info("📊 Showing your last market scan results")
            stocks = st.session_state.last_scan_results
            if st.session_state.last_scan_filters:
                st.caption(f"Filters used: {st.session_state.last_scan_filters}")
            else:
                st.caption("No filters applied")
            
            # Display the results (same logic as after a fresh scan)
            if st.session_state.subscribed:
                if len(stocks) > 0:
                    st.success(f"Found {len(stocks)} high-potential squeeze candidates!")
                    
                    # Display all stocks with improved layout
                    for i, stock in enumerate(stocks):
                        # Create a container for each stock
                        with st.container():
                            # Header with stock info and squeeze score
                            st.markdown(f"### #{i+1} {stock['ticker']}")
                            
                            # Squeeze Score section with graphic close to text
                            # Create beautiful circular progress indicator for score
                            score_percentage = stock['score']
                            circumference = 2 * 3.14159 * 30  # radius = 30 (even smaller)
                            stroke_dasharray = circumference
                            stroke_dashoffset = circumference - (score_percentage / 100) * circumference
                            
                            # Determine color based on score
                            if score_percentage >= 80:
                                color = "#10b981"  # Green
                            elif score_percentage >= 60:
                                color = "#f59e0b"  # Yellow
                            else:
                                color = "#ef4444"  # Red
                            
                            st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
                                <span style="font-weight: 600; color: #fafafa; font-size: 16px;">Squeeze Score</span>
                                <div style="position: relative; width: 60px; height: 60px;">
                                    <svg width="60" height="60" style="transform: rotate(-90deg);">
                                        <!-- Background circle -->
                                        <circle cx="30" cy="30" r="25" 
                                                fill="none" 
                                                stroke="#374151" 
                                                stroke-width="4"/>
                                        <!-- Progress circle -->
                                        <circle cx="30" cy="30" r="25" 
                                                fill="none" 
                                                stroke="{color}" 
                                                stroke-width="4" 
                                                stroke-linecap="round"
                                                stroke-dasharray="{stroke_dasharray}" 
                                                stroke-dashoffset="{stroke_dashoffset}"
                                                style="transition: stroke-dashoffset 0.6s ease-in-out;"/>
                                    </svg>
                                    <!-- Score text in center -->
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                                        <div style="font-size: 18px; font-weight: bold; color: {color}; line-height: 1;">{stock['score']}</div>
                                        <div style="font-size: 10px; color: #9ca3af; line-height: 1;">/100</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Metrics in columns
                            metric_col1, metric_col2, metric_col3 = st.columns(3)
                            with metric_col1:
                                st.metric("Short Interest", f"{stock['short_percent']}%")
                            with metric_col2:
                                st.metric("Borrow Fee", f"{stock['borrow_fee']}%")
                            with metric_col3:
                                st.metric("Days to Cover", f"{stock['days_to_cover']}")
                            
                            # Catalyst information
                            st.info(f"**Catalyst:** {stock['why']}")
                            
                            st.divider()
                
                    # Clean Summary chart
                    st.subheader("📊 Squeeze Score Comparison")
                    df = pd.DataFrame(stocks)
                    
                    # Create a clean, modern bar chart
                    chart = alt.Chart(df).mark_bar(
                        cornerRadiusTopLeft=4,
                        cornerRadiusTopRight=4,
                        strokeWidth=0,
                        width=40  # Make bars thinner
                    ).encode(
                        x=alt.X('ticker:N', 
                               sort=alt.EncodingSortField(field='score', order='descending'),
                               title='Stock Ticker',
                               axis=alt.Axis(
                                   labelAngle=0,
                                   labelFontSize=11,
                                   labelColor='#9ca3af',
                                   titleColor='#9ca3af',
                                   titleFontSize=13,
                                   domainOpacity=0,
                                   tickOpacity=0
                               )),
                        y=alt.Y('score:Q', 
                               title='Squeeze Score',
                               scale=alt.Scale(domain=[0, 100]),
                               axis=alt.Axis(
                                   labelFontSize=11,
                                   labelColor='#9ca3af',
                                   titleColor='#9ca3af',
                                   titleFontSize=13,
                                   grid=True,
                                   gridColor='#374151',
                                   gridOpacity=0.2,
                                   domainOpacity=0,
                                   tickOpacity=0
                               )),
                        color=alt.Color('score:Q', 
                                       scale=alt.Scale(
                                           range=['#065f46', '#047857', '#059669', '#10b981', '#34d399', '#00D564']
                                       ),
                                       legend=None),
                        tooltip=[
                            alt.Tooltip('ticker:N', title='Stock'),
                            alt.Tooltip('score:Q', title='Squeeze Score'),
                            alt.Tooltip('short_percent:Q', title='Short Interest %'),
                            alt.Tooltip('borrow_fee:Q', title='Borrow Fee %'),
                            alt.Tooltip('days_to_cover:Q', title='Days to Cover')
                        ]
                    ).properties(
                        height=280,
                        title=alt.TitleParams(
                            text='Top Squeeze Candidates by Score',
                            fontSize=15,
                            color='#00D564',
                            anchor='start',
                            offset=10
                        )
                    ).configure_view(
                        strokeWidth=0,
                        fill='#0e1117'
                    ).configure_title(
                        fontSize=15,
                        color='#00D564'
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    # No stocks found with selected filters
                    st.warning("🔍 **No stocks found with your selected filters**")
                    st.markdown(f"""
                    <div class='stock-card'>
                        <h3>No Results Found</h3>
                        <p>Your current filter combination didn't return any stocks. Try:</p>
                        <ul>
                            <li>🔄 <strong>Removing some filters</strong> to broaden your search</li>
                            <li>📊 <strong>Lowering the minimum score</strong> requirement</li>
                            <li>🎯 <strong>Choosing a different sector</strong> or market cap range</li>
                            <li>📈 <strong>Adjusting short interest thresholds</strong></li>
                        </ul>
                        <p style='margin-top: 1rem;'>
                            <strong>Current filters:</strong> {st.session_state.last_scan_filters if st.session_state.last_scan_filters else "None"}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            else:
                # Free preview
                st.info("🎯 Free Preview: Showing top squeeze candidate only")
                if stocks and len(stocks) > 0:
                    stock = stocks[0]
                    st.markdown(f"""
                    <div class='stock-card'>
                        <h3>{stock['ticker']} - Squeeze Score: {stock['score']}/100</h3>
                        <p><strong>Why:</strong> {stock['why']}</p>
                        <p style='color: #00D564; margin-top: 1rem;'>
                            ⚡ Unlock all 5 stocks with Pro!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("🔍 **No stocks found with your selected filters**")
                    st.markdown(f"""
                    <div class='stock-card'>
                        <h3>No Results Found</h3>
                        <p>Your current filter combination didn't return any stocks. Try:</p>
                        <ul>
                            <li>🔄 <strong>Removing some filters</strong> to broaden your search</li>
                            <li>📊 <strong>Lowering the minimum score</strong> requirement</li>
                            <li>🎯 <strong>Choosing a different sector</strong> or market cap range</li>
                            <li>📈 <strong>Adjusting short interest thresholds</strong></li>
                        </ul>
                        <p style='margin-top: 1rem;'>
                            <strong>Current filters:</strong> {st.session_state.last_scan_filters if st.session_state.last_scan_filters else "None"}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # Handle new scan request
        if scan_button_clicked:
            # Check if user is subscribed or if they've used their free scan
            # Note: subscribed status should be loaded from session, not defaulted here
            
            if not st.session_state.subscribed and st.session_state.free_scan_used:
                # Free user has already used their scan
                st.warning("🔒 Free scan limit reached!")
                st.markdown("""
                <div class='stock-card'>
                    <h3>Upgrade to Pro for Unlimited Access</h3>
                    <p>You've used your free market scan. Upgrade to Pro to get:</p>
                    <ul>
                        <li>✅ Unlimited market scans</li>
                        <li>✅ All 5 daily squeeze picks</li>
                        <li>✅ Advanced filtering options</li>
                        <li>✅ Historical performance data</li>
                        <li>✅ Priority support</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔓 Upgrade to Pro - $29/month (14-day FREE trial)", type="primary", key="scan_upgrade"):
                    # Debug: Show Stripe key status
                    import os
                    stripe_key = os.getenv('STRIPE_SECRET_KEY')
                    
                    try:
                        domain = get_current_domain()
                        
                        # Include session ID in success URL for proper session restoration
                        session_id = st.session_state.get('session_id', '')
                        success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                        
                        session = stripe_handler.create_checkout_session(
                            user_id=st.session_state.get('user_id', 1),
                            email=get_user_email(),
                            success_url=success_url,
                            cancel_url=domain
                        )
                        
                        
                        if session:
                            st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                            st.info("✅ 14-day FREE trial - No charge until trial ends!")
                        else:
                            st.error("Unable to create checkout session - session is None")
                            # Fallback to direct activation
                            st.session_state.subscribed = True
                            save_session(st.session_state.username)
                            st.success("🎉 Pro activated! (Stripe unavailable)")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Payment setup error: {str(e)}")
                        import traceback
                        st.error(f"Debug traceback: {traceback.format_exc()}")
                        # Fallback to direct activation
                        st.session_state.subscribed = True
                        save_session(st.session_state.username)
                        st.success("🎉 Pro activated! (Stripe unavailable)")
                        st.rerun()
            else:
                with st.spinner("Analyzing thousands of stocks..."):
                    stocks = get_squeeze_stocks(filters_str)
                
                # Save scan results and filters to session
                st.session_state.last_scan_results = stocks
                st.session_state.last_scan_filters = filters_str
                save_session(st.session_state.username)
                
                # Mark free scan as used for non-subscribers
                if not st.session_state.subscribed:
                    st.session_state.free_scan_used = True
                    save_session(st.session_state.username)  # Save the usage limit

                if st.session_state.subscribed:
                    if len(stocks) > 0:
                        st.success(f"Found {len(stocks)} high-potential squeeze candidates!")
                        
                        # Display all stocks with improved layout
                        for i, stock in enumerate(stocks):
                            # Create a container for each stock
                            with st.container():
                                # Header with stock info and squeeze score
                                st.markdown(f"### #{i+1} {stock['ticker']}")
                                
                                # Squeeze Score section with graphic close to text
                                # Create beautiful circular progress indicator for score
                                score_percentage = stock['score']
                                circumference = 2 * 3.14159 * 30  # radius = 30 (even smaller)
                                stroke_dasharray = circumference
                                stroke_dashoffset = circumference - (score_percentage / 100) * circumference
                                
                                # Determine color based on score
                                if score_percentage >= 80:
                                    color = "#10b981"  # Green
                                elif score_percentage >= 60:
                                    color = "#f59e0b"  # Yellow
                                else:
                                    color = "#ef4444"  # Red
                                
                                st.markdown(f"""
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
                                    <span style="font-weight: 600; color: #fafafa; font-size: 16px;">Squeeze Score</span>
                                    <div style="position: relative; width: 60px; height: 60px;">
                                        <svg width="60" height="60" style="transform: rotate(-90deg);">
                                            <!-- Background circle -->
                                            <circle cx="30" cy="30" r="25" 
                                                    fill="none" 
                                                    stroke="#374151" 
                                                    stroke-width="4"/>
                                            <!-- Progress circle -->
                                            <circle cx="30" cy="30" r="25" 
                                                    fill="none" 
                                                    stroke="{color}" 
                                                    stroke-width="4" 
                                                    stroke-linecap="round"
                                                    stroke-dasharray="{stroke_dasharray}" 
                                                    stroke-dashoffset="{stroke_dashoffset}"
                                                    style="transition: stroke-dashoffset 0.6s ease-in-out;"/>
                                        </svg>
                                        <!-- Score text in center -->
                                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                                            <div style="font-size: 18px; font-weight: bold; color: {color}; line-height: 1;">{stock['score']}</div>
                                            <div style="font-size: 10px; color: #9ca3af; line-height: 1;">/100</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Metrics in columns
                                metric_col1, metric_col2, metric_col3 = st.columns(3)
                                with metric_col1:
                                    st.metric("Short Interest", f"{stock['short_percent']}%")
                                with metric_col2:
                                    st.metric("Borrow Fee", f"{stock['borrow_fee']}%")
                                with metric_col3:
                                    st.metric("Days to Cover", stock['days_to_cover'])
                                
                                # Catalyst information
                                st.info(f"**Catalyst:** {stock['why']}")
                                
                                st.divider()
                    
                        # Clean Summary chart
                        st.subheader("📊 Squeeze Score Comparison")
                        df = pd.DataFrame(stocks)
                        
                        # Create a clean, modern bar chart
                        chart = alt.Chart(df).mark_bar(
                            cornerRadiusTopLeft=4,
                            cornerRadiusTopRight=4,
                            strokeWidth=0,
                            width=40  # Make bars thinner
                        ).encode(
                            x=alt.X('ticker:N', 
                                   sort=alt.EncodingSortField(field='score', order='descending'),
                                   title='Stock Ticker',
                                   axis=alt.Axis(
                                       labelAngle=0,
                                       labelFontSize=11,
                                       labelColor='#9ca3af',
                                       titleColor='#9ca3af',
                                       titleFontSize=13,
                                       domainOpacity=0,
                                       tickOpacity=0
                                   )),
                            y=alt.Y('score:Q', 
                                   title='Squeeze Score',
                                   scale=alt.Scale(domain=[0, 100]),
                                   axis=alt.Axis(
                                       labelFontSize=11,
                                       labelColor='#9ca3af',
                                       titleColor='#9ca3af',
                                       titleFontSize=13,
                                       grid=True,
                                       gridColor='#374151',
                                       gridOpacity=0.2,
                                       domainOpacity=0,
                                       tickOpacity=0
                                   )),
                            color=alt.Color('score:Q', 
                                           scale=alt.Scale(
                                               range=['#065f46', '#047857', '#059669', '#10b981', '#34d399', '#00D564']
                                           ),
                                           legend=None),
                            tooltip=[
                                alt.Tooltip('ticker:N', title='Stock'),
                                alt.Tooltip('score:Q', title='Squeeze Score'),
                                alt.Tooltip('short_percent:Q', title='Short Interest %'),
                                alt.Tooltip('borrow_fee:Q', title='Borrow Fee %'),
                                alt.Tooltip('days_to_cover:Q', title='Days to Cover')
                            ]
                        ).properties(
                            height=280,
                            title=alt.TitleParams(
                                text='Top Squeeze Candidates by Score',
                                fontSize=15,
                                color='#00D564',
                                anchor='start',
                                offset=10
                            )
                        ).configure_view(
                            strokeWidth=0,
                            fill='#0e1117'
                        ).configure_title(
                            fontSize=15,
                            color='#00D564'
                        )
                        
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        # No stocks found with selected filters
                        st.warning("🔍 **No stocks found with your selected filters**")
                        st.markdown(f"""
                        <div class='stock-card'>
                            <h3>No Results Found</h3>
                            <p>Your current filter combination didn't return any stocks. Try:</p>
                            <ul>
                                <li>🔄 <strong>Removing some filters</strong> to broaden your search</li>
                                <li>📊 <strong>Lowering the minimum score</strong> requirement</li>
                                <li>🎯 <strong>Choosing a different sector</strong> or market cap range</li>
                                <li>📈 <strong>Adjusting short interest thresholds</strong></li>
                            </ul>
                            <p style='margin-top: 1rem;'>
                                <strong>Current filters:</strong> {filters_str if filters_str else "None"}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                else:
                    # Free preview
                    st.info("🎯 Free Preview: Showing top squeeze candidate only")
                    if stocks and len(stocks) > 0:
                        stock = stocks[0]
                        st.markdown(f"""
                        <div class='stock-card'>
                            <h3>{stock['ticker']} - Squeeze Score: {stock['score']}/100</h3>
                            <p><strong>Why:</strong> {stock['why']}</p>
                            <p style='color: #00D564; margin-top: 1rem;'>
                                ⚡ Unlock all 5 stocks with Pro!
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🔓 Unlock Pro Access - $29/month (14-day FREE trial)", type="primary"):
                            try:
                                domain = get_current_domain()
                                # Include session ID in success URL for proper session restoration
                                session_id = st.session_state.get('session_id', '')
                                success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                                
                                session = stripe_handler.create_checkout_session(
                                    user_id=st.session_state.get('user_id', 1),
                                    email=get_user_email(),
                                    success_url=success_url,
                                    cancel_url=domain
                                )
                                
                                if session:
                                    st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                                    st.info("✅ 14-day FREE trial - No charge until trial ends!")
                                else:
                                    st.error("Unable to create checkout session")
                                    # Show the actual Stripe error if available
                                    if hasattr(stripe_handler, 'last_error') and stripe_handler.last_error:
                                        st.error(f"Payment Error: {stripe_handler.last_error}")
                            except Exception as e:
                                st.error(f"Payment setup error: {str(e)}")
                                import traceback
                                st.error(f"Debug traceback: {traceback.format_exc()}")
                                # Fallback to direct activation
                                st.session_state.subscribed = True
                                save_session(st.session_state.username)
                                st.success("🎉 Pro activated! (Stripe unavailable)")
                                st.rerun()
                    else:
                        # No stocks found for free preview
                        st.warning("🔍 **No stocks found with your selected filters**")
                        st.markdown(f"""
                        <div class='stock-card'>
                            <h3>No Results Found</h3>
                            <p>Your current filter combination didn't return any stocks.</p>
                            <p><strong>Current filters:</strong> {filters_str if filters_str else "None"}</p>
                            <p style='color: #00D564; margin-top: 1rem;'>
                                ⚡ Upgrade to Pro for more filtering options and broader search capabilities!
                            </p>
                        </div>
                        """, unsafe_allow_html=True)


                # Save to history
                history_file = f"{st.session_state.username}_history.csv"
                with open(history_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.now(), "scan", filters_str, len(stocks)])

    with tab2:
        st.subheader("Deep Stock Analysis")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker = st.text_input("Enter Stock Ticker", placeholder="TSLA, GME, AMC...")
        with col2:
            period = st.radio("Chart Period", ["1mo", "3mo", "6mo"], horizontal=True)
        
        # Check if user wants to perform a new analysis
        analyze_button_clicked = st.button("Analyze Stock", type="primary")
        
        # Show limit message for free users who have used their analysis
        if (not st.session_state.subscribed and st.session_state.free_search_used and 
            not analyze_button_clicked):
            st.warning("🔒 Free analysis limit reached!")
            st.markdown("""
            <div class='stock-card'>
                <h3>Upgrade to Pro for Unlimited Access</h3>
                <p>You've used your free stock analysis. Upgrade to Pro to get:</p>
                <ul>
                    <li>✅ Unlimited stock analysis</li>
                    <li>✅ Full price charts and historical data</li>
                    <li>✅ Score breakdown visualizations</li>
                    <li>✅ All 5 daily squeeze picks</li>
                    <li>✅ Priority support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔓 Upgrade to Pro - $29/month (14-day FREE trial)", type="primary", key="stock_analysis_upgrade"):
                try:
                    domain = get_current_domain()
                    # Include session ID in success URL for proper session restoration
                    session_id = st.session_state.get('session_id', '')
                    success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                    
                    session = stripe_handler.create_checkout_session(
                        user_id=st.session_state.get('user_id', 1),
                        email=get_user_email(),
                        success_url=success_url,
                        cancel_url=domain
                    )
                    if session:
                        st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                        st.info("✅ 14-day FREE trial - No charge until trial ends!")
                    else:
                        st.error("Unable to create checkout session")
                        # Show the actual Stripe error if available
                        if hasattr(stripe_handler, 'last_error') and stripe_handler.last_error:
                            st.error(f"Payment Error: {stripe_handler.last_error}")
                except Exception as e:
                    st.error(f"Payment setup error: {str(e)}")
                    import traceback
                    st.error(f"Debug traceback: {traceback.format_exc()}")
                    # Fallback to direct activation
                    st.session_state.subscribed = True
                    save_session(st.session_state.username)
                    st.success("🎉 Pro activated! (Stripe unavailable)")
                    st.rerun()
        
        # Display previous analysis results if available and no new analysis requested
        # Only show saved results for subscribed users (free users can't access saved results)
        elif (st.session_state.get('last_analysis_result') and 
            st.session_state.get('last_analysis_ticker') and 
            not analyze_button_clicked and
            st.session_state.subscribed):
            
            st.info(f"📊 Showing your last analysis for {st.session_state.last_analysis_ticker}")
            
            # Restore the analysis data
            ticker = st.session_state.last_analysis_ticker
            score_data = st.session_state.last_analysis_result
            period = st.session_state.get('last_analysis_period', '6mo')
            
            # Display the same results as after fresh analysis
            if score_data['score'] != "ERROR":
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Squeeze Score", f"{score_data['score']}/100")
                with col2:
                    st.metric("Short Interest", f"{score_data['short_percent']}%")
                with col3:
                    st.metric("Borrow Fee", f"{score_data['borrow_fee']}%")
                with col4:
                    st.metric("Days to Cover", f"{score_data['days_to_cover']}")
                
                # Catalyst/Why information
                st.info(f"**Analysis:** {score_data['why']}")
                
                # Get fresh historical data for the chart
                hist_data = get_historical_data(ticker, period)
                
                # Display chart if we have historical data
                if not hist_data.empty:
                    st.subheader(f"📈 {ticker} Price Chart ({period})")
                    
                    # Create price chart
                    chart = alt.Chart(hist_data).mark_line(
                        color='#00D564',
                        strokeWidth=2,
                        point=alt.OverlayMarkDef(color='#00D564', size=30)
                    ).encode(
                        x=alt.X('Date:T', title='Date'),
                        y=alt.Y('Close:Q', title='Price ($)'),
                        tooltip=['Date:T', 'Close:Q', 'Volume:Q']
                    ).properties(
                        height=400,
                        title=f'{ticker} Stock Price - {period}'
                    ).configure_title(
                        fontSize=16,
                        color='#00D564'
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.warning("Chart data unavailable for this stock")
            else:
                st.error(f"❌ {score_data['why']}")
            
        
        # Handle new analysis request
        if analyze_button_clicked:
            if ticker:
                # Check if user is subscribed or if they've used their free search
                # Note: subscribed status should be loaded from session, not defaulted here
                
                if not st.session_state.subscribed and st.session_state.free_search_used:
                    # Free user has already used their search
                    st.warning("🔒 Free analysis limit reached!")
                    st.markdown("""
                    <div class='stock-card'>
                        <h3>Upgrade to Pro for Unlimited Access</h3>
                        <p>You've used your free stock analysis. Upgrade to Pro to get:</p>
                        <ul>
                            <li>✅ Unlimited stock analysis</li>
                            <li>✅ Full price charts and historical data</li>
                            <li>✅ Score breakdown visualizations</li>
                            <li>✅ All 5 daily squeeze picks</li>
                            <li>✅ Priority support</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔓 Upgrade to Pro - $29/month (14-day FREE trial)", type="primary", key="search_upgrade"):
                        try:
                            domain = get_current_domain()
                            # Include session ID in success URL for proper session restoration
                            session_id = st.session_state.get('session_id', '')
                            success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                            
                            session = stripe_handler.create_checkout_session(
                                user_id=st.session_state.get('user_id', 1),
                                email=get_user_email(),
                                success_url=success_url,
                                cancel_url=domain
                            )
                            
                            if session:
                                st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                                st.info("✅ 14-day FREE trial - No charge until trial ends!")
                            else:
                                st.error("Unable to create checkout session")
                                # Show the actual Stripe error if available
                                if hasattr(stripe_handler, 'last_error') and stripe_handler.last_error:
                                    st.error(f"Payment Error: {stripe_handler.last_error}")
                        except Exception as e:
                            st.error(f"Payment setup error: {str(e)}")
                            import traceback
                            st.error(f"Debug traceback: {traceback.format_exc()}")
                            # Fallback to direct activation
                            st.session_state.subscribed = True
                            save_session(st.session_state.username)
                            st.success("🎉 Pro activated! (Stripe unavailable)")
                            st.rerun()
                else:
                    with st.spinner(f"Analyzing {ticker.upper()}..."):
                        # Mark free search as used for non-subscribers
                        if not st.session_state.subscribed:
                            st.session_state.free_search_used = True
                            save_session(st.session_state.username)  # Save the usage limit
                        
                        # Get squeeze score
                        score_data = get_single_squeeze_score(ticker.upper())
                        
                        # Get historical data
                        hist_data = get_historical_data(ticker.upper(), period)
                        
                        # Save analysis results to session
                        st.session_state.last_analysis_result = score_data
                        st.session_state.last_analysis_ticker = ticker.upper()
                        st.session_state.last_analysis_period = period
                        save_session(st.session_state.username)
                        
                        if score_data['score'] != "ERROR":
                            # Display metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Squeeze Score", f"{score_data['score']}/100")
                            with col2:
                                st.metric("Short Interest", f"{score_data['short_percent']}%")
                            with col3:
                                st.metric("Borrow Fee", f"{score_data['borrow_fee']}%")
                            with col4:
                                st.metric("Days to Cover", f"{score_data['days_to_cover']}")
                            
                            st.markdown(f"""
                            <div class='stock-card'>
                                <h3>Analysis Summary</h3>
                                <p>{score_data['why']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Price chart
                            if not hist_data.empty:
                                st.subheader(f"{ticker.upper()} Price History")
                                
                                # Calculate price change
                                price_change = ((hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[0]) / hist_data['Close'].iloc[0]) * 100
                                
                                price_chart = alt.Chart(hist_data).mark_area(
                                    line={'color': '#00D564', 'strokeWidth': 2},
                                    color=alt.Gradient(
                                        gradient='linear',
                                        stops=[
                                            alt.GradientStop(color='#00D564', offset=0),
                                            alt.GradientStop(color='#001F0F', offset=1)
                                        ],
                                        x1=1, x2=1, y1=1, y2=0
                                    )
                                ).encode(
                                    x=alt.X('Date:T', title='Date'),
                                    y=alt.Y('Close:Q', title='Price ($)'),
                                    tooltip=[
                                        alt.Tooltip('Date:T', format='%Y-%m-%d'),
                                        alt.Tooltip('Close:Q', format='$.2f', title='Price'),
                                        alt.Tooltip('Volume:Q', format=',d')
                                    ]
                                ).properties(
                                    height=400,
                                    title={
                                        'text': f'{ticker.upper()} - {period} Price Movement ({price_change:+.2f}%)',
                                        'color': '#00D564' if price_change > 0 else '#FF4444'
                                    }
                                ).configure_view(
                                    strokeWidth=0
                                ).configure_axis(
                                    grid=False,
                                    labelColor='#9ca3af',
                                    titleColor='#9ca3af'
                                )
                                
                                st.altair_chart(price_chart, use_container_width=True)
                                
                                # Volume chart
                                volume_chart = alt.Chart(hist_data).mark_bar(
                                    color='#00D564',
                                    opacity=0.3
                                ).encode(
                                    x=alt.X('Date:T', title=''),
                                    y=alt.Y('Volume:Q', title='Volume'),
                                    tooltip=[
                                        alt.Tooltip('Date:T', format='%Y-%m-%d'),
                                        alt.Tooltip('Volume:Q', format=',d')
                                    ]
                                ).properties(
                                    height=150
                                ).configure_view(
                                    strokeWidth=0
                                ).configure_axis(
                                    grid=False,
                                    labelColor='#9ca3af',
                                    titleColor='#9ca3af'
                                )
                                
                                st.altair_chart(volume_chart, use_container_width=True)
                            
                            # Score breakdown visualization
                            st.subheader("Score Breakdown")
                            breakdown_data = pd.DataFrame([
                                {'Factor': 'Short Interest', 'Weight': 30, 'Score': min(30, score_data['short_percent'])},
                                {'Factor': 'Borrow Fee', 'Weight': 20, 'Score': min(20, score_data['borrow_fee'])},
                                {'Factor': 'Days to Cover', 'Weight': 20, 'Score': min(20, score_data['days_to_cover'] * 2)},
                                {'Factor': 'Momentum', 'Weight': 30, 'Score': score_data['score'] - min(70, score_data['short_percent'] + score_data['borrow_fee'] + score_data['days_to_cover'] * 2)}
                            ])
                            
                            breakdown_chart = alt.Chart(breakdown_data).mark_bar().encode(
                                x=alt.X('Score:Q', scale=alt.Scale(domain=[0, 30]), title='Contribution to Score'),
                                y=alt.Y('Factor:N', sort='-x'),
                                color=alt.Color('Factor:N', scale=alt.Scale(scheme='greens'), legend=None),
                                tooltip=['Factor', 'Score', 'Weight']
                            ).properties(
                                height=200
                            ).configure_view(
                                strokeWidth=0
                            ).configure_axis(
                                grid=False
                            )
                            
                            st.altair_chart(breakdown_chart, use_container_width=True)
                        else:
                            # Handle invalid ticker symbol
                            st.error(f"❌ **'{ticker.upper()}' is not a valid stock ticker symbol.**")
                            st.markdown("""
                            <div class='stock-card'>
                                <h3>Invalid Ticker Symbol</h3>
                                <p>Please check your ticker symbol and try again. Examples of valid ticker symbols:</p>
                                <ul>
                                    <li><strong>AAPL</strong> - Apple Inc.</li>
                                    <li><strong>TSLA</strong> - Tesla Inc.</li>
                                    <li><strong>MSFT</strong> - Microsoft Corporation</li>
                                    <li><strong>GOOGL</strong> - Alphabet Inc.</li>
                                    <li><strong>AMZN</strong> - Amazon.com Inc.</li>
                                </ul>
                                <p style='margin-top: 1rem;'>
                                    <strong>Tips:</strong>
                                    <br>• Use the official stock ticker symbol (not company name)
                                    <br>• Check if the company is publicly traded
                                    <br>• Verify the symbol on financial websites like Yahoo Finance
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        

                        # Save to history
                        history_file = f"{st.session_state.username}_history.csv"
                        with open(history_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([datetime.now(), "search", ticker, score_data.get('score', 'ERROR')])
            else:
                st.warning("Please enter a ticker symbol")

    with tab3:
        st.subheader("Portfolio Tracker")
        
        # Check if user has Pro access
        if not st.session_state.subscribed:
            st.warning("🔒 Portfolio tracking is a Pro feature!")
            st.markdown("""
            <div class='stock-card'>
                <h3>Upgrade to Pro for Portfolio Tracking</h3>
                <p>Track your stock holdings with advanced portfolio analytics:</p>
                <ul>
                    <li>✅ Add unlimited holdings</li>
                    <li>✅ Real-time portfolio value tracking</li>
                    <li>✅ 1-year performance charts</li>
                    <li>✅ Profit/loss analysis</li>
                    <li>✅ Portfolio diversity metrics</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔓 Upgrade to Pro - $29/month (14-day FREE trial)", type="primary", key="portfolio_upgrade"):
                try:
                    domain = get_current_domain()
                    # Get user email
                    user_email = get_user_email()
                    
                    # Include session ID in success URL
                    session_id = st.session_state.get('session_id', '')
                    success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                    
                    session = stripe_handler.create_checkout_session(
                        user_id=st.session_state.get('user_id', 1),
                        email=user_email,
                        success_url=success_url,
                        cancel_url=domain
                    )
                    
                    if session:
                        st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                        st.info("✅ 14-day FREE trial - No charge until trial ends!")
                    else:
                        st.error("Unable to create checkout session")
                        # Show the actual Stripe error if available
                        if hasattr(stripe_handler, 'last_error') and stripe_handler.last_error:
                            st.error(f"Payment Error: {stripe_handler.last_error}")
                except Exception as e:
                    st.error(f"Payment setup error: {str(e)}")
                    st.session_state.subscribed = True  # Demo mode
                    save_session(st.session_state.username)
        else:
            # Portfolio functionality for Pro users
            st.success("🚀 Pro Portfolio Tracker")
            
            # Initialize portfolio data in session if not exists
            if 'portfolio_holdings' not in st.session_state:
                st.session_state.portfolio_holdings = []
            
            # Add new holding section
            st.subheader("Add New Holding")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                ticker_input = st.text_input("Stock Ticker", placeholder="AAPL", key="portfolio_ticker")
            with col2:
                shares_input = st.number_input("Shares", min_value=1, step=1, key="portfolio_shares")
            with col3:
                avg_price_input = st.number_input("Avg Price ($)", min_value=0.01, step=1.00, key="portfolio_avg_price")
            
            if st.button("Add to Portfolio", type="primary"):
                if ticker_input and shares_input and avg_price_input:
                    # Validate ticker exists
                    ticker_upper = ticker_input.upper()
                    
                    with st.spinner(f"Validating {ticker_upper}..."):
                        try:
                            # Check if ticker exists by trying to fetch basic info
                            stock = yf.Ticker(ticker_upper)
                            info = stock.info
                            
                            # Try to get recent price to confirm ticker is valid
                            recent_data = stock.history(period="5d")
                            
                            if recent_data.empty or not info or info.get('symbol') != ticker_upper:
                                raise ValueError("Invalid ticker")
                            
                            # Get company name for confirmation
                            company_name = info.get('longName', info.get('shortName', ticker_upper))
                            
                            # Ticker is valid, proceed with adding
                            existing_holding = next((h for h in st.session_state.portfolio_holdings if h['ticker'] == ticker_upper), None)
                            
                            if existing_holding:
                                # Update existing holding (average cost basis)
                                total_shares = existing_holding['shares'] + shares_input
                                total_cost = (existing_holding['shares'] * existing_holding['avg_price']) + (shares_input * avg_price_input)
                                new_avg_price = total_cost / total_shares
                                
                                existing_holding['shares'] = total_shares
                                existing_holding['avg_price'] = new_avg_price
                                st.success(f"✅ Updated {ticker_upper} ({company_name}) holding!")
                            else:
                                # Add new holding
                                st.session_state.portfolio_holdings.append({
                                    'ticker': ticker_upper,
                                    'shares': shares_input,
                                    'avg_price': avg_price_input,
                                    'date_added': datetime.now().strftime('%Y-%m-%d')
                                })
                                st.success(f"✅ Added {ticker_upper} ({company_name}) to portfolio!")
                            
                            # Save portfolio to session
                            save_session(st.session_state.username)
                            st.rerun()
                            
                        except Exception as e:
                            # Ticker doesn't exist or other error
                            st.error(f"❌ **'{ticker_upper}' is not a valid ticker symbol**")
                            st.markdown(f"""
                            <div style='background-color: #1f2937; padding: 1rem; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 0.5rem;'>
                                <p style='margin: 0; color: #fca5a5;'><strong>Please check:</strong></p>
                                <ul style='margin: 0.5rem 0; padding-left: 1.5rem; color: #fca5a5;'>
                                    <li>Ticker symbol is spelled correctly</li>
                                    <li>Company is publicly traded</li>
                                    <li>Use the official ticker symbol (e.g., AAPL for Apple)</li>
                                    <li>Check if it's delisted or suspended</li>
                                </ul>
                                <p style='margin: 0.5rem 0 0 0; color: #9ca3af; font-size: 0.9rem;'>
                                    <strong>Examples:</strong> AAPL, TSLA, MSFT, GOOGL, AMZN, SPY, QQQ
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("Please fill in all fields")
            
            # Display current holdings
            if st.session_state.portfolio_holdings:
                st.subheader("Current Holdings")
                
                # Calculate portfolio metrics
                total_value = 0
                total_cost = 0
                portfolio_data = []
                
                for holding in st.session_state.portfolio_holdings:
                    try:
                        # Get current price
                        stock = yf.Ticker(holding['ticker'])
                        price_data = stock.history(period="1d")
                        
                        # Check if we have valid price data
                        if not price_data.empty and 'Close' in price_data.columns:
                            current_price = price_data['Close'].iloc[-1]
                            
                            # Calculate metrics
                            current_value = holding['shares'] * current_price
                            cost_basis = holding['shares'] * holding['avg_price']
                            pnl = current_value - cost_basis
                            pnl_percent = (pnl / cost_basis) * 100
                            
                            portfolio_data.append({
                                'ticker': holding['ticker'],
                                'shares': holding['shares'],
                                'avg_price': holding['avg_price'],
                                'current_price': current_price,
                                'current_value': current_value,
                                'cost_basis': cost_basis,
                                'pnl': pnl,
                                'pnl_percent': pnl_percent
                            })
                            
                            total_value += current_value
                            total_cost += cost_basis
                        else:
                            # Skip this holding silently - no error message
                            continue
                        
                    except Exception as e:
                        # Skip this holding silently - no error message
                        continue
                
                # Portfolio summary
                total_pnl = total_value - total_cost
                total_pnl_percent = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
                
                # Show last update time
                current_time = datetime.now()
                st.caption(f"📊 Portfolio updated: {current_time.strftime('%I:%M:%S %p')} ET")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Value", f"${total_value:,.2f}")
                with col2:
                    st.metric("Total Cost", f"${total_cost:,.2f}")
                with col3:
                    st.metric("Total P&L", f"${total_pnl:,.2f}", f"{total_pnl_percent:+.2f}%")
                with col4:
                    st.metric("Holdings", len(st.session_state.portfolio_holdings))
                
                # Holdings table
                st.subheader("Holdings Detail")
                for i, data in enumerate(portfolio_data):
                    with st.expander(f"{data['ticker']} - {data['shares']} shares"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Current Price", f"${data['current_price']:.2f}")
                            st.metric("Avg Cost", f"${data['avg_price']:.2f}")
                            st.metric("Current Value", f"${data['current_value']:.2f}")
                        
                        with col2:
                            st.metric("Cost Basis", f"${data['cost_basis']:.2f}")
                            st.metric("P&L", f"${data['pnl']:.2f}", f"{data['pnl_percent']:+.2f}%")
                            if st.button(f"Remove {data['ticker']}", key=f"remove_{data['ticker']}"):
                                st.session_state.portfolio_holdings = [h for h in st.session_state.portfolio_holdings if h['ticker'] != data['ticker']]
                                save_session(st.session_state.username)
                                st.rerun()
                
                # Interactive Portfolio Performance Chart
                if portfolio_data:
                    st.subheader("Interactive Portfolio Performance")
                    
                    # Time period selector
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        chart_period = st.selectbox(
                            "Time Period",
                            options=["1W", "1M", "3M", "6M", "1Y", "2Y"],
                            index=4,  # Default to 1Y
                            key="portfolio_chart_period"
                        )
                    
                    # Map period to days
                    period_days = {
                        "1W": 7, "1M": 30, "3M": 90, 
                        "6M": 180, "1Y": 365, "2Y": 730
                    }
                    
                    days = period_days[chart_period]
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    with st.spinner(f"Loading {chart_period} portfolio data..."):
                        try:
                            # Enhanced portfolio calculation with better performance
                            portfolio_history = []
                            
                            # Get all tickers and fetch data once
                            tickers = [holding['ticker'] for holding in st.session_state.portfolio_holdings]
                            
                            if tickers:
                                # Fetch historical data for all tickers at once (more efficient)
                                ticker_data = {}
                                for ticker in tickers:
                                    try:
                                        stock = yf.Ticker(ticker)
                                        hist = stock.history(start=start_date, end=end_date)
                                        if not hist.empty:
                                            ticker_data[ticker] = hist
                                    except:
                                        continue
                                
                                # Calculate portfolio value for each day
                                if ticker_data:
                                    # Get all unique dates
                                    all_dates = set()
                                    for hist in ticker_data.values():
                                        all_dates.update(hist.index.date)
                                    
                                    all_dates = sorted(all_dates)
                                    
                                    for date in all_dates:
                                        daily_value = 0
                                        daily_cost = 0
                                        
                                        for holding in st.session_state.portfolio_holdings:
                                            ticker = holding['ticker']
                                            if ticker in ticker_data:
                                                hist = ticker_data[ticker]
                                                # Find closest date
                                                available_dates = [d.date() for d in hist.index]
                                                closest_date = min(available_dates, key=lambda x: abs((x - date).days))
                                                
                                                if abs((closest_date - date).days) <= 3:  # Within 3 days
                                                    price_data = hist[hist.index.date == closest_date]
                                                    if not price_data.empty:
                                                        price = price_data['Close'].iloc[0]
                                                        daily_value += holding['shares'] * price
                                                        daily_cost += holding['shares'] * holding['avg_price']
                                        
                                        if daily_value > 0:
                                            pnl = daily_value - daily_cost
                                            pnl_percent = (pnl / daily_cost) * 100 if daily_cost > 0 else 0
                                            
                                            portfolio_history.append({
                                                'date': pd.Timestamp(date),
                                                'value': daily_value,
                                                'cost': daily_cost,
                                                'pnl': pnl,
                                                'pnl_percent': pnl_percent
                                            })
                            
                            if portfolio_history:
                                df_portfolio = pd.DataFrame(portfolio_history)
                                df_portfolio = df_portfolio.sort_values('date')
                                
                                # Calculate additional metrics
                                first_value = df_portfolio['value'].iloc[0]
                                last_value = df_portfolio['value'].iloc[-1]
                                period_return = ((last_value - first_value) / first_value) * 100
                                
                                # Display period summary
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Period Return", f"{period_return:+.2f}%")
                                with col2:
                                    st.metric("Period High", f"${df_portfolio['value'].max():,.2f}")
                                with col3:
                                    st.metric("Period Low", f"${df_portfolio['value'].min():,.2f}")
                                with col4:
                                    volatility = df_portfolio['pnl_percent'].std()
                                    st.metric("Volatility", f"{volatility:.2f}%")
                                
                                # Create interactive chart with selection
                                brush = alt.selection_interval(encodings=['x'])
                                
                                # Main chart
                                base = alt.Chart(df_portfolio).add_selection(brush)
                                
                                # Area chart for portfolio value
                                area_chart = base.mark_area(
                                    line={'color': '#00D564', 'strokeWidth': 2},
                                    color=alt.Gradient(
                                        gradient='linear',
                                        stops=[
                                            alt.GradientStop(color='#00D564', offset=0),
                                            alt.GradientStop(color='rgba(0, 213, 100, 0.1)', offset=1)
                                        ],
                                        x1=1, x2=1, y1=1, y2=0
                                    ),
                                    opacity=0.8
                                ).encode(
                                    x=alt.X('date:T', 
                                           title='Date',
                                           axis=alt.Axis(format='%b %d' if days <= 30 else '%b %Y', 
                                                        grid=False, 
                                                        labelColor='#9ca3af',
                                                        titleColor='#9ca3af')),
                                    y=alt.Y('value:Q', 
                                           title='Portfolio Value ($)',
                                           axis=alt.Axis(format='$,.0f', 
                                                        grid=True, 
                                                        gridColor='#374151',
                                                        labelColor='#9ca3af',
                                                        titleColor='#9ca3af')),
                                    tooltip=[
                                        alt.Tooltip('date:T', format='%Y-%m-%d', title='Date'),
                                        alt.Tooltip('value:Q', format='$,.2f', title='Portfolio Value'),
                                        alt.Tooltip('cost:Q', format='$,.2f', title='Cost Basis'),
                                        alt.Tooltip('pnl:Q', format='$,.2f', title='P&L ($)'),
                                        alt.Tooltip('pnl_percent:Q', format='.2f', title='P&L (%)')
                                    ]
                                ).properties(
                                    height=400,
                                    title={
                                        'text': f'Portfolio Performance ({chart_period}) - {period_return:+.2f}%',
                                        'color': '#00D564' if period_return > 0 else '#FF4444',
                                        'fontSize': 16
                                    }
                                )
                                
                                # Cost basis line
                                cost_line = base.mark_line(
                                    color='#6b7280',
                                    strokeDash=[5, 5],
                                    strokeWidth=1
                                ).encode(
                                    x='date:T',
                                    y='cost:Q',
                                    tooltip=[
                                        alt.Tooltip('date:T', format='%Y-%m-%d', title='Date'),
                                        alt.Tooltip('cost:Q', format='$,.2f', title='Cost Basis')
                                    ]
                                )
                                
                                # Combine charts
                                main_chart = (area_chart + cost_line).resolve_scale(
                                    y='shared'
                                ).configure_view(
                                    strokeWidth=0,
                                    fill='#0e1117'
                                ).configure_title(
                                    fontSize=16,
                                    color='#00D564' if period_return > 0 else '#FF4444'
                                )
                                
                                st.altair_chart(main_chart, use_container_width=True)
                                
                                # Performance statistics
                                st.subheader("Performance Statistics")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**Returns by Period:**")
                                    if len(df_portfolio) > 7:
                                        week_return = ((df_portfolio['value'].iloc[-1] - df_portfolio['value'].iloc[-7]) / df_portfolio['value'].iloc[-7]) * 100
                                        st.write(f"• 1 Week: {week_return:+.2f}%")
                                    if len(df_portfolio) > 30:
                                        month_return = ((df_portfolio['value'].iloc[-1] - df_portfolio['value'].iloc[-30]) / df_portfolio['value'].iloc[-30]) * 100
                                        st.write(f"• 1 Month: {month_return:+.2f}%")
                                    st.write(f"• {chart_period}: {period_return:+.2f}%")
                                
                                with col2:
                                    st.markdown("**Risk Metrics:**")
                                    daily_returns = df_portfolio['pnl_percent'].pct_change().dropna()
                                    if len(daily_returns) > 1:
                                        sharpe_ratio = daily_returns.mean() / daily_returns.std() * (252**0.5) if daily_returns.std() != 0 else 0
                                        st.write(f"• Volatility: {volatility:.2f}%")
                                        st.write(f"• Sharpe Ratio: {sharpe_ratio:.2f}")
                                        max_drawdown = ((df_portfolio['value'].cummax() - df_portfolio['value']) / df_portfolio['value'].cummax()).max() * 100
                                        st.write(f"• Max Drawdown: {max_drawdown:.2f}%")
                                
                            else:
                                st.warning(f"Unable to generate {chart_period} portfolio chart. This may be due to insufficient historical data or market closures.")
                        
                        except Exception as e:
                            st.error(f"Error generating interactive portfolio chart: {str(e)}")
                            st.info("Try selecting a different time period or check your internet connection.")
                
                # Real-time update controls (moved below chart to prevent excessive API usage)
                st.markdown("---")
                st.subheader("🔄 Real-Time Updates")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    auto_refresh = st.checkbox("🔄 Auto-refresh portfolio", value=False, key="auto_refresh_portfolio")
                with col2:
                    if auto_refresh:
                        refresh_interval = st.selectbox(
                            "Update every:",
                            options=[30, 60, 300, 900],
                            format_func=lambda x: f"{x//60}m {x%60}s" if x >= 60 else f"{x}s",
                            index=1,  # Default to 60 seconds
                            key="refresh_interval"
                        )
                    else:
                        refresh_interval = 60
                with col3:
                    if st.button("🔄 Refresh Now", key="manual_refresh"):
                        st.rerun()
                
                # Auto-refresh mechanism
                if auto_refresh and st.session_state.portfolio_holdings:
                    import time
                    
                    # Initialize last refresh time
                    if 'last_portfolio_refresh' not in st.session_state:
                        st.session_state.last_portfolio_refresh = time.time()
                    
                    current_time = time.time()
                    time_since_refresh = current_time - st.session_state.last_portfolio_refresh
                    
                    # Show countdown
                    remaining_time = max(0, refresh_interval - int(time_since_refresh))
                    
                    if remaining_time > 0:
                        st.info(f"🕐 Next update in {remaining_time} seconds...")
                        # Auto-refresh when time is up
                        time.sleep(1)  # Wait 1 second then rerun to update countdown
                        st.rerun()
                    else:
                        st.info("🔄 Updating portfolio...")
                        st.session_state.last_portfolio_refresh = current_time
                        st.rerun()
                
            else:
                st.info("No holdings added yet. Add your first stock above to get started!")

    with tab4:
        st.subheader("Analytics Dashboard")
        
        # Get actual user activity data
        history_file = f"{st.session_state.username}_history.csv"
        history_data = []
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        try:
                            history_data.append({
                                'Time': pd.to_datetime(row[0]),
                                'Type': row[1],
                                'Query': row[2] if row[2] != 'None' else '',
                                'Result': int(row[3]) if row[3].isdigit() else row[3]
                            })
                        except:
                            continue
        
        # Calculate real metrics from user data
        total_scans = len([h for h in history_data if h['Type'] == 'scan'])
        total_searches = len([h for h in history_data if h['Type'] == 'search'])
        total_activities = len(history_data)
        
        # Calculate average score from searches
        search_scores = [h['Result'] for h in history_data if h['Type'] == 'search' and isinstance(h['Result'], int)]
        avg_score = int(sum(search_scores) / len(search_scores)) if search_scores else 0
        
        # Summary metrics with real data
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Market Scans", total_scans, help="Number of market scans performed")
        with col2:
            st.metric("Stock Searches", total_searches, help="Individual stocks analyzed")
        
        
        # Recent Activity with better formatting
        st.subheader("🕒 Recent Activity")
        
        if history_data:
            # Show last 10 activities with better formatting
            recent_activities = sorted(history_data, key=lambda x: x['Time'], reverse=True)[:10]
            
            for i, activity in enumerate(recent_activities):
                time_str = activity['Time'].strftime("%m/%d/%Y %I:%M %p")
                
                if activity['Type'] == 'scan':
                    if activity['Query']:
                        action_text = f"Market scan with filters: {activity['Query']}"
                    else:
                        action_text = "Market scan (no filters)"
                    result_text = f"Found {activity['Result']} stocks"
                    icon = "🔍"
                else:  # search
                    action_text = f"Analyzed stock: {activity['Query'].upper()}"
                    result_text = f"Score: {activity['Result']}/100"
                    icon = "📊"
                
                st.markdown(f"""
                <div class='stock-card' style='padding: 1rem; margin-bottom: 0.5rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='display: flex; align-items: center; gap: 0.5rem;'>
                            <span style='font-size: 1.2rem;'>{icon}</span>
                            <div>
                                <div style='font-weight: 600; color: #fafafa;'>{action_text}</div>
                                <div style='font-size: 0.85rem; color: #9ca3af;'>{time_str}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: #00D564; font-weight: 600;'>{result_text}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activity yet. Start by scanning the market or analyzing individual stocks!")
        
        # Enhanced Top Searched Stocks Section
        if history_data:
            searches = [h for h in history_data if h['Type'] == 'search' and h['Query']]
            if searches:
                st.subheader("🔥 Most Analyzed Stocks")
                
                # Count searches by stock
                stock_counts = {}
                stock_scores = {}
                for search in searches:
                    ticker = search['Query'].upper()
                    stock_counts[ticker] = stock_counts.get(ticker, 0) + 1
                    if isinstance(search['Result'], int):
                        stock_scores[ticker] = search['Result']
                
                # Create top stocks display with better styling
                top_stocks = sorted(stock_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                
                for i, (ticker, count) in enumerate(top_stocks):
                    score = stock_scores.get(ticker, 'N/A')
                    
                    # Determine score color
                    if score != 'N/A':
                        if score >= 70:
                            score_color = '#00D564'  # Green
                        elif score >= 50:
                            score_color = '#f59e0b'  # Yellow
                        else:
                            score_color = '#ef4444'  # Red
                        score_text = f"{score}/100"
                    else:
                        score_color = '#9ca3af'
                        score_text = "N/A"
                    
                    st.markdown(f"""
                    <div class='stock-card' style='padding: 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;'>
                        <div style='display: flex; align-items: center; gap: 1rem;'>
                            <div style='background-color: #374151; color: #00D564; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: 600; font-size: 0.8rem;'>
                                #{i+1}
                            </div>
                            <div>
                                <div style='font-weight: 600; color: #fafafa; font-size: 1.1rem;'>{ticker}</div>
                                <div style='color: #9ca3af; font-size: 0.85rem;'>{count} analysis{'' if count == 1 else 'es'}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: {score_color}; font-weight: 600;'>Score: {score_text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        

    with tab5:
        st.subheader("Account Settings")
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            st.markdown("### Profile Information")
            st.markdown("")
            
            # Safety check for username
            if not st.session_state.username:
                st.error("Session error. Please log in again.")
                st.stop()
            
            st.text_input("Username", value=st.session_state.username, disabled=True, help="Username cannot be changed for security reasons")
            
            # Safety check for user existence
            current_user = authenticator.get_user_by_username(st.session_state.username)
            if not current_user:
                st.error("User not found. Please log in again.")
                st.stop()
                
            current_email = current_user.email
            st.text_input("Email Address", value=current_email, disabled=True, help="Email address cannot be changed for security reasons")
            
            st.markdown("")
            st.markdown("### Change Password")
            st.markdown("")
            
            current_password = st.text_input("Current Password", type="password", help="Enter your current password to change it")
            new_password = st.text_input("New Password", type="password", help="Enter your new password")
            confirm_password = st.text_input("Confirm New Password", type="password", help="Confirm your new password")
            
            st.markdown("")
            col_update, col_forgot = st.columns([1, 1])
            
            with col_update:
                if st.button("Update Password", type="primary"):
                    # Update password
                    if new_password and confirm_password and current_password:
                        if new_password == confirm_password:
                            # Use PostgreSQL authentication system
                            try:
                                success = authenticator.change_password(
                                    st.session_state.username, 
                                    current_password, 
                                    new_password
                                )
                                
                                if success:
                                    st.success("Password updated successfully!")
                                else:
                                    st.error("Current password is incorrect")
                            except Exception as e:
                                st.error(f"Error updating password: {str(e)}")
                        else:
                            st.error("New passwords don't match")
                    else:
                        st.error("Please fill in all password fields")
            
            with col_forgot:
                if st.button("Forgot Password?", type="secondary"):
                    try:
                        # Safety check for username
                        if not st.session_state.username:
                            st.error("Session error. Please log in again.")
                            st.stop()
                        
                        # Generate reset token using PostgreSQL
                        reset_token = authenticator.create_reset_token(st.session_state.username)
                        
                        if not reset_token:
                            st.error("Failed to generate reset token. Please try again.")
                            st.stop()
                        
                        # Get user details from database
                        user = authenticator.get_user_by_username(st.session_state.username)
                        if not user:
                            st.error("User not found. Please log in again.")
                            st.stop()
                        
                        user_name = f"{user.first_name} {user.last_name}".strip() or user.username
                        
                        # Send password reset email using the new email service
                        email_sent = email_service.send_password_reset_email(current_email, user_name, reset_token)
                        
                        if email_sent:
                            st.success("✅ Password reset email sent! Check your inbox for the reset link.")
                        else:
                            st.error("❌ Failed to send email. Please try again or contact support.")
                        
                    except Exception as e:
                        st.error(f"Error resetting password: {str(e)}")
            
            st.markdown("")
            st.info("💡 **Tip:** If you forgot your current password, use the 'Forgot Password?' button to receive a temporary password via email.")
        
        with col2:
            st.markdown("### Subscription Status")
            st.markdown("")
            
            # Force refresh subscription data from session to ensure persistence across refreshes
            session_data = load_session()
            if session_data:
                st.session_state.subscribed = session_data.get('subscribed', False)
                st.session_state.subscription_cancelled = session_data.get('subscription_cancelled', False)
                st.session_state.subscription_start_date = session_data.get('subscription_start_date', None)
            
            if st.session_state.get('subscribed', False):
                st.success("✅ Pro Member")
                st.markdown("")
                
                # Calculate proper billing date (14 days from subscription start)
                # If we have subscription start date, use it; otherwise estimate from current date
                subscription_start = st.session_state.get('subscription_start_date')
                if subscription_start:
                    try:
                        start_date = pd.to_datetime(subscription_start)
                        next_billing = start_date + pd.Timedelta(days=14)
                    except:
                        # Fallback if date parsing fails
                        next_billing = pd.Timestamp.now() + pd.Timedelta(days=13)
                else:
                    # Estimate: assume they just subscribed, so 13 days left in trial
                    next_billing = pd.Timestamp.now() + pd.Timedelta(days=13)
                
                st.write(f"Next billing date: {next_billing.strftime('%B %d, %Y')}")
                
                # Check if subscription has expired
                if pd.Timestamp.now() > next_billing:
                    # Subscription has expired, revert to free
                    st.session_state.subscribed = False
                    st.session_state.subscription_cancelled = False
                    save_session(st.session_state.username)
                    st.warning("Your Pro subscription has expired. Please upgrade to continue using Pro features.")
                    st.rerun()
                
                # Check if subscription is cancelled but still active
                is_cancelled = st.session_state.get('subscription_cancelled', False)
                if is_cancelled:
                    st.warning("⚠️ Subscription cancelled - active until billing period ends")
                    st.write(f"Access expires: {next_billing.strftime('%B %d, %Y')}")
                else:
                    st.markdown("")
                    
                    # Add confirmation dialog for cancellation
                    if 'show_cancel_confirm' not in st.session_state:
                        st.session_state.show_cancel_confirm = False
                    
                    if st.session_state.show_cancel_confirm:
                        st.warning("⚠️ Are you sure you want to cancel your subscription?")
                        st.write("Your Pro access will continue until the end of your current billing period.")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yes, Cancel", type="primary"):
                                # Mark as cancelled but keep active until billing period ends
                                st.session_state.subscription_cancelled = True
                                st.session_state.show_cancel_confirm = False
                                # Ensure subscription remains active
                                st.session_state.subscribed = True
                                save_session(st.session_state.username)
                                st.success("Subscription cancelled. You'll retain Pro access until your billing period ends.")
                                st.rerun()
                        with col2:
                            if st.button("Keep Subscription", type="secondary"):
                                st.session_state.show_cancel_confirm = False
                                st.rerun()
                    else:
                        if st.button("Cancel Subscription", type="secondary"):
                            st.session_state.show_cancel_confirm = True
                            st.rerun()
            else:
                st.warning("⚠️ Free Account")
                st.markdown("")
                st.markdown("**Upgrade to Pro for:**")
                st.markdown("• Unlimited market scans")
                st.markdown("• Unlimited stock analysis")
                st.markdown("• All 5 daily squeeze picks")
                st.markdown("• Historical performance data")
                st.markdown("• Priority support")
                st.markdown("")
                
                if st.button("Upgrade to Pro - $29/month (14-day FREE trial)", type="primary"):
                    try:
                        domain = get_current_domain()
                        # Get user email
                        user_email = get_user_email()
                        
                        # Include session ID in success URL
                        session_id = st.session_state.get('session_id', '')
                        success_url = f"{domain}?subscribed=true&user_session={session_id}" if session_id else f"{domain}?subscribed=true"
                        
                        session = stripe_handler.create_checkout_session(
                            user_id=st.session_state.get('user_id', 1),
                            email=user_email,
                            success_url=success_url,
                            cancel_url=domain
                        )
                        
                        if session:
                            st.markdown(f"[Complete Payment - Start FREE Trial]({session.url})")
                            st.info("✅ 14-day FREE trial - No charge until trial ends!")
                        else:
                            st.error("Unable to create checkout session")
                            # Show the actual Stripe error if available
                            if hasattr(stripe_handler, 'last_error') and stripe_handler.last_error:
                                st.error(f"Payment Error: {stripe_handler.last_error}")
                    except Exception as e:
                        st.error(f"Payment setup error: {str(e)}")
                        st.session_state.subscribed = True  # Demo mode
                        save_session(st.session_state.username)  # Save subscription status
                        st.success("🚀 Pro subscription activated and saved!")
                        st.rerun()
            
            st.markdown("")
            st.markdown("### Account Actions")
            st.markdown("")
            
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                # Clear database session first
                clear_session()
                
                # Clear all session state
                st.session_state.authentication_status = False
                st.session_state.authenticated = False
                st.session_state.name = None
                st.session_state.username = None
                st.session_state.free_scan_used = False
                st.session_state.free_search_used = False
                
                # Clear session ID
                if 'session_id' in st.session_state:
                    del st.session_state.session_id
                
                st.rerun()
            
            st.markdown("")
            
            # Delete account section with confirmation
            if 'show_delete_confirmation' not in st.session_state:
                st.session_state.show_delete_confirmation = False
            
            if not st.session_state.show_delete_confirmation:
                # Initial delete button with red styling
                st.markdown('<div class="delete-button">', unsafe_allow_html=True)
                if st.button("🗑️ Delete Account", type="secondary", use_container_width=True, 
                           help="Permanently delete your account and all associated data"):
                    st.session_state.show_delete_confirmation = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Confirmation dialog
                st.markdown("⚠️ **Are you sure you want to delete your account?**")
                st.markdown("This action cannot be undone and will permanently delete:")
                st.markdown("• Your account and login credentials")
                st.markdown("• All portfolio data and settings")
                st.markdown("• All saved preferences and history")
                st.markdown("")
                
                col_confirm, col_cancel = st.columns([1, 1])
                
                with col_confirm:
                    if st.button("✅ Yes, Delete My Account", type="primary", use_container_width=True):
                        try:
                            # Safety check for username
                            if not st.session_state.username:
                                st.error("Session error. Please log in again.")
                                st.stop()
                            
                            # Delete user from PostgreSQL
                            success = authenticator.delete_user(st.session_state.username)
                            
                            if not success:
                                st.error("Failed to delete account. Please try again.")
                                st.stop()
                            
                            # Delete session file if it exists
                            session_file = f"session_{st.session_state.username}.json"
                            if os.path.exists(session_file):
                                os.remove(session_file)
                            
                            # Delete portfolio data if it exists
                            portfolio_file = f"portfolio_{st.session_state.username}.json"
                            if os.path.exists(portfolio_file):
                                os.remove(portfolio_file)
                            
                            # Clear session state
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            
                            st.success("✅ Your account has been permanently deleted.")
                            st.info("You will be redirected to the login page.")
                            time.sleep(2)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error deleting account: {str(e)}")
                            st.session_state.show_delete_confirmation = False
                            st.rerun()
                
                with col_cancel:
                    if st.button("❌ Cancel", type="secondary", use_container_width=True):
                        st.session_state.show_delete_confirmation = False
                        st.rerun()

# Footer with disclaimers
st.markdown("""
<div class='disclaimer-box'>
    <h4 style='color: #00D564; margin-bottom: 1rem;'>Important Disclaimers</h4>
    <ul style='color: #9ca3af; margin-left: 1.5rem;'>
        <li>This tool provides analysis for educational purposes only</li>
        <li>Not investment advice - always consult with a qualified financial advisor</li>
        <li>Short squeezes are high-risk, high-volatility events</li>
        <li>Past performance does not predict future results</li>
        <li>Scores are algorithmic estimates based on multiple factors</li>
        <li>Always do your own research and verify data independently before making investment decisions</li>
    </ul>
    <p style='color: #6b7280; margin-top: 1rem; font-size: 0.875rem;'>
        Squeeze Ai uses advanced algorithms to analyze short interest data, borrow rates, and market momentum. 
        Our scores are for educational and informational purposes only.
    </p>
</div>
""", unsafe_allow_html=True)

# Footer with clickable text using HTML and session state
footer_html = """
<div style='text-align: center; color: #6b7280; padding: 2rem 0;'>
    <small>© 2025 Squeeze Ai | 
    <a href="?page=terms" style='color: #00D564; text-decoration: none; cursor: pointer;' 
       onclick="window.location.href='?page=terms'; return false;">Terms</a> | 
    <a href="?page=privacy" style='color: #00D564; text-decoration: none; cursor: pointer;'
       onclick="window.location.href='?page=privacy'; return false;">Privacy</a> | 
    <a href="?page=contact" style='color: #00D564; text-decoration: none; cursor: pointer;'
       onclick="window.location.href='?page=contact'; return false;">Contact</a>
    </small>
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)
