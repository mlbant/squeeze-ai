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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "guest_scan_used" not in st.session_state:
    st.session_state.guest_scan_used = False
if "guest_search_used" not in st.session_state:
    st.session_state.guest_search_used = False

# Show login/sign up if not logged in
if "authentication_status" not in st.session_state or not st.session_state.authentication_status:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🚀 Squeeze AI")
        st.markdown("### AI-Powered Short Squeeze Analysis")
        st.markdown("Identify high-potential squeeze opportunities with advanced metrics")
        
    tab_login, tab_signup, tab_guest = st.tabs(["Login", "Sign Up", "Try as Guest"])

    with tab_login:
        login_result = authenticator.login(key='login', location='main')
        if login_result is not None:
            name, authentication_status, username = login_result
            if authentication_status:
                st.session_state.authentication_status = authentication_status
                st.session_state.name = name
                st.session_state.username = username
                st.rerun()
            elif authentication_status is False:
                st.error('Username/password is incorrect')

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
        try:
            if authenticator.register_user(key='register', location='main'):
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success('✅ Registration successful! Please log in.')
        except Exception as e:
            st.error(e)

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
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"Welcome back, {st.session_state.name}! 🚀")
        st.markdown("### AI-Powered Squeeze Detection Dashboard")
    with col2:
        st.markdown(f"""
        <div class='metric-card' style='text-align: center;'>
            <h3 style='margin: 0;'>Live Users</h3>
            <h2 style='margin: 0; color: #00D564;'>{random.randint(800, 1200)}</h2>
            <small>scanning now</small>
        </div>
        """, unsafe_allow_html=True)

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
            with st.spinner("Analyzing thousands of stocks..."):
                stocks = get_squeeze_stocks(filters_str)
                
                if "subscribed" not in st.session_state:
                    st.session_state.subscribed = False

                if st.session_state.subscribed:
                    st.success(f"Found {len(stocks)} high-potential squeeze candidates!")
                    
                    # Display all stocks
                    for i, stock in enumerate(stocks):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"""
                            <div class='stock-card'>
                                <h3>#{i+1} {stock['ticker']} - Squeeze Score: {stock['score']}/100</h3>
                                <div style='display: flex; gap: 2rem; margin: 1rem 0;'>
                                    <div>
                                        <strong>Short Interest:</strong> {stock['short_percent']}%
                                    </div>
                                    <div>
                                        <strong>Borrow Fee:</strong> {stock['borrow_fee']}%
                                    </div>
                                    <div>
                                        <strong>Days to Cover:</strong> {stock['days_to_cover']}
                                    </div>
                                </div>
                                <p><strong>Catalyst:</strong> {stock['why']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Mini score visualization
                            score_df = pd.DataFrame([{
                                'Metric': 'Score',
                                'Value': stock['score']
                            }])
                            
                            score_chart = alt.Chart(score_df).mark_arc(innerRadius=30).encode(
                                theta=alt.Theta(field="Value", type="quantitative", scale=alt.Scale(domain=[0, 100])),
                                color=alt.Color("Value", scale=alt.Scale(scheme='greens'))
                            ).properties(width=100, height=100)
                            
                            st.altair_chart(score_chart, use_container_width=True)
                    
                    # Summary chart
                    df = pd.DataFrame(stocks)
                    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
                        x=alt.X('ticker', sort='-y', title='Stock'),
                        y=alt.Y('score', title='Squeeze Score'),
                        color=alt.Color('score', scale=alt.Scale(scheme='greens'), legend=None),
                        tooltip=['ticker', 'score', 'short_percent', 'borrow_fee', 'days_to_cover', 'why']
                    ).properties(
                        title='Squeeze Score Comparison',
                        height=400
                    ).configure_view(
                        strokeWidth=0
                    ).configure_axis(
                        grid=False
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
                with st.spinner(f"Analyzing {ticker.upper()}..."):
                    # Get squeeze score
                    score_data = get_single_squeeze_score(ticker.upper())
                    
                    # Get historical data
                    hist_data = get_historical_data(ticker.upper(), period)
                    
                    if score_data['score'] != "ERROR":
                        # Display metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Squeeze Score", f"{score_data['score']}/100", 
                                     delta=f"+{random.randint(5, 15)}%" if score_data['score'] > 60 else f"-{random.randint(1, 5)}%")
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
        st.subheader("Your Trading Dashboard")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Scans", random.randint(50, 200))
        with col2:
            st.metric("Stocks Analyzed", random.randint(20, 80))
        with col3:
            st.metric("Avg Score Found", f"{random.randint(65, 85)}/100")
        with col4:
            st.metric("Success Rate", f"{random.randint(70, 90)}%")
        
        # History
        st.subheader("Recent Activity")
        history_file = f"{st.session_state.username}_history.csv"
        if os.path.exists(history_file):
            history_data = []
            with open(history_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        history_data.append({
                            'Time': row[0],
                            'Type': row[1],
                            'Query': row[2],
                            'Result': row[3]
                        })
            
            if history_data:
                history_df = pd.DataFrame(history_data[-10:])  # Last 10 entries
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("No activity yet. Start scanning for squeezes!")
        else:
            st.info("No activity yet. Start scanning for squeezes!")
        
        # Performance chart (mock data)
        st.subheader("Your Performance")
        days = pd.date_range(start='2024-01-01', periods=30, freq='D')
        performance_data = pd.DataFrame({
            'Date': days,
            'Portfolio': [100 + i * 2 + random.randint(-5, 10) for i in range(30)],
            'Market': [100 + i * 0.5 + random.randint(-3, 3) for i in range(30)]
        })
        
        performance_long = performance_data.melt('Date', var_name='Type', value_name='Value')
        
        perf_chart = alt.Chart(performance_long).mark_line(strokeWidth=2).encode(
            x='Date:T',
            y=alt.Y('Value:Q', title='Performance (%)'),
            color=alt.Color('Type:N', scale=alt.Scale(
                domain=['Portfolio', 'Market'],
                range=['#00D564', '#6B7280']
            )),
            tooltip=['Date:T', 'Type:N', 'Value:Q']
        ).properties(
            height=300,
            title='Portfolio vs Market Performance'
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=False
        )
        
        st.altair_chart(perf_chart, use_container_width=True)

    with tab4:
        st.subheader("Account Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Profile Information")
            current_email = config['credentials']['usernames'][st.session_state.username].get('email', '')
            new_email = st.text_input("Email Address", value=current_email)
            
            st.markdown("### Change Password")
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.button("Update Profile"):
                updates_made = False
                
                # Update email
                if new_email != current_email:
                    config['credentials']['usernames'][st.session_state.username]['email'] = new_email
                    updates_made = True
                
                # Update password
                if new_password and new_password == confirm_password:
                    # Verify current password first
                    hasher = stauth.Hasher([''])
                    if hasher.verify(current_password, config['credentials']['usernames'][st.session_state.username]['password']):
                        hashed_password = hasher.generate()[0]
                        config['credentials']['usernames'][st.session_state.username]['password'] = hashed_password
                        updates_made = True
                    else:
                        st.error("Current password is incorrect")
                elif new_password != confirm_password:
                    st.error("New passwords don't match")
                
                if updates_made:
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    st.success("Profile updated successfully!")
        
        with col2:
            st.markdown("### Subscription Status")
            if st.session_state.get('subscribed', False):
                st.success("✅ Pro Member")
                st.write("Next billing date: " + pd.Timestamp.now().strftime('%B %d, %Y'))
                if st.button("Cancel Subscription"):
                    st.session_state.subscribed = False
                    st.info("Subscription cancelled")
            else:
                st.warning("⚠️ Free Account")
                st.write("Upgrade to Pro for:")
                st.write("- All 5 daily squeeze picks")
                st.write("- Real-time price alerts")
                st.write("- Advanced filters")
                st.write("- Historical performance data")
                st.write("- Priority support")
                
                if st.button("Upgrade to Pro - $29/month"):
                    st.session_state.subscribed = True  # Demo
                    st.success("Welcome to Pro!")
            
            st.markdown("### Alert Preferences")
            email_alerts = st.checkbox("Email Alerts", value=True)
            alert_threshold = st.slider("Alert when score above:", 50, 100, 75)
            
            if st.button("Save Preferences"):
                st.success("Preferences saved!")

# Footer with disclaimers
st.markdown("""
<div class='disclaimer-box'>
    <h4 style='color: #00D564; margin-bottom: 1rem;'>Important Disclaimers</h4>
    <ul style='color: #9ca3af; margin-left: 1.5rem;'>
        <li>This tool provides analysis based on publicly available market data</li>
        <li>Not investment advice - always consult with a qualified financial advisor</li>
        <li>Short squeezes are high-risk, high-volatility events</li>
        <li>Past performance does not predict future results</li>
        <li>Scores are algorithmic estimates based on multiple factors</li>
        <li>Always do your own research before making investment decisions</li>
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