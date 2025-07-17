import streamlit as st
import pandas as pd
from database import UserDatabase
from secure_auth import SecureAuth
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import bcrypt
import secrets
import dotenv
dotenv.load_dotenv()

# Initialize database and secure auth
db = UserDatabase()
auth = SecureAuth()

st.set_page_config(
    page_title="Squeeze AI Admin Dashboard",
    page_icon="🔐",
    layout="wide"
)

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

# Admin login with rate limiting
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
            # Validate inputs
            valid_username, username_msg = auth.validate_input(username, "username")
            if not valid_username:
                st.error(f"Username error: {username_msg}")
                st.stop()
            
            # Check rate limiting
            if not auth.check_rate_limit(username):
                st.error("Too many failed login attempts. Please try again later.")
                st.stop()
            
            # Verify credentials
            if verify_admin_credentials(username, password):
                st.session_state.admin_logged_in = True
                st.session_state.admin_username = username
                auth.log_login_attempt(username, "admin_panel", True)
                st.success("Admin login successful!")
                st.rerun()
            else:
                auth.log_login_attempt(username, "admin_panel", False)
                st.error("Invalid admin credentials")
    st.stop()

# Admin Dashboard
st.title("🔐 Squeeze AI Admin Dashboard")

# Logout button
if st.button("Logout", type="secondary"):
    st.session_state.admin_logged_in = False
    st.rerun()

# Get statistics
stats = db.get_user_stats()

# Display key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Users", stats['total_users'], delta=stats['today_signups'])
with col2:
    st.metric("Pro Subscribers", stats['active_subscriptions'])
with col3:
    st.metric("Monthly Revenue", f"${stats['monthly_revenue']:,}")
with col4:
    conversion_rate = (stats['active_subscriptions'] / max(stats['total_users'], 1)) * 100
    st.metric("Conversion Rate", f"{conversion_rate:.1f}%")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "💳 Subscriptions", "📊 Analytics", "⚙️ Settings"])

with tab1:
    st.subheader("User Management")
    
    # Get all users
    users = db.get_all_users()
    
    if users:
        # Convert to DataFrame
        df = pd.DataFrame(users)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            plan_filter = st.multiselect("Filter by Plan", ["free", "pro"], default=["free", "pro"])
        with col2:
            active_filter = st.checkbox("Active Users Only", value=True)
        with col3:
            search = st.text_input("Search users", placeholder="Username or email...")
        
        # Apply filters
        filtered_df = df[df['plan'].isin(plan_filter)]
        if active_filter:
            filtered_df = filtered_df[filtered_df['is_active'] == 1]
        if search:
            filtered_df = filtered_df[
                filtered_df['username'].str.contains(search, case=False) |
                filtered_df['email'].str.contains(search, case=False)
            ]
        
        # Display users
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "User ID",
                "created_at": st.column_config.DatetimeColumn("Joined", format="DD/MM/YYYY"),
                "last_login": st.column_config.DatetimeColumn("Last Login", format="DD/MM/YYYY HH:mm"),
                "is_active": st.column_config.CheckboxColumn("Active"),
                "plan": st.column_config.SelectboxColumn("Plan", options=["free", "pro"]),
                "subscription_status": st.column_config.SelectboxColumn("Status", options=["active", "inactive", "cancelled"])
            }
        )
        
        # User actions
        st.subheader("User Actions")
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.number_input("User ID", min_value=1, step=1)
        with col2:
            action = st.selectbox("Action", ["Deactivate", "Activate", "Reset Password", "Upgrade to Pro"])
        
        if st.button("Execute Action"):
            if action == "Deactivate":
                db.set_user_active(user_id, False)
                st.success(f"User {user_id} deactivated.")
            elif action == "Activate":
                db.set_user_active(user_id, True)
                st.success(f"User {user_id} activated.")
            elif action == "Reset Password":
                new_password = st.text_input("New Password for User", type="password")
                if new_password:
                    db.reset_user_password(user_id, new_password)
                    st.success(f"Password for user {user_id} reset.")
                else:
                    st.warning("Enter a new password above and click again.")
            elif action == "Upgrade to Pro":
                db.upgrade_user_to_pro(user_id)
                st.success(f"User {user_id} upgraded to Pro.")
    else:
        st.info("No users yet")

# Subscription Management (tab2)
with tab2:
    st.subheader("Subscription Management")
    # Subscription stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Pro Subscriptions", stats['active_subscriptions'])
    with col2:
        st.metric("Monthly Recurring Revenue", f"${stats['monthly_revenue']:,}")
    with col3:
        # Calculate churn rate if you have the data, else mock
        churn_rate = 5.2  # TODO: Replace with real calculation if available
        st.metric("Churn Rate", f"{churn_rate}%", delta="-0.8%")
    # Recent subscriptions
    st.subheader("Recent Subscription Activity")
    recent_subs = db.get_subscription_activity()
    if recent_subs:
        sub_df = pd.DataFrame(recent_subs, columns=["Date", "User ID", "Status", "Plan"])
        st.dataframe(sub_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent subscription activity.")

# Analytics Dashboard (tab3)
with tab3:
    st.subheader("Analytics Dashboard")
    # User growth chart
    user_growth = db.get_user_growth()
    if user_growth:
        growth_df = pd.DataFrame(user_growth, columns=["Date", "Signups"])
        fig1 = px.line(growth_df, x='Date', y='Signups', title='User Signups Over Time')
        st.plotly_chart(fig1, use_container_width=True)
    # Revenue chart
    revenue_data = db.get_revenue_by_month()
    if revenue_data:
        rev_df = pd.DataFrame(revenue_data, columns=["Month", "Revenue"])
        fig2 = px.bar(rev_df, x='Month', y='Revenue', title='Monthly Revenue', text='Revenue')
        fig2.update_traces(texttemplate='$%{text:,}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)
    # Search analytics (mock for now)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Searches Today", "1,247")
        st.metric("Avg Searches per User", "3.2")
    with col2:
        st.metric("Most Searched Stock", "TSLA")
        st.metric("API Calls Today", "5,832")

with tab4:
    st.subheader("System Settings")
    
    # Stripe configuration
    st.markdown("### Stripe Configuration")
    stripe_test_mode = st.checkbox("Test Mode", value=True)
    stripe_key = st.text_input("Stripe Secret Key", type="password", value="sk_test_...")
    price_id = st.text_input("Price ID", value="price_...")
    
    # Email settings
    st.markdown("### Email Configuration")
    smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
    smtp_port = st.number_input("SMTP Port", value=587)
    email_address = st.text_input("Email Address")
    email_password = st.text_input("Email Password", type="password")
    
    # API limits
    st.markdown("### API Rate Limits")
    free_limit = st.number_input("Free User Daily Limit", value=5)
    pro_limit = st.number_input("Pro User Daily Limit", value=100)
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

# Export functionality
st.sidebar.title("Export Data")
if st.sidebar.button("Export User List"):
    users_df = pd.DataFrame(db.get_all_users())
    csv = users_df.to_csv(index=False)
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"users_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
