#!/usr/bin/env python3
"""
Migration script to move data from config.yaml and SQLite to PostgreSQL
"""

import os
import yaml
import sqlite3
import bcrypt
from datetime import datetime
from sqlalchemy.orm import Session
from database_config import init_database, get_db, create_user, User, Subscription, LoginAttempt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config_yaml():
    """Load existing config.yaml file"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logger.warning("config.yaml not found - no user data to migrate")
        return None
    except Exception as e:
        logger.error(f"Error loading config.yaml: {e}")
        return None

def migrate_users_from_config(db: Session):
    """Migrate users from config.yaml to PostgreSQL"""
    config = load_config_yaml()
    if not config:
        return 0
    
    users = config.get('credentials', {}).get('usernames', {})
    migrated_count = 0
    
    for username, user_data in users.items():
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                logger.info(f"User {username} already exists - skipping")
                continue
            
            # Create new user
            user = User(
                username=username,
                email=user_data.get('email', f"{username}@example.com"),
                password_hash=user_data.get('password', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                logged_in=user_data.get('logged_in', False),
                failed_login_attempts=user_data.get('failed_login_attempts', 0),
                roles=user_data.get('roles', 'user'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            migrated_count += 1
            logger.info(f"Migrated user: {username}")
            
        except Exception as e:
            logger.error(f"Error migrating user {username}: {e}")
            db.rollback()
    
    return migrated_count

def migrate_sqlite_data(db: Session):
    """Migrate data from SQLite database"""
    try:
        # Connect to SQLite database
        sqlite_conn = sqlite3.connect('squeeze_ai.db')
        cursor = sqlite_conn.cursor()
        
        # Migrate subscriptions
        try:
            cursor.execute("SELECT * FROM subscriptions")
            subscriptions = cursor.fetchall()
            
            for sub in subscriptions:
                try:
                    subscription = Subscription(
                        user_id=sub[1],  # user_id
                        plan_type=sub[2],  # plan_type
                        status=sub[3],  # status
                        started_at=datetime.fromisoformat(sub[4]) if sub[4] else datetime.utcnow(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(subscription)
                    db.commit()
                    logger.info(f"Migrated subscription: user_id={sub[1]}, plan={sub[2]}")
                except Exception as e:
                    logger.error(f"Error migrating subscription: {e}")
                    db.rollback()
        except sqlite3.OperationalError:
            logger.warning("No subscriptions table found in SQLite")
        
        # Migrate login attempts
        try:
            cursor.execute("SELECT * FROM login_attempts")
            login_attempts = cursor.fetchall()
            
            for attempt in login_attempts:
                try:
                    login_attempt = LoginAttempt(
                        username=attempt[1],  # username
                        success=bool(attempt[2]),  # success
                        ip_address=attempt[3],  # ip_address
                        attempt_time=datetime.fromisoformat(attempt[4]) if attempt[4] else datetime.utcnow(),
                        user_agent=attempt[5] if len(attempt) > 5 else None
                    )
                    db.add(login_attempt)
                    db.commit()
                    logger.info(f"Migrated login attempt: {attempt[1]}")
                except Exception as e:
                    logger.error(f"Error migrating login attempt: {e}")
                    db.rollback()
        except sqlite3.OperationalError:
            logger.warning("No login_attempts table found in SQLite")
        
        sqlite_conn.close()
        return True
        
    except FileNotFoundError:
        logger.warning("squeeze_ai.db not found - no SQLite data to migrate")
        return False
    except Exception as e:
        logger.error(f"Error migrating SQLite data: {e}")
        return False

def create_admin_user(db: Session):
    """Create admin user if it doesn't exist"""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == admin_username).first()
    if admin_user:
        logger.info("Admin user already exists")
        return
    
    # Hash admin password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create admin user
    admin = User(
        username=admin_username,
        email="admin@squeeze-ai.com",
        password_hash=password_hash,
        first_name="Admin",
        last_name="User",
        roles="admin",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    logger.info(f"Created admin user: {admin_username}")

def main():
    """Main migration function"""
    logger.info("Starting PostgreSQL migration...")
    
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
        return
    
    # Get database session
    db = next(get_db())
    
    try:
        # Migrate users from config.yaml
        user_count = migrate_users_from_config(db)
        logger.info(f"Migrated {user_count} users from config.yaml")
        
        # Migrate SQLite data
        sqlite_success = migrate_sqlite_data(db)
        if sqlite_success:
            logger.info("SQLite data migration completed")
        
        # Create admin user
        create_admin_user(db)
        
        # Show summary
        total_users = db.query(User).count()
        total_subscriptions = db.query(Subscription).count()
        total_login_attempts = db.query(LoginAttempt).count()
        
        logger.info(f"""
        Migration Summary:
        - Total Users: {total_users}
        - Total Subscriptions: {total_subscriptions}
        - Total Login Attempts: {total_login_attempts}
        """)
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()