import os
import secrets
from datetime import timedelta
import dotenv
dotenv.load_dotenv()

class SecurityConfig:
    """Centralized security configuration"""
    
    # Authentication settings
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION = 3600  # 1 hour lockout after max attempts
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    API_RATE_LIMIT = 100  # API calls per hour
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Input validation
    MAX_INPUT_LENGTH = 1000
    ALLOWED_FILE_EXTENSIONS = ['.txt', '.csv', '.json']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Database security
    DB_CONNECTION_TIMEOUT = 30
    MAX_DB_CONNECTIONS = 10
    
    # Encryption settings
    BCRYPT_ROUNDS = 12
    TOKEN_LENGTH = 32
    
    # HTTPS enforcement
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'
    
    # Logging
    LOG_SECURITY_EVENTS = True
    LOG_FAILED_LOGINS = True
    LOG_ADMIN_ACTIONS = True
    
    # Email security
    EMAIL_RATE_LIMIT = 5  # emails per hour per user
    
    # API security
    API_KEY_ROTATION_DAYS = 90
    WEBHOOK_TIMEOUT = 30
    
    @staticmethod
    def generate_secret_key():
        """Generate a new secret key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_secure_password(password):
        """Check if password meets security requirements"""
        import re
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters"
        
        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if SecurityConfig.REQUIRE_NUMBERS and not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password meets requirements"
    
    @staticmethod
    def sanitize_input(input_text, max_length=None):
        """Sanitize user input"""
        if not input_text:
            return ""
        
        # Truncate if too long
        max_len = max_length or SecurityConfig.MAX_INPUT_LENGTH
        if len(input_text) > max_len:
            input_text = input_text[:max_len]
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$', '{', '}']
        sanitized = input_text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        if not email or len(email) > 254:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        import re
        if not username or len(username) < 3 or len(username) > 30:
            return False
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False
        
        # Prevent reserved usernames
        reserved = ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp', 'test']
        if username.lower() in reserved:
            return False
        
        return True
    
    @staticmethod
    def get_client_ip():
        """Get client IP address (placeholder for Streamlit)"""
        # In a real deployment, you'd extract this from headers
        return "127.0.0.1"
    
    @staticmethod
    def log_security_event(event_type, details, user_id=None):
        """Log security events"""
        if not SecurityConfig.LOG_SECURITY_EVENTS:
            return
        
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Create security logs table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT,
                user_id INTEGER,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO security_logs (event_type, details, user_id, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (event_type, details, user_id, SecurityConfig.get_client_ip()))
        
        conn.commit()
        conn.close()

# Security middleware functions
def require_https():
    """Middleware to enforce HTTPS"""
    if SecurityConfig.FORCE_HTTPS:
        # In production, check if request is HTTPS
        # For Streamlit, this would be handled by reverse proxy
        pass

def add_security_headers():
    """Add security headers to response"""
    # In production, these would be added by web server or reverse proxy
    return SecurityConfig.SECURITY_HEADERS

def check_rate_limit(identifier, limit_type="general"):
    """Check if identifier has exceeded rate limits"""
    import sqlite3
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect('squeeze_ai.db')
    cursor = conn.cursor()
    
    # Create rate limit table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            limit_type TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check requests in last minute
    one_minute_ago = datetime.now() - timedelta(minutes=1)
    
    cursor.execute('''
        SELECT COUNT(*) FROM rate_limits 
        WHERE identifier = ? AND limit_type = ? AND timestamp > ?
    ''', (identifier, limit_type, one_minute_ago))
    
    count = cursor.fetchone()[0]
    
    # Log this request
    cursor.execute('''
        INSERT INTO rate_limits (identifier, limit_type)
        VALUES (?, ?)
    ''', (identifier, limit_type))
    
    # Clean old entries
    cursor.execute('''
        DELETE FROM rate_limits 
        WHERE timestamp < ?
    ''', (one_minute_ago,))
    
    conn.commit()
    conn.close()
    
    return count < SecurityConfig.RATE_LIMIT_PER_MINUTE
