import os
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Create database engine
engine = None
SessionLocal = None
Base = declarative_base()

def init_database():
    """Initialize database connection"""
    global engine, SessionLocal
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def get_db():
    """Get database session"""
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    logged_in = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    roles = Column(String(100), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    plan_type = Column(String(20), nullable=False)  # free, pro
    status = Column(String(20), nullable=False)     # active, inactive, cancelled
    stripe_subscription_id = Column(String(100), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    success = Column(Boolean, nullable=False)
    attempt_time = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(255), nullable=True)

class ResetToken(Base):
    __tablename__ = "reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), default="new")  # new, in_progress, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database utility functions
def create_user(db, username, email, password_hash, first_name=None, last_name=None):
    """Create a new user"""
    try:
        db_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created: {username}")
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        return None

def get_user_by_username(db, username):
    """Get user by username"""
    try:
        return db.query(User).filter(User.username == username).first()
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None

def get_user_by_email(db, email):
    """Get user by email"""
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def update_user_login_status(db, username, logged_in=True):
    """Update user login status"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.logged_in = logged_in
            user.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"User login status updated: {username} -> {logged_in}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating user login status: {e}")
        db.rollback()
        return False

def log_login_attempt(db, username, success, ip_address=None, user_agent=None):
    """Log a login attempt"""
    try:
        login_attempt = LoginAttempt(
            username=username,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(login_attempt)
        db.commit()
        logger.info(f"Login attempt logged: {username} -> {success}")
        return True
    except Exception as e:
        logger.error(f"Error logging login attempt: {e}")
        db.rollback()
        return False

def save_contact_message(db, name, email, subject, message, priority):
    """Save a contact message"""
    try:
        contact_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            priority=priority
        )
        db.add(contact_msg)
        db.commit()
        db.refresh(contact_msg)
        logger.info(f"Contact message saved: {name} - {subject}")
        return contact_msg
    except Exception as e:
        logger.error(f"Error saving contact message: {e}")
        db.rollback()
        return None