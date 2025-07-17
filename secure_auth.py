import streamlit as st
import bcrypt
import secrets
import time
import re
import sqlite3
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dotenv
dotenv.load_dotenv()

class SecureAuth:
    def __init__(self):
        self.max_attempts = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', 3600))
        self.init_security_tables()
    
    def init_security_tables(self):
        """Initialize security-related database tables"""
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Login attempts tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                username TEXT,
                attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 0
            )
        ''')
        
        # Session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Password reset tokens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                used BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def validate_input(self, input_text, input_type="general"):
        """Validate and sanitize user inputs"""
        if not input_text:
            return False, "Input cannot be empty"
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        for char in dangerous_chars:
            if char in input_text:
                return False, f"Invalid character '{char}' not allowed"
        
        if input_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, input_text):
                return False, "Invalid email format"
            if len(input_text) > 254:
                return False, "Email too long"
        
        elif input_type == "username":
            if not re.match(r'^[a-zA-Z0-9_-]+$', input_text):
                return False, "Username can only contain letters, numbers, hyphens, and underscores"
            if len(input_text) < 3 or len(input_text) > 30:
                return False, "Username must be 3-30 characters long"
        
        elif input_type == "password":
            if len(input_text) < 8:
                return False, "Password must be at least 8 characters long"
            if not re.search(r'[A-Z]', input_text):
                return False, "Password must contain at least one uppercase letter"
            if not re.search(r'[a-z]', input_text):
                return False, "Password must contain at least one lowercase letter"
            if not re.search(r'[0-9]', input_text):
                return False, "Password must contain at least one number"
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', input_text):
                return False, "Password must contain at least one special character"
        
        return True, "Valid"
    
    def hash_password(self, password):
        """Securely hash password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def check_rate_limit(self, identifier, limit_type="login"):
        """Check if user/IP has exceeded rate limits"""
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Check login attempts in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM login_attempts 
            WHERE (ip_address = ? OR username = ?) 
            AND attempt_time > ? 
            AND success = 0
        ''', (identifier, identifier, one_hour_ago))
        
        failed_attempts = cursor.fetchone()[0]
        conn.close()
        
        return failed_attempts < self.max_attempts
    
    def log_login_attempt(self, username, ip_address, success):
        """Log login attempt for security monitoring"""
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts (username, ip_address, success)
            VALUES (?, ?, ?)
        ''', (username, ip_address, success))
        
        conn.commit()
        conn.close()
    
    def create_session(self, user_id, ip_address="unknown", user_agent="unknown"):
        """Create secure session token"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Invalidate old sessions
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 
            WHERE user_id = ?
        ''', (user_id,))
        
        # Create new session
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, expires_at, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return session_token
    
    def validate_session(self, session_token):
        """Validate session token"""
        if not session_token:
            return False, None
        
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, expires_at FROM user_sessions 
            WHERE session_token = ? AND is_active = 1
        ''', (session_token,))
        
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            return False, None
        
        user_id, expires_at = session
        expires_at = datetime.fromisoformat(expires_at)
        
        if datetime.now() > expires_at:
            self.invalidate_session(session_token)
            return False, None
        
        return True, user_id
    
    def invalidate_session(self, session_token):
        """Invalidate session token"""
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 
            WHERE session_token = ?
        ''', (session_token,))
        
        conn.commit()
        conn.close()
    
    def secure_login_form(self):
        """Display secure login form with rate limiting"""
        st.subheader("🔐 Secure Login")
        
        # Check if user is already logged in
        if 'session_token' in st.session_state:
            valid, user_id = self.validate_session(st.session_state.session_token)
            if valid:
                return True, user_id
            else:
                del st.session_state.session_token
        
        with st.form("secure_login_form"):
            username = st.text_input("Username", max_chars=30)
            password = st.text_input("Password", type="password", max_chars=128)
            submit = st.form_submit_button("Login")
            
            if submit:
                # Validate inputs
                valid_username, username_msg = self.validate_input(username, "username")
                valid_password, password_msg = self.validate_input(password, "password")
                
                if not valid_username:
                    st.error(f"Username error: {username_msg}")
                    return False, None
                
                if not valid_password:
                    st.error(f"Password error: {password_msg}")
                    return False, None
                
                # Check rate limiting
                client_ip = st.session_state.get('client_ip', 'unknown')
                if not self.check_rate_limit(username):
                    st.error("Too many failed login attempts. Please try again later.")
                    return False, None
                
                # Attempt login
                success, user_data = self.authenticate_user(username, password)
                self.log_login_attempt(username, client_ip, success)
                
                if success:
                    # Create secure session
                    session_token = self.create_session(user_data['user_id'], client_ip)
                    st.session_state.session_token = session_token
                    st.session_state.user_id = user_data['user_id']
                    st.session_state.username = username
                    st.session_state.email = user_data['email']
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        return False, None
    
    def authenticate_user(self, username, password):
        """Authenticate user with secure password verification"""
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, password_hash, email, is_active, email_verified
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if user and self.verify_password(password, user[1]):
            if not user[3]:  # Check if account is active
                conn.close()
                return False, {"error": "Account is deactivated"}
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user[0],))
            
            conn.commit()
            conn.close()
            
            return True, {
                'user_id': user[0],
                'email': user[2],
                'email_verified': user[4]
            }
        
        conn.close()
        return False, {"error": "Invalid credentials"}
    
    def secure_logout(self):
        """Secure logout with session cleanup"""
        if 'session_token' in st.session_state:
            self.invalidate_session(st.session_state.session_token)
            del st.session_state.session_token
        
        # Clear all session data
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.success("Logged out successfully!")
        st.rerun()
    
    def require_auth(self):
        """Decorator function to require authentication"""
        if 'session_token' not in st.session_state:
            st.warning("Please login to access this feature")
            return False
        
        valid, user_id = self.validate_session(st.session_state.session_token)
        if not valid:
            st.warning("Session expired. Please login again.")
            if 'session_token' in st.session_state:
                del st.session_state.session_token
            return False
        
        return True
    
    def generate_csrf_token(self):
        """Generate CSRF token for forms"""
        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = secrets.token_urlsafe(32)
        return st.session_state.csrf_token
    
    def validate_csrf_token(self, token):
        """Validate CSRF token"""
        return token == st.session_state.get('csrf_token')

# Initialize secure auth
secure_auth = SecureAuth()
