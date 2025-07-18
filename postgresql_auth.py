import streamlit as st
import bcrypt
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from database_config import init_database, get_db, User, ResetToken, log_login_attempt
from sqlalchemy.orm import Session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLAuthenticator:
    """PostgreSQL-based authentication system"""
    
    def __init__(self):
        self.cookie_name = "squeeze_ai_auth"
        self.cookie_expiry_days = 30
        
        # Initialize database
        if not init_database():
            logger.error("Failed to initialize database")
            st.error("Database connection failed. Please try again later.")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def generate_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def get_user_by_username(self, username: str) -> User:
        """Get user by username from database"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            db.close()
            return user
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> User:
        """Get user by email from database"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.email == email).first()
            db.close()
            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def create_user(self, username: str, email: str, password: str, first_name: str = "", last_name: str = "") -> bool:
        """Create a new user account"""
        try:
            db = next(get_db())
            
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                db.close()
                return False
            
            # Create new user
            password_hash = self.hash_password(password)
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            db.close()
            
            logger.info(f"User created successfully: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                # Log failed attempt
                log_login_attempt(db, username, False)
                db.close()
                return False
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1
                user.updated_at = datetime.utcnow()
                db.commit()
                
                # Log failed attempt
                log_login_attempt(db, username, False)
                db.close()
                return False
            
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.logged_in = True
            user.updated_at = datetime.utcnow()
            db.commit()
            
            # Log successful attempt
            log_login_attempt(db, username, True)
            db.close()
            
            logger.info(f"User authenticated successfully: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            if 'db' in locals():
                db.close()
            return False
    
    def logout_user(self, username: str) -> bool:
        """Log out user"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            
            if user:
                user.logged_in = False
                user.updated_at = datetime.utcnow()
                db.commit()
                db.close()
                logger.info(f"User logged out: {username}")
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            if 'db' in locals():
                db.close()
            return False
    
    def create_reset_token(self, username: str) -> str:
        """Create a password reset token"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                db.close()
                return None
            
            # Generate reset token
            token = self.generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Save reset token
            reset_token = ResetToken(
                username=username,
                token=token,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )
            
            db.add(reset_token)
            db.commit()
            db.close()
            
            logger.info(f"Reset token created for user: {username}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating reset token: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        try:
            db = next(get_db())
            reset_token = db.query(ResetToken).filter(
                ResetToken.token == token,
                ResetToken.used == False,
                ResetToken.expires_at > datetime.utcnow()
            ).first()
            
            if not reset_token:
                db.close()
                return False
            
            # Get user and update password
            user = db.query(User).filter(User.username == reset_token.username).first()
            if not user:
                db.close()
                return False
            
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token.used = True
            
            db.commit()
            db.close()
            
            logger.info(f"Password reset successfully for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def login(self, username: str, password: str) -> bool:
        """Login user and set session"""
        if self.authenticate_user(username, password):
            # Set session state
            st.session_state['authenticated'] = True
            st.session_state['username'] = username
            st.session_state['login_time'] = datetime.now()
            
            # Get user details
            user = self.get_user_by_username(username)
            if user:
                st.session_state['user_email'] = user.email
                st.session_state['user_first_name'] = user.first_name
                st.session_state['user_last_name'] = user.last_name
                st.session_state['user_roles'] = user.roles
            
            return True
        return False
    
    def logout(self):
        """Logout user and clear session"""
        if 'username' in st.session_state:
            self.logout_user(st.session_state['username'])
        
        # Clear session state
        for key in ['authenticated', 'username', 'login_time', 'user_email', 
                   'user_first_name', 'user_last_name', 'user_roles']:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_username(self) -> str:
        """Get current username"""
        return st.session_state.get('username', '')
    
    def require_auth(self, redirect_to_login: bool = True):
        """Require authentication decorator"""
        if not self.is_authenticated():
            if redirect_to_login:
                st.warning("Please log in to access this page.")
                st.stop()
            return False
        return True
    
    def get_user_stats(self) -> dict:
        """Get user statistics for admin panel"""
        try:
            db = next(get_db())
            
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.logged_in == True).count()
            failed_attempts = db.query(User).filter(User.failed_login_attempts > 0).count()
            
            db.close()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'failed_attempts': failed_attempts
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total_users': 0, 'active_users': 0, 'failed_attempts': 0}
    
    def get_all_users(self) -> list:
        """Get all users for admin panel"""
        try:
            db = next(get_db())
            users = db.query(User).all()
            db.close()
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def change_password(self, username: str, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                db.close()
                return False
            
            # Verify current password
            if not self.verify_password(current_password, user.password_hash):
                db.close()
                return False
            
            # Update password
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
            db.close()
            
            logger.info(f"Password changed successfully for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def delete_user(self, username: str) -> bool:
        """Delete a user account"""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                db.close()
                return False
            
            # Delete user
            db.delete(user)
            db.commit()
            db.close()
            
            logger.info(f"User deleted successfully: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False

# Create global authenticator instance
authenticator = PostgreSQLAuthenticator()