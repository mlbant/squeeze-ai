import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import bcrypt
import yaml
from yaml.loader import SafeLoader
import sqlite3
import json
from collections import defaultdict
import dotenv
dotenv.load_dotenv()

st.set_page_config(
    page_title="Squeeze Ai Admin Dashboard",
    page_icon="🔐",
    layout="wide"
)

# Helper functions for YAML user management
def load_config():
    """Load the config.yaml file"""
    try:
        with open('config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except FileNotFoundError:
        st.error("config.yaml not found!")
        return None
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return None

def save_config(config):
    """Save the config.yaml file"""
    try:
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

def get_subscription_data():
    """Get subscription data from SQLite database"""
    try:
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Get subscription stats
        cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status = "active" AND plan_type = "pro"')
        pro_subs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status = "active"')
        total_subs = cursor.fetchone()[0]
        
        # Get recent subscription activity
        cursor.execute('''
            SELECT started_at, user_id, status, plan_type 
            FROM subscriptions 
            ORDER BY started_at DESC 
            LIMIT 10
        ''')
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        return {
            'pro_subscriptions': pro_subs,
            'total_subscriptions': total_subs,
            'monthly_revenue': pro_subs * 29,
            'recent_activity': recent_activity
        }
    except Exception as e:
        st.error(f"Database error: {e}")
        return {
            'pro_subscriptions': 0,
            'total_subscriptions': 0,
            'monthly_revenue': 0,
            'recent_activity': []
        }

def get_analytics_data():
    """Get comprehensive analytics data from various sources"""
    try:
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Login attempts analytics
        cursor.execute('''
            SELECT DATE(attempt_time) as date, COUNT(*) as attempts, 
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM login_attempts 
            WHERE attempt_time >= DATE('now', '-30 days')
            GROUP BY DATE(attempt_time)
            ORDER BY DATE(attempt_time)
        ''')
        login_data = cursor.fetchall()
        
        # Failed login attempts by user
        cursor.execute('''
            SELECT username, COUNT(*) as failed_attempts
            FROM login_attempts 
            WHERE success = 0 AND attempt_time >= DATE('now', '-7 days')
            GROUP BY username
            ORDER BY failed_attempts DESC
            LIMIT 10
        ''')
        failed_logins = cursor.fetchall()
        
        # Subscription growth over time
        cursor.execute('''
            SELECT DATE(started_at) as date, plan_type, COUNT(*) as count
            FROM subscriptions 
            WHERE started_at >= DATE('now', '-30 days')
            GROUP BY DATE(started_at), plan_type
            ORDER BY DATE(started_at)
        ''')
        subscription_growth = cursor.fetchall()
        
        # Revenue by month (last 6 months)
        cursor.execute('''
            SELECT strftime('%Y-%m', started_at) as month, 
                   COUNT(*) * 29 as revenue
            FROM subscriptions 
            WHERE plan_type = 'pro' AND status = 'active'
            AND started_at >= DATE('now', '-6 months')
            GROUP BY strftime('%Y-%m', started_at)
            ORDER BY strftime('%Y-%m', started_at)
        ''')
        revenue_data = cursor.fetchall()
        
        # Admin activity
        cursor.execute('''
            SELECT COUNT(*) as total_attempts,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_logins
            FROM login_attempts 
            WHERE ip_address = 'admin_panel'
        ''')
        admin_activity = cursor.fetchone()
        
        # User registration trends (based on config file analysis)
        config = load_config()
        users = config.get('credentials', {}).get('usernames', {}) if config else {}
        
        # Activity by hour (login attempts)
        cursor.execute('''
            SELECT strftime('%H', attempt_time) as hour, COUNT(*) as attempts
            FROM login_attempts 
            WHERE attempt_time >= DATE('now', '-7 days')
            GROUP BY strftime('%H', attempt_time)
            ORDER BY hour
        ''')
        hourly_activity = cursor.fetchall()
        
        conn.close()
        
        return {
            'login_data': login_data,
            'failed_logins': failed_logins,
            'subscription_growth': subscription_growth,
            'revenue_data': revenue_data,
            'admin_activity': admin_activity,
            'users': users,
            'hourly_activity': hourly_activity
        }
    except Exception as e:
        st.error(f"Analytics error: {e}")
        return {
            'login_data': [],
            'failed_logins': [],
            'subscription_growth': [],
            'revenue_data': [],
            'admin_activity': (0, 0),
            'users': {},
            'hourly_activity': []
        }

def get_user_analytics():
    """Get user analytics from the config file"""
    config = load_config()
    if not config:
        return {}
    
    users = config.get('credentials', {}).get('usernames', {})
    
    # Calculate analytics
    total_users = len(users)
    active_users = sum(1 for u in users.values() if u.get('logged_in', False))
    failed_logins = sum(u.get('failed_login_attempts', 0) for u in users.values())
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'failed_logins': failed_logins,
        'users': users
    }

# Secure admin authentication
def verify_admin_credentials(username, password):
    """Verify admin credentials securely"""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    
    if not admin_password or admin_password == "your_secure_admin_password_here":
        st.error("⚠️ SECURITY WARNING: Admin password not configured! Set ADMIN_PASSWORD in .env file")
        return False
    
    # Hash the stored password if it's not already hashed
    if not admin_password.startswith('$2b$'):
        # First time - hash the password and show it to admin
        hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        st.warning(f"⚠️ Update your .env file with this hashed password: ADMIN_PASSWORD={hashed.decode('utf-8')}")
        return username == admin_username and password == admin_password
    else:
        # Use hashed password verification
        return username == admin_username and bcrypt.checkpw(password.encode('utf-8'), admin_password.encode('utf-8'))

# Admin login
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.title("🔐 Admin Login")
    st.warning("⚠️ Restricted Access - Authorized Personnel Only")
    
    with st.form("admin_login_form"):
        username = st.text_input("Username", max_chars=50)
        password = st.text_input("Password", type="password", max_chars=128)
        submit = st.form_submit_button("Login")
        
        if submit:
            if verify_admin_credentials(username, password):
                st.session_state.admin_logged_in = True
                st.session_state.admin_username = username
                st.success("Admin login successful!")
                st.rerun()
            else:
                st.error("Invalid admin credentials")
    st.stop()

# Admin Dashboard
st.title("🔐 Squeeze Ai Admin Dashboard")

# Logout button
if st.button("Logout", type="secondary"):
    st.session_state.admin_logged_in = False
    st.rerun()

# Get data
user_analytics = get_user_analytics()
subscription_data = get_subscription_data()
analytics_data = get_analytics_data()

# Display key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Users", user_analytics.get('total_users', 0))
with col2:
    st.metric("Pro Subscribers", subscription_data.get('pro_subscriptions', 0))
with col3:
    st.metric("Monthly Revenue", f"${subscription_data.get('monthly_revenue', 0):,}")
with col4:
    active_users = user_analytics.get('active_users', 0)
    total_users = user_analytics.get('total_users', 1)
    conversion_rate = (subscription_data.get('pro_subscriptions', 0) / max(total_users, 1)) * 100
    st.metric("Conversion Rate", f"{conversion_rate:.1f}%")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "💳 Subscriptions", "📊 Analytics", "⚙️ Settings"])

with tab1:
    st.subheader("User Management")
    
    users = user_analytics.get('users', {})
    
    if users:
        # Convert to DataFrame for display
        user_data = []
        for username, user_info in users.items():
            user_data.append({
                'username': username,
                'email': user_info.get('email', 'N/A'),
                'name': user_info.get('name', f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}").strip(),
                'logged_in': user_info.get('logged_in', False),
                'failed_attempts': user_info.get('failed_login_attempts', 0),
                'roles': user_info.get('roles', 'user')
            })
        
        df = pd.DataFrame(user_data)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Logged In", "Not Logged In"])
        with col2:
            failed_filter = st.checkbox("Show Users with Failed Attempts", value=False)
        with col3:
            search = st.text_input("Search users", placeholder="Username or email...")
        
        # Apply filters
        filtered_df = df.copy()
        if status_filter == "Logged In":
            filtered_df = filtered_df[filtered_df['logged_in'] == True]
        elif status_filter == "Not Logged In":
            filtered_df = filtered_df[filtered_df['logged_in'] == False]
        
        if failed_filter:
            filtered_df = filtered_df[filtered_df['failed_attempts'] > 0]
        
        if search:
            filtered_df = filtered_df[
                filtered_df['username'].str.contains(search, case=False, na=False) |
                filtered_df['email'].str.contains(search, case=False, na=False)
            ]
        
        # Display users
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "username": "Username",
                "email": "Email",
                "name": "Full Name",
                "logged_in": st.column_config.CheckboxColumn("Currently Logged In"),
                "failed_attempts": st.column_config.NumberColumn("Failed Login Attempts"),
                "roles": "Roles"
            }
        )
        
        # User management actions
        st.subheader("User Actions")
        selected_username = st.selectbox("Select User", [""] + list(users.keys()))
        
        if selected_username:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reset Failed Login Attempts"):
                    config = load_config()
                    if config:
                        config['credentials']['usernames'][selected_username]['failed_login_attempts'] = 0
                        if save_config(config):
                            st.success(f"Reset failed login attempts for {selected_username}")
                            st.rerun()
                
                if st.button("Force Logout User"):
                    config = load_config()
                    if config:
                        config['credentials']['usernames'][selected_username]['logged_in'] = False
                        if save_config(config):
                            st.success(f"Forced logout for {selected_username}")
                            st.rerun()
            
            with col2:
                new_password = st.text_input("New Password", type="password", key="new_pass")
                if st.button("Reset Password") and new_password:
                    config = load_config()
                    if config:
                        # Hash the new password
                        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                        config['credentials']['usernames'][selected_username]['password'] = hashed.decode('utf-8')
                        if save_config(config):
                            st.success(f"Password reset for {selected_username}")
                            st.rerun()
                
                if st.button("Delete User"):
                    config = load_config()
                    if config:
                        if selected_username in config['credentials']['usernames']:
                            del config['credentials']['usernames'][selected_username]
                            if save_config(config):
                                st.success(f"User {selected_username} deleted")
                                st.rerun()
    else:
        st.info("No users found in the system")

with tab2:
    st.subheader("Subscription Management")
    
    # Subscription stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pro Subscriptions", subscription_data.get('pro_subscriptions', 0))
    with col2:
        st.metric("Total Subscriptions", subscription_data.get('total_subscriptions', 0))
    with col3:
        st.metric("Monthly Revenue", f"${subscription_data.get('monthly_revenue', 0):,}")
    
    # Recent subscription activity
    st.subheader("Recent Subscription Activity")
    recent_activity = subscription_data.get('recent_activity', [])
    
    if recent_activity:
        activity_df = pd.DataFrame(recent_activity, columns=["Date", "User ID", "Status", "Plan"])
        st.dataframe(activity_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent subscription activity found")
    
    # Manual subscription management
    st.subheader("Manual Subscription Management")
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.number_input("User ID", min_value=1, step=1)
        plan_type = st.selectbox("Plan Type", ["free", "pro"])
    with col2:
        status = st.selectbox("Status", ["active", "inactive", "cancelled"])
        
    if st.button("Update Subscription"):
        try:
            conn = sqlite3.connect('squeeze_ai.db')
            cursor = conn.cursor()
            
            # Check if user exists in subscriptions
            cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()[0]
            
            if exists:
                cursor.execute('''
                    UPDATE subscriptions 
                    SET plan_type = ?, status = ?, started_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (plan_type, status, user_id))
            else:
                cursor.execute('''
                    INSERT INTO subscriptions (user_id, plan_type, status, started_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, plan_type, status))
            
            conn.commit()
            conn.close()
            st.success(f"Subscription updated for user {user_id}")
            st.rerun()
        except Exception as e:
            st.error(f"Error updating subscription: {e}")

with tab3:
    st.subheader("📊 Analytics Dashboard")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", user_analytics.get('total_users', 0))
    with col2:
        st.metric("Active Users", user_analytics.get('active_users', 0))
    with col3:
        admin_activity = analytics_data.get('admin_activity', (0, 0))
        st.metric("Admin Logins", admin_activity[1])
    with col4:
        st.metric("Failed Logins (7d)", len(analytics_data.get('failed_logins', [])))
    
    # Login Activity Analysis
    st.subheader("🔐 Login Activity Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        # Login attempts over time
        login_data = analytics_data.get('login_data', [])
        if login_data:
            login_df = pd.DataFrame(login_data, columns=['Date', 'Total Attempts', 'Successful'])
            login_df['Failed'] = login_df['Total Attempts'] - login_df['Successful']
            
            fig = px.line(login_df, x='Date', y=['Successful', 'Failed'], 
                         title="Login Attempts Over Time (Last 30 Days)")
            fig.update_layout(xaxis_title="Date", yaxis_title="Number of Attempts")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No login data available for the last 30 days")
    
    with col2:
        # Failed login attempts by user
        failed_logins = analytics_data.get('failed_logins', [])
        if failed_logins:
            failed_df = pd.DataFrame(failed_logins, columns=['Username', 'Failed Attempts'])
            fig = px.bar(failed_df, x='Username', y='Failed Attempts', 
                        title="Failed Login Attempts by User (Last 7 Days)")
            fig.update_layout(xaxis_title="Username", yaxis_title="Failed Attempts")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No failed login attempts in the last 7 days")
    
    # Activity by hour
    st.subheader("⏰ Activity Patterns")
    col1, col2 = st.columns(2)
    
    with col1:
        hourly_activity = analytics_data.get('hourly_activity', [])
        if hourly_activity:
            hourly_df = pd.DataFrame(hourly_activity, columns=['Hour', 'Attempts'])
            hourly_df['Hour'] = hourly_df['Hour'].astype(int)
            
            fig = px.bar(hourly_df, x='Hour', y='Attempts', 
                        title="Login Activity by Hour (Last 7 Days)")
            fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Login Attempts")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hourly activity data available")
    
    with col2:
        # User status distribution
        if user_analytics.get('users'):
            status_data = {
                'Logged In': user_analytics.get('active_users', 0),
                'Not Logged In': user_analytics.get('total_users', 0) - user_analytics.get('active_users', 0)
            }
            
            fig = px.pie(values=list(status_data.values()), names=list(status_data.keys()),
                        title="Current User Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    # Subscription Analytics
    st.subheader("💰 Subscription & Revenue Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        # Revenue over time
        revenue_data = analytics_data.get('revenue_data', [])
        if revenue_data:
            revenue_df = pd.DataFrame(revenue_data, columns=['Month', 'Revenue'])
            fig = px.bar(revenue_df, x='Month', y='Revenue', 
                        title="Monthly Revenue (Pro Subscriptions)")
            fig.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Show current month revenue
            current_revenue = subscription_data.get('monthly_revenue', 0)
            st.metric("Current Monthly Revenue", f"${current_revenue}")
            st.info("Historical revenue data will appear as subscriptions are processed over time")
    
    with col2:
        # Subscription distribution
        sub_data = {
            'Free': user_analytics.get('total_users', 0) - subscription_data.get('pro_subscriptions', 0),
            'Pro': subscription_data.get('pro_subscriptions', 0)
        }
        
        fig = px.pie(values=list(sub_data.values()), names=list(sub_data.keys()),
                    title="Subscription Plan Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent Activity Summary
    st.subheader("📈 Recent Activity Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔑 Security Metrics**")
        admin_total, admin_success = analytics_data.get('admin_activity', (0, 0))
        admin_fail_rate = ((admin_total - admin_success) / max(admin_total, 1)) * 100
        st.metric("Admin Login Success Rate", f"{100 - admin_fail_rate:.1f}%")
        st.metric("Total Admin Attempts", admin_total)
    
    with col2:
        st.markdown("**👥 User Engagement**")
        total_users = user_analytics.get('total_users', 0)
        active_users = user_analytics.get('active_users', 0)
        engagement_rate = (active_users / max(total_users, 1)) * 100
        st.metric("User Engagement Rate", f"{engagement_rate:.1f}%")
        st.metric("Users with Failed Logins", len(analytics_data.get('failed_logins', [])))
    
    with col3:
        st.markdown("**💼 Business Metrics**")
        conversion_rate = (subscription_data.get('pro_subscriptions', 0) / max(total_users, 1)) * 100
        st.metric("Pro Conversion Rate", f"{conversion_rate:.1f}%")
        st.metric("Monthly Revenue", f"${subscription_data.get('monthly_revenue', 0)}")
    
    # Data Export
    st.subheader("📊 Export Analytics Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Login Data"):
            if login_data:
                login_df = pd.DataFrame(login_data, columns=['Date', 'Total Attempts', 'Successful'])
                csv = login_df.to_csv(index=False)
                st.download_button(
                    label="Download Login Analytics CSV",
                    data=csv,
                    file_name=f"login_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No login data to export")
    
    with col2:
        if st.button("Export User Data"):
            if user_analytics.get('users'):
                users_list = []
                for username, user_info in user_analytics['users'].items():
                    users_list.append({
                        'username': username,
                        'email': user_info.get('email', ''),
                        'logged_in': user_info.get('logged_in', False),
                        'failed_attempts': user_info.get('failed_login_attempts', 0)
                    })
                users_df = pd.DataFrame(users_list)
                csv = users_df.to_csv(index=False)
                st.download_button(
                    label="Download User Analytics CSV",
                    data=csv,
                    file_name=f"user_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.button("Export Revenue Data"):
            if revenue_data:
                revenue_df = pd.DataFrame(revenue_data, columns=['Month', 'Revenue'])
                csv = revenue_df.to_csv(index=False)
                st.download_button(
                    label="Download Revenue Analytics CSV",
                    data=csv,
                    file_name=f"revenue_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No revenue data to export")

with tab4:
    st.subheader("System Settings")
    
    # Configuration management
    st.markdown("### System Configuration")
    config = load_config()
    
    if config:
        # Cookie settings
        st.markdown("#### Cookie Settings")
        cookie_expiry = st.number_input("Cookie Expiry Days", value=config.get('cookie', {}).get('expiry_days', 30))
        cookie_name = st.text_input("Cookie Name", value=config.get('cookie', {}).get('name', 'squeeze_ai_cookie'))
        
        # Pre-authorized emails
        st.markdown("#### Pre-authorized Emails")
        preauth_emails = st.text_area(
            "Pre-authorized Emails (one per line)",
            value="\n".join(config.get('preauthorized', {}).get('emails', []))
        )
        
        if st.button("Save Configuration"):
            config['cookie']['expiry_days'] = cookie_expiry
            config['cookie']['name'] = cookie_name
            config['preauthorized']['emails'] = [email.strip() for email in preauth_emails.split('\n') if email.strip()]
            
            if save_config(config):
                st.success("Configuration saved successfully!")
                st.rerun()
    
    # Database management
    st.markdown("### Database Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Backup Database"):
            try:
                # Create a backup of the database
                backup_name = f"backup_squeeze_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                os.system(f'copy squeeze_ai.db {backup_name}')
                st.success(f"Database backed up as {backup_name}")
            except Exception as e:
                st.error(f"Backup failed: {e}")
    
    with col2:
        if st.button("Clear Failed Login Attempts"):
            config = load_config()
            if config:
                for username in config['credentials']['usernames']:
                    config['credentials']['usernames'][username]['failed_login_attempts'] = 0
                
                if save_config(config):
                    st.success("All failed login attempts cleared")
                    st.rerun()
    
    # System statistics
    st.markdown("### System Statistics")
    
    try:
        # Database size
        db_size = os.path.getsize('squeeze_ai.db') / (1024 * 1024)  # Size in MB
        st.metric("Database Size", f"{db_size:.2f} MB")
        
        # Config file info
        config_size = os.path.getsize('config.yaml') / 1024  # Size in KB
        st.metric("Config File Size", f"{config_size:.2f} KB")
        
        # Reset tokens count
        if config:
            reset_tokens = len(config.get('reset_tokens', {}))
            st.metric("Active Reset Tokens", reset_tokens)
    except Exception as e:
        st.warning(f"Could not get system statistics: {e}")

# Footer
st.markdown("---")
st.markdown("© 2025 Squeeze Ai Admin Dashboard - Logged in as: " + st.session_state.get('admin_username', 'Unknown'))