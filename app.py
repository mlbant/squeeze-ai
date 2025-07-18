import streamlit as st
from backend import get_squeeze_stocks, get_single_squeeze_score, get_historical_data
import stripe
import altair as alt
import pandas as pd
import random
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import csv
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import dotenv
import hashlib
import time
import bcrypt
dotenv.load_dotenv()

# Stripe key (test mode)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Page config
st.set_page_config(
    page_title="Squeeze AI - Stock Squeeze Analysis", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load config for auth
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("config.yaml missing! Create it as per instructions.")
    st.stop()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Enhanced dark mode styling
st.markdown("""
<style>
    .main { 
        background-color: #0e1117; 
        color: #fafafa; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stButton > button { 
        background-color: #00D564; 
        color: #0e1117; 
        border: none; 
        border-radius: 8px; 
        padding: 0.5rem 1.5rem; 
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #00E56F;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 213, 100, 0.3);
    }
    .stSelectbox > div, .stTextInput > div > div > input { 
        background-color: #1f2937; 
        color: #fafafa;
        border-radius: 8px; 
        border: 1px solid #374151;
    }
    small { 
        color: #9ca3af; 
        font-size: 0.875rem; 
    }
    h1, h2, h3 { 
        color: #00D564; 
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: transparent;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f2937;
        color: #00D564;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 1rem;
    }
    .disclaimer-box {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
    }
    .stock-card {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .stock-card:hover {
        border-color: #00D564;
        box-shadow: 0 4px 12px rgba(0, 213, 100, 0.1);
    }
    .login-button {
        width: 200px !important;
        margin: 0 auto !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to get browser fingerprint
def get_browser_fingerprint():
    """Create a browser fingerprint using JavaScript"""
    fingerprint_js = """
    <script>
    function getBrowserFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Browser fingerprint', 2, 2);
        
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset(),
            canvas.toDataURL()
        ].join('|');
        
        const hash = fingerprint.split('').reduce((a,b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        return Math.abs(hash).toString();
    }
    
    const fingerprint = getBrowserFingerprint();
    window.parent.postMessage({type: 'fingerprint', value: fingerprint}, '*');
    </script>
    """
    return fingerprint_js

# Function to check guest usage limits
def check_guest_limits():
    """Check if guest has exceeded usage limits using browser fingerprinting"""
    # Create a simple fingerprint based on user agent and screen info
    # This is a basic implementation - in production you'd want more sophisticated fingerprinting
    import hashlib
    
    # Get basic browser info (this is a simplified approach)
    # In a real implementation, you'd use JavaScript to get more detailed fingerprinting
    user_agent = st.context.headers.get("user-agent", "unknown")
    
    # Create a hash of the user agent as a simple fingerprint
    fingerprint = hashlib.md5(user_agent.encode()).hexdigest()[:16]
    
    # Check if usage files exist for this fingerprint
    scan_file = f"guest_scan_{fingerprint}.txt"
    search_file = f"guest_search_{fingerprint}.txt"
    
    scan_used = os.path.exists(scan_file)
    search_used = os.path.exists(search_file)
    
    return scan_used, search_used, fingerprint

# Function to mark guest usage
def mark_guest_usage(fingerprint, usage_type):
    """Mark that guest has used a feature"""
    if usage_type == "scan":
        with open(f"guest_scan_{fingerprint}.txt", "w") as f:
            f.write(str(time.time()))
    elif usage_type == "search":
        with open(f"guest_search_{fingerprint}.txt", "w") as f:
            f.write(str(time.time()))

# Initialize session state and check guest limits
if "guest_scan_used" not in st.session_state:
    st.session_state.guest_scan_used = False
if "guest_search_used" not in st.session_state:
    st.session_state.guest_search_used = False
if "free_scan_used" not in st.session_state:
    st.session_state.free_scan_used = False
if "free_search_used" not in st.session_state:
    st.session_state.free_search_used = False

# Check guest usage limits on page load
try:
    scan_used, search_used, fingerprint = check_guest_limits()
    if scan_used:
        st.session_state.guest_scan_used = True
    if search_used:
        st.session_state.guest_search_used = True
    st.session_state.browser_fingerprint = fingerprint
except:
    # Fallback if fingerprinting fails
    st.session_state.browser_fingerprint = "fallback"

# Show login/sign up if not logged in
if "authentication_status" not in st.session_state or not st.session_state.authentication_status:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🚀 Squeeze AI")
        st.markdown("### AI-Powered Short Squeeze Analysis")
        st.markdown("Identify high-potential squeeze opportunities with advanced metrics")
        
    tab_login, tab_signup, tab_guest = st.tabs(["Login", "Sign Up", "Try as Guest"])

    with tab_login:
        st.subheader("Login to Your Account")
        
        # Custom login form
        login_identifier = st.text_input("Username or Email", placeholder="Enter your username or email")
        login_password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", type="primary"):
            if login_identifier and login_password:
                # Find user by username or email
                found_username = None
                
                # Check if it's a direct username match
                if login_identifier in config['credentials']['usernames']:
                    found_username = login_identifier
                else:
                    # Search by email
                    for username, user_data in config['credentials']['usernames'].items():
                        if user_data.get('email', '').lower() == login_identifier.lower():
                            found_username = username
                            break
                
                if found_username:
                    # Verify password
                    stored_password = config['credentials']['usernames'][found_username]['password']
                    
                    if bcrypt.checkpw(login_password.encode('utf-8'), stored_password.encode('utf-8')):
                        # Successful login
                        st.session_state.authentication_status = True
                        st.session_state.name = config['credentials']['usernames'][found_username]['name']
                        st.session_state.username = found_username
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("Username or email not found")
            else:
                st.error("Please enter both username/email and password")

        if st.button("Forgot Password?"):
            forgot_username = st.text_input("Enter your username")
            if forgot_username:
                try:
                    random_password = authenticator.forgot_password(forgot_username)
                    if random_password:
                        # Email configuration
                        sender_email = "acusumano618@gmail.com"  # Replace
                        sender_password = "rrou qocy zmff naie"   # Replace
                        
                        msg = MIMEText(f"Your temporary password is: {random_password}\n\nPlease log in and change it immediately.")
                        msg['Subject'] = "Squeeze AI Password Reset"
                        msg['From'] = sender_email
                        msg['To'] = config['credentials']['usernames'][forgot_username]['email']

                        try:
                            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                                server.login(sender_email, sender_password)
                                server.sendmail(sender_email, msg['To'], msg.as_string())
                            st.success("Temporary password sent to your email!")
                        except Exception as e:
                            st.error(f"Email failed. Temporary password: {random_password}")
                    else:
                        st.error("Username not found")
                except:
                    st.error("Username not found")

    with tab_signup:
        st.subheader("Create Your Account")
        
        # Custom registration form
        col1, col2 = st.columns(2)
        with col1:
            reg_first_name = st.text_input("First Name", placeholder="Enter your first name")
            reg_email = st.text_input("Email", placeholder="Enter your email address")
            reg_password = st.text_input("Password", type="password", placeholder="Create a password")
        with col2:
            reg_last_name = st.text_input("Last Name", placeholder="Enter your last name")
            reg_username = st.text_input("Username", placeholder="Choose a username")
            reg_confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        if st.button("Create Account", type="primary", use_container_width=True):
            if all([reg_first_name, reg_last_name, reg_email, reg_username, reg_password, reg_confirm_password]):
                if reg_password == reg_confirm_password:
                    # Check if username or email already exists
                    username_exists = reg_username in config['credentials']['usernames']
                    email_exists = any(
                        user_data.get('email', '').lower() == reg_email.lower() 
                        for user_data in config['credentials']['usernames'].values()
                    )
                    
                    if username_exists:
                        st.error("Username already exists. Please choose a different username.")
                    elif email_exists:
                        st.error("Email already registered. Please use a different email or log in.")
                    else:
                        try:
                            # Hash the password
                            hashed_password = stauth.Hasher([reg_password]).generate()[0]
                            
                            # Add new user to config
                            config['credentials']['usernames'][reg_username] = {
                                'email': reg_email,
                                'name': f"{reg_first_name} {reg_last_name}",
                                'password': hashed_password
                            }
                            
                            # Save config
                            with open('config.yaml', 'w') as file:
                                yaml.dump(config, file, default_flow_style=False)
                            
                            # Automatically log in the user
                            st.session_state.authentication_status = True
                            st.session_state.name = f"{reg_first_name} {reg_last_name}"
                            st.session_state.username = reg_username
                            
                            st.success("✅ Account created successfully! Welcome to Squeeze AI!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Registration failed: {str(e)}")
                else:
                    st.error("Passwords don't match. Please try again.")
            else:
                st.error("Please fill in all fields.")

    with tab_guest:
        st.subheader("🎯 Limited Guest Access")
        st.info("Try our features with limited access. Sign up for full functionality!")
        
        guest_col1, guest_col2 = st.columns(2)
        
        with guest_col1:
            st.markdown("### Top Squeeze Preview")
            if not st.session_state.guest_scan_used:
                if st.button("Get Free Preview", key="guest_scan"):
                    with st.spinner("Analyzing market data..."):
                        stocks = get_squeeze_stocks()
                        st.session_state.guest_scan_used = True
                        # Mark usage persistently
                        mark_guest_usage(st.session_state.browser_fingerprint, "scan")
                        
                        if stocks and len(stocks) > 0:
                            stock = stocks[0]
                            st.markdown(f"""
                            <div class='stock-card'>
                                <h4>{stock['ticker']} - Score: {stock['score']}/100</h4>
                                <p>Short %: {stock['short_percent']}% | Borrow Fee: {stock['borrow_fee']}%</p>
                                <p>{stock['why']}</p>
                                <small>Sign up to see all 5 stocks + filters!</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.warning("Guest preview used. Sign up for unlimited access!")

        with guest_col2:
            st.markdown("### Single Stock Analysis")
            if not st.session_state.guest_search_used:
                ticker = st.text_input("Enter ticker (e.g., TSLA)", key="guest_ticker")
                if st.button("Analyze Free", key="guest_analyze"):
                    if ticker:
                        with st.spinner(f"Analyzing {ticker.upper()}..."):
                            score_data = get_single_squeeze_score(ticker.upper())
                            st.session_state.guest_search_used = True
                            # Mark usage persistently
                            mark_guest_usage(st.session_state.browser_fingerprint, "search")
                            
                            st.markdown(f"""
                            <div class='stock-card'>
                                <h4>{score_data['ticker']} - Score: {score_data['score']}/100</h4>
                                <p>{score_data['why']}</p>
                                <small>Sign up for charts + unlimited searches!</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.warning("Guest search used. Sign up for unlimited access!")

else:
    # Logged in - show main app
    authenticator.logout('Logout', 'sidebar')
    
    # Header
    st.title("Squeeze AI 🚀")
    st.markdown("### AI-Powered Squeeze Detection Dashboard")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Top Squeezes", "🔍 Stock Analysis", "📈 Dashboard", "⚙️ Settings"])

    with tab1:
        st.subheader("Real-Time Squeeze Scanner")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sector = st.selectbox("Sector Filter", ["All", "Tech", "Biotech", "Retail", "Energy", "Finance"])
        with col2:
            market_cap = st.selectbox("Market Cap", ["All", "Small (<$1B)", "Mid ($1B-$10B)", "Large (>$10B)"])
        with col3:
            volatility = st.checkbox("High Volatility Only")

        filters = []
        if sector != "All":
            filters.append(f"Sector: {sector}")
        if market_cap != "All":
            filters.append(f"Market Cap: {market_cap}")
        if volatility:
            filters.append("High Volatility")
        filters_str = ", ".join(filters) if filters else None

        if st.button("🚀 Scan Market", type="primary"):
            # Check if user is subscribed or if they've used their free scan
            if "subscribed" not in st.session_state:
                st.session_state.subscribed = False
            
            if not st.session_state.subscribed and st.session_state.free_scan_used:
                # Free user has already used their scan
                st.warning("🔒 Free scan limit reached!")
                st.markdown("""
                <div class='stock-card'>
                    <h3>Upgrade to Pro for Unlimited Access</h3>
                    <p>You've used your free market scan. Upgrade to Pro to get:</p>
                    <ul>
                        <li>✅ Unlimited market scans</li>
                        <li>✅ All 5 daily squeeze picks</li>
                        <li>✅ Advanced filtering options</li>
                        <li>✅ Historical performance data</li>
                        <li>✅ Priority support</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔓 Upgrade to Pro - $29/month", type="primary", key="scan_upgrade"):
                    try:
                        session = stripe.checkout.Session.create(
                            payment_method_types=['card'],
                            line_items=[{
                                'price_data': {
                                    'currency': 'usd',
                                    'product_data': {
                                        'name': 'Squeeze AI Pro',
                                        'description': 'Full access to all squeeze alerts and analysis'
                                    },
                                    'unit_amount': 2900,
                                    'recurring': {
                                        'interval': 'month'
                                    }
                                },
                                'quantity': 1
                            }],
                            mode='subscription',
                            success_url="http://localhost:8501?subscribed=true",
                            cancel_url="http://localhost:8501"
                        )
                        st.markdown(f"[Complete Payment]({session.url})")
                    except Exception as e:
                        st.error(f"Payment setup error: {str(e)}")
                        st.session_state.subscribed = True  # Demo mode
            else:
                with st.spinner("Analyzing thousands of stocks..."):
                    stocks = get_squeeze_stocks(filters_str)
                
                # Mark free scan as used for non-subscribers
                if not st.session_state.subscribed:
                    st.session_state.free_scan_used = True

                if st.session_state.subscribed:
                    st.success(f"Found {len(stocks)} high-potential squeeze candidates!")
                    
                    # Display all stocks with improved layout
                    for i, stock in enumerate(stocks):
                        # Create a container for each stock
                        with st.container():
                            # Header with stock info and circular score
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"### #{i+1} {stock['ticker']}")
                                st.caption("Squeeze Score")
                            with col2:
                                # Create circular progress indicator for score
                                score_percentage = stock['score']
                                circumference = 2 * 3.14159 * 45  # radius = 45
                                stroke_dasharray = circumference
                                stroke_dashoffset = circumference - (score_percentage / 100) * circumference
                                
                                # Determine color based on score
                                if score_percentage >= 80:
                                    color = "#10b981"  # Green
                                elif score_percentage >= 60:
                                    color = "#f59e0b"  # Yellow
                                else:
                                    color = "#ef4444"  # Red
                                
                                st.markdown(f"""
                                <div style="display: flex; justify-content: center; align-items: center;">
                                    <div style="position: relative; width: 120px; height: 120px;">
                                        <svg width="120" height="120" style="transform: rotate(-90deg);">
                                            <!-- Background circle -->
                                            <circle cx="60" cy="60" r="45" 
                                                    fill="none" 
                                                    stroke="#374151" 
                                                    stroke-width="8"/>
                                            <!-- Progress circle -->
                                            <circle cx="60" cy="60" r="45" 
                                                    fill="none" 
                                                    stroke="{color}" 
                                                    stroke-width="8" 
                                                    stroke-linecap="round"
                                                    stroke-dasharray="{stroke_dasharray}" 
                                                    stroke-dashoffset="{stroke_dashoffset}"
                                                    style="transition: stroke-dashoffset 0.5s ease-in-out;"/>
                                        </svg>
                                        <!-- Score text in center -->
                                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                                            <div style="font-size: 24px; font-weight: bold; color: {color};">{stock['score']}</div>
                                            <div style="font-size: 12px; color: #9ca3af;">/100</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Metrics in columns
                            metric_col1, metric_col2, metric_col3 = st.columns(3)
                            with metric_col1:
                                st.metric("Short Interest", f"{stock['short_percent']}%")
                            with metric_col2:
                                st.metric("Borrow Fee", f"{stock['borrow_fee']}%")
                            with metric_col3:
                                st.metric("Days to Cover", stock['days_to_cover'])
                            
                            # Catalyst information
                            st.info(f"**Catalyst:** {stock['why']}")
                            
                            st.divider()
                    
                    # Improved Summary chart
                    st.subheader("📊 Squeeze Score Comparison")
                    df = pd.DataFrame(stocks)
                    
                    # Create a more refined bar chart
                    chart = alt.Chart(df).mark_bar(
                        cornerRadiusTopLeft=6,
                        cornerRadiusTopRight=6,
                        strokeWidth=1,
                        stroke='#374151'
                    ).encode(
                        x=alt.X('ticker:N', 
                               sort=alt.EncodingSortField(field='score', order='descending'),
                               title='Stock Ticker',
                               axis=alt.Axis(
                                   labelAngle=0,
                                   labelFontSize=12,
                                   labelColor='#9ca3af',
                                   titleColor='#9ca3af',
                                   titleFontSize=14
                               )),
                        y=alt.Y('score:Q', 
                               title='Squeeze Score',
                               scale=alt.Scale(domain=[0, 100]),
                               axis=alt.Axis(
                                   labelFontSize=12,
                                   labelColor='#9ca3af',
                                   titleColor='#9ca3af',
                                   titleFontSize=14,
                                   grid=True,
                                   gridColor='#374151',
                                   gridOpacity=0.3
                               )),
                        color=alt.Color('score:Q', 
                                       scale=alt.Scale(
                                           range=['#065f46', '#047857', '#059669', '#10b981', '#34d399', '#6ee7b7']
                                       ),
                                       legend=None),
                        tooltip=[
                            alt.Tooltip('ticker:N', title='Stock'),
                            alt.Tooltip('score:Q', title='Squeeze Score'),
                            alt.Tooltip('short_percent:Q', title='Short Interest %'),
                            alt.Tooltip('borrow_fee:Q', title='Borrow Fee %'),
                            alt.Tooltip('days_to_cover:Q', title='Days to Cover')
                        ]
                    ).properties(
                        height=350,
                        title=alt.TitleParams(
                            text='Top Squeeze Candidates by Score',
                            fontSize=16,
                            color='#00D564',
                            anchor='start'
                        )
                    ).configure_view(
                        strokeWidth=0,
                        fill='#0e1117'
                    ).configure_axis(
                        domainColor='#374151',
                        tickColor='#374151'
                    ).configure_title(
                        fontSize=16,
                        color='#00D564'
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
                    
                else:
                    # Free preview
                    st.info("🎯 Free Preview: Showing top squeeze candidate only")
                    if stocks and len(stocks) > 0:
                        stock = stocks[0]
                        st.markdown(f"""
                        <div class='stock-card'>
                            <h3>{stock['ticker']} - Squeeze Score: {stock['score']}/100</h3>
                            <p><strong>Why:</strong> {stock['why']}</p>
                            <p style='color: #00D564; margin-top: 1rem;'>
                                ⚡ Unlock all 5 stocks + real-time alerts with Pro!
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🔓 Unlock Pro Access - $29/month", type="primary"):
                            # Create Stripe session
                            try:
                                session = stripe.checkout.Session.create(
                                    payment_method_types=['card'],
                                    line_items=[{
                                        'price_data': {
                                            'currency': 'usd',
                                            'product_data': {
                                                'name': 'Squeeze AI Pro',
                                                'description': 'Full access to all squeeze alerts and analysis'
                                            },
                                            'unit_amount': 2900,
                                            'recurring': {
                                                'interval': 'month'
                                            }
                                        },
                                        'quantity': 1
                                    }],
                                    mode='subscription',
                                    success_url="http://localhost:8501?subscribed=true",
                                    cancel_url="http://localhost:8501"
                                )
                                st.markdown(f"[Complete Payment]({session.url})")
                            except Exception as e:
                                st.error(f"Payment setup error: {str(e)}")
                                st.session_state.subscribed = True  # Demo mode

                # Save to history
                history_file = f"{st.session_state.username}_history.csv"
                with open(history_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.now(), "scan", filters_str, len(stocks)])

    with tab2:
        st.subheader("Deep Stock Analysis")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker = st.text_input("Enter Stock Ticker", placeholder="TSLA, GME, AMC...")
        with col2:
            period = st.radio("Chart Period", ["1mo", "3mo", "6mo"], horizontal=True)
        
        if st.button("Analyze Stock", type="primary"):
            if ticker:
                # Check if user is subscribed or if they've used their free search
                if "subscribed" not in st.session_state:
                    st.session_state.subscribed = False
                
                if not st.session_state.subscribed and st.session_state.free_search_used:
                    # Free user has already used their search
                    st.warning("🔒 Free analysis limit reached!")
                    st.markdown("""
                    <div class='stock-card'>
                        <h3>Upgrade to Pro for Unlimited Access</h3>
                        <p>You've used your free stock analysis. Upgrade to Pro to get:</p>
                        <ul>
                            <li>✅ Unlimited stock analysis</li>
                            <li>✅ Full price charts and historical data</li>
                            <li>✅ Score breakdown visualizations</li>
                            <li>✅ All 5 daily squeeze picks</li>
                            <li>✅ Priority support</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔓 Upgrade to Pro - $29/month", type="primary", key="search_upgrade"):
                        try:
                            session = stripe.checkout.Session.create(
                                payment_method_types=['card'],
                                line_items=[{
                                    'price_data': {
                                        'currency': 'usd',
                                        'product_data': {
                                            'name': 'Squeeze AI Pro',
                                            'description': 'Full access to all squeeze alerts and analysis'
                                        },
                                        'unit_amount': 2900,
                                        'recurring': {
                                            'interval': 'month'
                                        }
                                    },
                                    'quantity': 1
                                }],
                                mode='subscription',
                                success_url="http://localhost:8501?subscribed=true",
                                cancel_url="http://localhost:8501"
                            )
                            st.markdown(f"[Complete Payment]({session.url})")
                        except Exception as e:
                            st.error(f"Payment setup error: {str(e)}")
                            st.session_state.subscribed = True  # Demo mode
                else:
                    with st.spinner(f"Analyzing {ticker.upper()}..."):
                        # Mark free search as used for non-subscribers
                        if not st.session_state.subscribed:
                            st.session_state.free_search_used = True
                        
                        # Get squeeze score
                        score_data = get_single_squeeze_score(ticker.upper())
                        
                        # Get historical data
                        hist_data = get_historical_data(ticker.upper(), period)
                        
                        if score_data['score'] != "ERROR":
                            # Display metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Squeeze Score", f"{score_data['score']}/100")
                            with col2:
                                st.metric("Short Interest", f"{score_data['short_percent']}%")
                            with col3:
                                st.metric("Borrow Fee", f"{score_data['borrow_fee']}%")
                            with col4:
                                st.metric("Days to Cover", f"{score_data['days_to_cover']}")
                            
                            st.markdown(f"""
                            <div class='stock-card'>
                                <h3>Analysis Summary</h3>
                                <p>{score_data['why']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Price chart
                            if not hist_data.empty:
                                st.subheader(f"{ticker.upper()} Price History")
                                
                                # Calculate price change
                                price_change = ((hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[0]) / hist_data['Close'].iloc[0]) * 100
                                
                                price_chart = alt.Chart(hist_data).mark_area(
                                    line={'color': '#00D564', 'strokeWidth': 2},
                                    color=alt.Gradient(
                                        gradient='linear',
                                        stops=[
                                            alt.GradientStop(color='#00D564', offset=0),
                                            alt.GradientStop(color='#001F0F', offset=1)
                                        ],
                                        x1=1, x2=1, y1=1, y2=0
                                    )
                                ).encode(
                                    x=alt.X('Date:T', title='Date'),
                                    y=alt.Y('Close:Q', title='Price ($)'),
                                    tooltip=[
                                        alt.Tooltip('Date:T', format='%Y-%m-%d'),
                                        alt.Tooltip('Close:Q', format='$.2f', title='Price'),
                                        alt.Tooltip('Volume:Q', format=',d')
                                    ]
                                ).properties(
                                    height=400,
                                    title={
                                        'text': f'{ticker.upper()} - {period} Price Movement ({price_change:+.2f}%)',
                                        'color': '#00D564' if price_change > 0 else '#FF4444'
                                    }
                                ).configure_view(
                                    strokeWidth=0
                                ).configure_axis(
                                    grid=False,
                                    labelColor='#9ca3af',
                                    titleColor='#9ca3af'
                                )
                                
                                st.altair_chart(price_chart, use_container_width=True)
                                
                                # Volume chart
                                volume_chart = alt.Chart(hist_data).mark_bar(
                                    color='#00D564',
                                    opacity=0.3
                                ).encode(
                                    x=alt.X('Date:T', title=''),
                                    y=alt.Y('Volume:Q', title='Volume'),
                                    tooltip=[
                                        alt.Tooltip('Date:T', format='%Y-%m-%d'),
                                        alt.Tooltip('Volume:Q', format=',d')
                                    ]
                                ).properties(
                                    height=150
                                ).configure_view(
                                    strokeWidth=0
                                ).configure_axis(
                                    grid=False,
                                    labelColor='#9ca3af',
                                    titleColor='#9ca3af'
                                )
                                
                                st.altair_chart(volume_chart, use_container_width=True)
                            
                            # Score breakdown visualization
                            st.subheader("Score Breakdown")
                            breakdown_data = pd.DataFrame([
                                {'Factor': 'Short Interest', 'Weight': 30, 'Score': min(30, score_data['short_percent'])},
                                {'Factor': 'Borrow Fee', 'Weight': 20, 'Score': min(20, score_data['borrow_fee'])},
                                {'Factor': 'Days to Cover', 'Weight': 20, 'Score': min(20, score_data['days_to_cover'] * 2)},
                                {'Factor': 'Momentum', 'Weight': 30, 'Score': score_data['score'] - min(70, score_data['short_percent'] + score_data['borrow_fee'] + score_data['days_to_cover'] * 2)}
                            ])
                            
                            breakdown_chart = alt.Chart(breakdown_data).mark_bar().encode(
                                x=alt.X('Score:Q', scale=alt.Scale(domain=[0, 30]), title='Contribution to Score'),
                                y=alt.Y('Factor:N', sort='-x'),
                                color=alt.Color('Factor:N', scale=alt.Scale(scheme='greens'), legend=None),
                                tooltip=['Factor', 'Score', 'Weight']
                            ).properties(
                                height=200
                            ).configure_view(
                                strokeWidth=0
                            ).configure_axis(
                                grid=False
                            )
                            
                            st.altair_chart(breakdown_chart, use_container_width=True)
                        else:
                            st.error("Error analyzing stock. Please try again.")
                        
                        # Save to history
                        history_file = f"{st.session_state.username}_history.csv"
                        with open(history_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([datetime.now(), "search", ticker, score_data.get('score', 'ERROR')])
            else:
                st.warning("Please enter a ticker symbol")

    with tab3:
        st.subheader("Analytics Dashboard")
        
        # Get actual user activity data
        history_file = f"{st.session_state.username}_history.csv"
        history_data = []
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        try:
                            history_data.append({
                                'Time': pd.to_datetime(row[0]),
                                'Type': row[1],
                                'Query': row[2] if row[2] != 'None' else '',
                                'Result': int(row[3]) if row[3].isdigit() else row[3]
                            })
                        except:
                            continue
        
        # Calculate real metrics from user data
        total_scans = len([h for h in history_data if h['Type'] == 'scan'])
        total_searches = len([h for h in history_data if h['Type'] == 'search'])
        total_activities = len(history_data)
        
        # Calculate average score from searches
        search_scores = [h['Result'] for h in history_data if h['Type'] == 'search' and isinstance(h['Result'], int)]
        avg_score = int(sum(search_scores) / len(search_scores)) if search_scores else 0
        
        # Summary metrics with real data
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Market Scans", total_scans, help="Number of market scans performed")
        with col2:
            st.metric("Stock Searches", total_searches, help="Individual stocks analyzed")
        
        # Activity over time chart
        if history_data:
            st.subheader("📈 Your Activity Trends")
            
            # Group activity by date
            activity_by_date = {}
            for h in history_data:
                date = h['Time'].date()
                if date not in activity_by_date:
                    activity_by_date[date] = {'scans': 0, 'searches': 0}
                
                # Map activity types correctly
                if h['Type'] == 'scan':
                    activity_by_date[date]['scans'] += 1
                elif h['Type'] == 'search':
                    activity_by_date[date]['searches'] += 1
            
            # Create DataFrame for chart
            chart_data = []
            for date, counts in activity_by_date.items():
                chart_data.append({
                    'Date': date,
                    'Market Scans': counts['scans'],
                    'Stock Searches': counts['searches']
                })
            
            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                chart_df = chart_df.melt('Date', var_name='Activity Type', value_name='Count')
                
                activity_chart = alt.Chart(chart_df).mark_bar().encode(
                    x=alt.X('Date:T', title='Date'),
                    y=alt.Y('Count:Q', title='Number of Activities'),
                    color=alt.Color('Activity Type:N', 
                                   scale=alt.Scale(range=['#00D564', '#10b981']),
                                   legend=alt.Legend(title="Activity Type")),
                    tooltip=['Date:T', 'Activity Type:N', 'Count:Q']
                ).properties(
                    height=300,
                    title='Daily Activity Overview'
                ).configure_view(
                    strokeWidth=0
                ).configure_axis(
                    grid=False,
                    labelColor='#9ca3af',
                    titleColor='#9ca3af'
                ).configure_title(
                    fontSize=16,
                    color='#00D564'
                )
                
                st.altair_chart(activity_chart, use_container_width=True)
        
        # Recent Activity with better formatting
        st.subheader("🕒 Recent Activity")
        
        if history_data:
            # Show last 10 activities with better formatting
            recent_activities = sorted(history_data, key=lambda x: x['Time'], reverse=True)[:10]
            
            for i, activity in enumerate(recent_activities):
                time_str = activity['Time'].strftime("%m/%d/%Y %I:%M %p")
                
                if activity['Type'] == 'scan':
                    if activity['Query']:
                        action_text = f"Market scan with filters: {activity['Query']}"
                    else:
                        action_text = "Market scan (no filters)"
                    result_text = f"Found {activity['Result']} stocks"
                    icon = "🔍"
                else:  # search
                    action_text = f"Analyzed stock: {activity['Query'].upper()}"
                    result_text = f"Score: {activity['Result']}/100"
                    icon = "📊"
                
                st.markdown(f"""
                <div class='stock-card' style='padding: 1rem; margin-bottom: 0.5rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='display: flex; align-items: center; gap: 0.5rem;'>
                            <span style='font-size: 1.2rem;'>{icon}</span>
                            <div>
                                <div style='font-weight: 600; color: #fafafa;'>{action_text}</div>
                                <div style='font-size: 0.85rem; color: #9ca3af;'>{time_str}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: #00D564; font-weight: 600;'>{result_text}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activity yet. Start by scanning the market or analyzing individual stocks!")
        
        # Top searched stocks
        if history_data:
            searches = [h for h in history_data if h['Type'] == 'search' and h['Query']]
            if searches:
                st.subheader("🔥 Your Most Searched Stocks")
                
                # Count searches by stock
                stock_counts = {}
                stock_scores = {}
                for search in searches:
                    ticker = search['Query'].upper()
                    stock_counts[ticker] = stock_counts.get(ticker, 0) + 1
                    if isinstance(search['Result'], int):
                        stock_scores[ticker] = search['Result']
                
                # Create top stocks display
                top_stocks = sorted(stock_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                
                for ticker, count in top_stocks:
                    score = stock_scores.get(ticker, 'N/A')
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{ticker}**")
                    with col2:
                        st.write(f"{count} searches")
                    with col3:
                        if score != 'N/A':
                            st.write(f"Score: {score}/100")
                        else:
                            st.write("Score: N/A")
        

    with tab4:
        st.subheader("Account Settings")
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            st.markdown("### Profile Information")
            st.markdown("")
            
            current_email = config['credentials']['usernames'][st.session_state.username].get('email', '')
            new_email = st.text_input("Email Address", value=current_email)
            
            st.markdown("")
            st.markdown("### Change Password")
            st.markdown("")
            
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            st.markdown("")
            if st.button("Update Profile", type="primary"):
                updates_made = False
                
                # Update email
                if new_email != current_email:
                    config['credentials']['usernames'][st.session_state.username]['email'] = new_email
                    updates_made = True
                
                # Update password
                if new_password and confirm_password:
                    if new_password == confirm_password:
                        # Verify current password first
                        try:
                            # Check if current password matches stored password
                            stored_password = config['credentials']['usernames'][st.session_state.username]['password']
                            
                            # Use the authenticator's verify method
                            if bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8')):
                                # Hash the new password
                                new_hashed_password = stauth.Hasher([new_password]).generate()[0]
                                config['credentials']['usernames'][st.session_state.username]['password'] = new_hashed_password
                                updates_made = True
                                st.success("Password updated successfully!")
                            else:
                                st.error("Current password is incorrect")
                        except Exception as e:
                            st.error(f"Error updating password: {str(e)}")
                    else:
                        st.error("New passwords don't match")
                elif new_password or confirm_password:
                    st.error("Please fill in both new password fields")
                
                if updates_made:
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    st.success("Profile updated successfully!")
        
        with col2:
            st.markdown("### Subscription Status")
            st.markdown("")
            
            if st.session_state.get('subscribed', False):
                st.success("✅ Pro Member")
                st.markdown("")
                st.write("Next billing date: " + pd.Timestamp.now().strftime('%B %d, %Y'))
                st.markdown("")
                if st.button("Cancel Subscription", type="secondary"):
                    st.session_state.subscribed = False
                    st.info("Subscription cancelled")
            else:
                st.warning("⚠️ Free Account")
                st.markdown("")
                st.markdown("**Upgrade to Pro for:**")
                st.markdown("• Unlimited market scans")
                st.markdown("• Unlimited stock analysis")
                st.markdown("• All 5 daily squeeze picks")
                st.markdown("• Historical performance data")
                st.markdown("• Priority support")
                st.markdown("")
                
                if st.button("Upgrade to Pro - $29/month", type="primary"):
                    st.session_state.subscribed = True  # Demo
                    st.success("Welcome to Pro!")

# Footer with disclaimers
st.markdown("""
<div class='disclaimer-box'>
    <h4 style='color: #00D564; margin-bottom: 1rem;'>Important Disclaimers</h4>
    <ul style='color: #9ca3af; margin-left: 1.5rem;'>
        <li>This tool provides analysis for educational purposes only</li>
        <li>Not investment advice - always consult with a qualified financial advisor</li>
        <li>Short squeezes are high-risk, high-volatility events</li>
        <li>Past performance does not predict future results</li>
        <li>Scores are algorithmic estimates based on multiple factors</li>
        <li>Always do your own research and verify data independently before making investment decisions</li>
    </ul>
    <p style='color: #6b7280; margin-top: 1rem; font-size: 0.875rem;'>
        Squeeze AI uses advanced algorithms to analyze short interest data, borrow rates, and market momentum. 
        Our scores are for educational and informational purposes only.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 2rem 0;'>
    <small>© 2024 Squeeze AI | <a href='#' style='color: #00D564;'>Terms</a> | <a href='#' style='color: #00D564;'>Privacy</a> | <a href='#' style='color: #00D564;'>Contact</a></small>
</div>
""", unsafe_allow_html=True)
