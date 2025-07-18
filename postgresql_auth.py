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
    
    def get_user_subscription_status(self, user_id: int) -> dict:
        """Get user's current subscription status from database"""
        try:
            if not user_id:
                return {'subscribed': False}
                
            db = next(get_db())
            
            # Check if user has an active subscription
            from database_config import Subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(['active', 'trialing'])
            ).first()
            
            if subscription:
                logger.info(f"Found active subscription for user {user_id}: {subscription.plan_type}")
                return {
                    'subscribed': True,
                    'subscription_cancelled': subscription.status == 'cancelled',
                    'subscription_start_date': subscription.started_at.isoformat() if subscription.started_at else None,
                    'plan_type': subscription.plan_type
                }
            else:
                logger.info(f"No active subscription found for user {user_id}")
                return {'subscribed': False}
                
        except Exception as e:
            logger.error(f"Error checking subscription status: {e}")
            return {'subscribed': False}
        finally:
            if 'db' in locals():
                db.close()
    
    def update_subscription(self, user_id: int, stripe_customer_id: str = None, stripe_subscription_id: str = None, plan_type: str = 'pro', status: str = 'active'):
        """Update user subscription in PostgreSQL database"""
        try:
            db = next(get_db())
            
            from database_config import Subscription
            
            # Check if subscription already exists
            subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
            
            if subscription:
                # Update existing subscription
                if stripe_subscription_id:
                    subscription.stripe_subscription_id = stripe_subscription_id
                subscription.plan_type = plan_type
                subscription.status = status
                subscription.started_at = datetime.utcnow()
                subscription.updated_at = datetime.utcnow()
                logger.info(f"Updated existing subscription for user {user_id}: {plan_type}")
            else:
                # Create new subscription
                subscription = Subscription(
                    user_id=user_id,
                    stripe_subscription_id=stripe_subscription_id,
                    plan_type=plan_type,
                    status=status,
                    started_at=datetime.utcnow()
                )
                db.add(subscription)
                logger.info(f"Created new subscription for user {user_id}: {plan_type}")
            
            db.commit()
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            if 'db' in locals():
                db.rollback()
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
            
            logger.info(f"Creating reset token for user: {username}, token: {token[:10]}..., expires at: {expires_at}")
            
            # Save reset token
            reset_token = ResetToken(
                username=username,
                token=token,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )
            
            db.add(reset_token)
            db.commit()
            
            # Verify token was saved
            saved_token = db.query(ResetToken).filter(ResetToken.token == token).first()
            if saved_token:
                logger.info(f"Reset token successfully saved to database for user: {username}")
            else:
                logger.error(f"Failed to save reset token to database for user: {username}")
            
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
            
            # Get the token directly and validate manually
            reset_token = db.query(ResetToken).filter(ResetToken.token == token).first()
            
            if not reset_token:
                logger.error(f"Reset token not found in database: {token}")
                db.close()
                return False
            
            # Manual validation with detailed logging
            current_time = datetime.utcnow()
            
            logger.info(f"VALIDATION DEBUG: Token={token[:10]}..., User={reset_token.username}, Used={reset_token.used}, Expires={reset_token.expires_at}, Current={current_time}")
            
            if reset_token.used:
                logger.error(f"Reset token already used: {token}")
                db.close()
                return False
                
            if reset_token.expires_at <= current_time:
                logger.error(f"Reset token expired: {token}, expired at {reset_token.expires_at}, current: {current_time}")
                db.close()
                return False
            
            logger.info(f"Token validation passed for user: {reset_token.username}")
            
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
            st.session_state['authentication_status'] = True
            st.session_state['username'] = username
            st.session_state['login_time'] = datetime.now()
            
            # Get user details
            user = self.get_user_by_username(username)
            if user:
                st.session_state['user_email'] = user.email
                st.session_state['user_first_name'] = user.first_name
                st.session_state['user_last_name'] = user.last_name
                st.session_state['user_roles'] = user.roles
                st.session_state['name'] = f"{user.first_name} {user.last_name}".strip() or username
                st.session_state['user_id'] = user.id
            
            # Load subscription status from database
            subscription_status = self.get_user_subscription_status(user.id if user else None)
            st.session_state['subscribed'] = subscription_status['subscribed']
            st.session_state['subscription_cancelled'] = subscription_status.get('subscription_cancelled', False)
            st.session_state['subscription_start_date'] = subscription_status.get('subscription_start_date', None)
            
            # Create database session
            from session_manager import session_manager
            session_data = {
                'username': username,
                'name': st.session_state.get('name', username),
                'subscribed': st.session_state['subscribed'],
                'subscription_cancelled': st.session_state['subscription_cancelled'],
                'subscription_start_date': st.session_state['subscription_start_date'],
                'email': user.email if user else ''
            }
            session_id = session_manager.create_session(username, session_data)
            if session_id:
                st.session_state['session_id'] = session_id
                # Add session ID to URL for persistence
                st.query_params['session_id'] = session_id
            
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
