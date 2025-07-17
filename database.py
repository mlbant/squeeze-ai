import sqlite3
import bcrypt
from datetime import datetime, timedelta
import secrets
import stripe
import json

class UserDatabase:
    def __init__(self, db_path='squeeze_ai.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                email_verified BOOLEAN DEFAULT 0,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expiry TIMESTAMP
            )
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                status TEXT DEFAULT 'inactive',
                plan_type TEXT DEFAULT 'free',
                started_at TIMESTAMP,
                expires_at TIMESTAMP,
                auto_renew BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Activity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                search_type TEXT,
                query TEXT,
                results TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, email, password, full_name=None):
        """Create a new user with input validation"""
        # Input validation
        if not self._validate_username(username):
            return {'success': False, 'error': 'Invalid username format'}
        if not self._validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        if not self._validate_password_strength(password):
            return {'success': False, 'error': 'Password does not meet security requirements'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hash password with higher cost factor for security
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, verification_token)
                VALUES (?, ?, ?, ?, ?)
            ''', (username.lower().strip(), email.lower().strip(), password_hash, 
                  full_name.strip() if full_name else None, verification_token))
            
            user_id = cursor.lastrowid
            
            # Create free subscription entry
            cursor.execute('''
                INSERT INTO subscriptions (user_id, status, plan_type)
                VALUES (?, 'active', 'free')
            ''', (user_id,))
            
            conn.commit()
            return {'success': True, 'user_id': user_id, 'verification_token': verification_token}
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in str(e):
                return {'success': False, 'error': 'Email already registered'}
            else:
                return {'success': False, 'error': 'Registration failed'}
        except Exception as e:
            return {'success': False, 'error': 'Database error occurred'}
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, password_hash, full_name, email, is_active, email_verified
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            if not user[4]:  # Check if account is active
                return {'success': False, 'error': 'Account is deactivated'}
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user[0],))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_id, action, details)
                VALUES (?, 'login', 'Successful login')
            ''', (user[0],))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user_id': user[0],
                'full_name': user[2],
                'email': user[3],
                'email_verified': user[5]
            }
        
        conn.close()
        return {'success': False, 'error': 'Invalid credentials'}
    
    def get_user_subscription(self, user_id):
        """Get user's subscription details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM subscriptions
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
        ''', (user_id,))
        
        sub = cursor.fetchone()
        conn.close()
        
        if sub:
            return {
                'status': sub[4],
                'plan_type': sub[5],
                'expires_at': sub[7],
                'auto_renew': sub[8],
                'stripe_subscription_id': sub[3]
            }
        return None
    
    def update_subscription(self, user_id, stripe_customer_id, stripe_subscription_id, plan_type='pro'):
        """Update user subscription after successful payment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions
            SET stripe_customer_id = ?,
                stripe_subscription_id = ?,
                status = 'active',
                plan_type = ?,
                started_at = CURRENT_TIMESTAMP,
                expires_at = datetime('now', '+1 month')
            WHERE user_id = ?
        ''', (stripe_customer_id, stripe_subscription_id, plan_type, user_id))
        
        conn.commit()
        conn.close()
    
    def log_search(self, user_id, search_type, query, results):
        """Log user search activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (user_id, search_type, query, results)
            VALUES (?, ?, ?, ?)
        ''', (user_id, search_type, query, json.dumps(results)))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """Admin function to get all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.full_name, u.created_at, 
                   u.last_login, u.is_active, s.plan_type, s.status
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            ORDER BY u.created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [{
            'id': u[0],
            'username': u[1],
            'email': u[2],
            'full_name': u[3],
            'created_at': u[4],
            'last_login': u[5],
            'is_active': u[6],
            'plan': u[7],
            'subscription_status': u[8]
        } for u in users]
    
    def get_user_stats(self):
        """Get user statistics for admin dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Active subscriptions
        cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status = "active" AND plan_type = "pro"')
        active_subs = cursor.fetchone()[0]
        
        # Today's signups
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_signups = cursor.fetchone()[0]
        
        # Revenue (simplified)
        monthly_revenue = active_subs * 29
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_subscriptions': active_subs,
            'today_signups': today_signups,
            'monthly_revenue': monthly_revenue
        }
    
    def _validate_username(self, username):
        """Validate username format and security"""
        import re
        if not username or len(username) < 3 or len(username) > 30:
            return False
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False
        # Prevent common attack patterns
        dangerous_patterns = ['admin', 'root', 'system', 'test', 'null', 'undefined']
        if username.lower() in dangerous_patterns:
            return False
        return True
    
    def _validate_email(self, email):
        """Validate email format"""
        import re
        if not email or len(email) > 254:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password_strength(self, password):
        """Validate password meets security requirements"""
        import re
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True
    
    def sanitize_input(self, input_text):
        """Sanitize user input to prevent injection attacks"""
        if not input_text:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
        sanitized = input_text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()

    def set_user_active(self, user_id, active: bool):
        """Activate or deactivate a user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active=? WHERE id=?", (1 if active else 0, user_id))
        conn.commit()
        conn.close()

    def reset_user_password(self, user_id, new_password):
        """Reset a user's password to a new value (hashed)"""
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))
        conn.commit()
        conn.close()

    def upgrade_user_to_pro(self, user_id):
        """Upgrade a user's subscription to Pro"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE subscriptions SET plan_type='pro', status='active' WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

    def get_user_growth(self):
        """Return user signup counts by date for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT DATE(created_at), COUNT(*) FROM users GROUP BY DATE(created_at) ORDER BY DATE(created_at)''')
        data = cursor.fetchall()
        conn.close()
        return data

    def get_revenue_by_month(self):
        """Return revenue totals by month for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT strftime('%Y-%m', started_at), COUNT(*)*29 FROM subscriptions WHERE plan_type='pro' AND status='active' GROUP BY strftime('%Y-%m', started_at) ORDER BY strftime('%Y-%m', started_at)''')
        data = cursor.fetchall()
        conn.close()
        return data

    def get_subscription_activity(self):
        """Return recent subscription events for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT started_at, user_id, status, plan_type FROM subscriptions ORDER BY started_at DESC LIMIT 20''')
        data = cursor.fetchall()
        conn.close()
        return data
