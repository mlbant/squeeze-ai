import os
import json
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from database_config import Base, get_db, engine
import logging

logger = logging.getLogger(__name__)

class UserSession(Base):
    """Database model for user sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    username = Column(String(50), nullable=False)
    session_data = Column(Text, nullable=True)  # JSON encoded session data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

# Create the sessions table if it doesn't exist
try:
    Base.metadata.create_all(bind=engine, tables=[UserSession.__table__])
except Exception as e:
    logger.error(f"Error creating sessions table: {e}")

class SessionManager:
    """Manage user sessions in PostgreSQL database"""
    
    def __init__(self, session_timeout_hours=24):
        self.session_timeout_hours = session_timeout_hours
        self.cleanup_old_sessions()
    
    def generate_session_id(self):
        """Generate a secure session ID"""
        return secrets.token_urlsafe(48)
    
    def create_session(self, username, session_data=None):
        """Create a new session in the database"""
        try:
            db = next(get_db())
            
            # Generate session ID
            session_id = self.generate_session_id()
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
            
            # Serialize session data
            session_data_json = json.dumps(session_data) if session_data else "{}"
            
            # Create session record
            session = UserSession(
                session_id=session_id,
                username=username,
                session_data=session_data_json,
                expires_at=expires_at,
                is_active=True
            )
            
            db.add(session)
            db.commit()
            db.close()
            
            logger.info(f"Session created for user: {username}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return None
    
    def get_session(self, session_id):
        """Get session data from database"""
        try:
            db = next(get_db())
            
            logger.info(f"Looking for session: {session_id}")
            
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                logger.info(f"Session found for user: {session.username}")
                # Update last activity
                session.updated_at = datetime.utcnow()
                db.commit()
                
                # Parse session data
                session_data = json.loads(session.session_data) if session.session_data else {}
                
                result = {
                    'username': session.username,
                    'session_data': session_data,
                    'created_at': session.created_at,
                    'expires_at': session.expires_at
                }
                
                db.close()
                return result
            else:
                logger.warning(f"Session not found or expired: {session_id}")
            
            db.close()
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            if 'db' in locals():
                db.close()
            return None
    
    def update_session(self, session_id, session_data):
        """Update session data"""
        try:
            db = next(get_db())
            
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id,
                UserSession.is_active == True
            ).first()
            
            if session:
                session.session_data = json.dumps(session_data)
                session.updated_at = datetime.utcnow()
                db.commit()
                db.close()
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def extend_session(self, session_id, hours=None):
        """Extend session expiration"""
        try:
            db = next(get_db())
            
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id,
                UserSession.is_active == True
            ).first()
            
            if session:
                hours = hours or self.session_timeout_hours
                session.expires_at = datetime.utcnow() + timedelta(hours=hours)
                session.updated_at = datetime.utcnow()
                db.commit()
                db.close()
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def invalidate_session(self, session_id):
        """Invalidate a session"""
        try:
            db = next(get_db())
            
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                session.is_active = False
                session.updated_at = datetime.utcnow()
                db.commit()
                db.close()
                logger.info(f"Session invalidated: {session_id}")
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def invalidate_user_sessions(self, username):
        """Invalidate all sessions for a user"""
        try:
            db = next(get_db())
            
            sessions = db.query(UserSession).filter(
                UserSession.username == username,
                UserSession.is_active == True
            ).all()
            
            for session in sessions:
                session.is_active = False
                session.updated_at = datetime.utcnow()
            
            db.commit()
            db.close()
            
            logger.info(f"All sessions invalidated for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    def cleanup_old_sessions(self):
        """Clean up expired sessions"""
        try:
            db = next(get_db())
            
            # Delete sessions older than 30 days or expired
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            deleted = db.query(UserSession).filter(
                (UserSession.expires_at < datetime.utcnow()) | 
                (UserSession.created_at < cutoff_date)
            ).delete()
            
            db.commit()
            db.close()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old sessions")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return 0
    
    def get_active_sessions_count(self, username=None):
        """Get count of active sessions"""
        try:
            db = next(get_db())
            
            query = db.query(UserSession).filter(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
            
            if username:
                query = query.filter(UserSession.username == username)
            
            count = query.count()
            db.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting active sessions: {e}")
            if 'db' in locals():
                db.close()
            return 0

# Create global session manager instance
session_manager = SessionManager()
