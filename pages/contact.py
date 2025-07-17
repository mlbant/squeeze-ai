import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import dotenv
dotenv.load_dotenv()

st.set_page_config(
    page_title="Contact Us - Squeeze AI",
    page_icon="📧",
    layout="wide"
)

# Enhanced dark mode styling
st.markdown("""
<style>
    .main { 
        background-color: #0e1117; 
        color: #fafafa; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    h1, h2, h3 { 
        color: #00D564; 
        font-weight: 700;
    }
    .contact-section {
        background-color: #1f2937;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 2rem;
    }
    .back-button {
        background-color: #00D564;
        color: #0e1117;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 2rem;
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
    .stSelectbox > div, .stTextInput > div > div > input, .stTextArea > div > div > textarea { 
        background-color: #1f2937; 
        color: #fafafa;
        border-radius: 8px; 
        border: 1px solid #374151;
    }
</style>
""", unsafe_allow_html=True)

st.title("📧 Contact Us")
st.markdown("We'd love to hear from you! Get in touch with our team.")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="contact-section">
    <h2>Send us a Message</h2>
    <p>Have questions, feedback, or need support? Fill out the form below and we'll get back to you within 24 hours.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("contact_form"):
        # Contact form fields
        col_name, col_email = st.columns(2)
        with col_name:
            name = st.text_input("Full Name *", placeholder="John Doe")
        with col_email:
            email = st.text_input("Email Address *", placeholder="john@example.com")
        
        subject_options = [
            "General Inquiry",
            "Technical Support",
            "Billing Question",
            "Feature Request",
            "Bug Report",
            "Partnership Inquiry",
            "Press/Media",
            "Other"
        ]
        subject = st.selectbox("Subject *", subject_options)
        
        message = st.text_area("Message *", 
                              placeholder="Please describe your question or issue in detail...",
                              height=150)
        
        # Priority level
        priority = st.radio("Priority Level", ["Low", "Medium", "High"], horizontal=True)
        
        # Submit button
        submitted = st.form_submit_button("Send Message", type="primary")
        
        if submitted:
            # Validate form
            if not name or not email or not message:
                st.error("Please fill in all required fields marked with *")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address")
            else:
                # Process the form (in a real app, you'd send this to your support system)
                try:
                    # Here you would typically send the email or save to database
                    # For demo purposes, we'll just show a success message
                    st.success("✅ Message sent successfully! We'll get back to you within 24 hours.")
                    
                    # You could also save to a local file for demo purposes
                    with open("contact_messages.txt", "a") as f:
                        f.write(f"\n--- New Message ({datetime.now()}) ---\n")
                        f.write(f"Name: {name}\n")
                        f.write(f"Email: {email}\n")
                        f.write(f"Subject: {subject}\n")
                        f.write(f"Priority: {priority}\n")
                        f.write(f"Message: {message}\n")
                        f.write("-" * 50 + "\n")
                    
                except Exception as e:
                    st.error("There was an error sending your message. Please try again or contact us directly.")

with col2:
    st.markdown("""
    <div class="contact-section">
    <h2>Other Ways to Reach Us</h2>
    
    <h3>📧 Email Support</h3>
    <ul>
    <li><strong>General:</strong> hello@squeezeai.com</li>
    <li><strong>Support:</strong> support@squeezeai.com</li>
    <li><strong>Billing:</strong> billing@squeezeai.com</li>
    <li><strong>Privacy:</strong> privacy@squeezeai.com</li>
    <li><strong>Legal:</strong> legal@squeezeai.com</li>
    </ul>
    
    <h3>⏰ Response Times</h3>
    <ul>
    <li><strong>High Priority:</strong> 2-4 hours</li>
    <li><strong>Medium Priority:</strong> 12-24 hours</li>
    <li><strong>Low Priority:</strong> 24-48 hours</li>
    </ul>
    
    <h3>🕒 Support Hours</h3>
    <p><strong>Monday - Friday:</strong> 9:00 AM - 6:00 PM EST<br>
    <strong>Saturday:</strong> 10:00 AM - 4:00 PM EST<br>
    <strong>Sunday:</strong> Closed</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="contact-section">
    <h2>📚 Self-Help Resources</h2>
    <p>Before contacting us, you might find answers in our resources:</p>
    <ul>
    <li><a href="/terms" style="color: #00D564;">Terms of Service</a></li>
    <li><a href="/privacy" style="color: #00D564;">Privacy Policy</a></li>
    <li><strong>FAQ:</strong> Coming soon</li>
    <li><strong>User Guide:</strong> Coming soon</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# FAQ Section
st.markdown("""
<div class="contact-section">
<h2>❓ Frequently Asked Questions</h2>

<h3>How do squeeze scores work?</h3>
<p>Our AI analyzes multiple factors including short interest percentage, borrow fees, days to cover, and market momentum to generate a score from 0-100. Higher scores indicate greater squeeze potential.</p>

<h3>How often is data updated?</h3>
<p>Stock data is updated in real-time during market hours. Squeeze scores are recalculated daily to reflect the latest market conditions.</p>

<h3>Can I cancel my subscription anytime?</h3>
<p>Yes! You can cancel your Pro subscription at any time through your account settings. You'll continue to have access until the end of your billing period.</p>

<h3>Is this investment advice?</h3>
<p>No, Squeeze AI provides educational analysis only. We are not licensed financial advisors. Always do your own research and consult with qualified professionals before making investment decisions.</p>

<h3>What payment methods do you accept?</h3>
<p>We accept all major credit cards (Visa, MasterCard, American Express) through our secure Stripe payment processor.</p>

<h3>How do I reset my password?</h3>
<p>Click "Forgot Password?" on the login page and enter your username. We'll send you a temporary password via email.</p>
</div>
""", unsafe_allow_html=True)

# Status page info
st.markdown("""
<div class="contact-section">
<h2>🔧 System Status</h2>
<p>Check our system status and any ongoing issues:</p>
<ul>
<li><strong>Platform Status:</strong> <span style="color: #00D564;">✅ All Systems Operational</span></li>
<li><strong>Data Feed:</strong> <span style="color: #00D564;">✅ Normal</span></li>
<li><strong>Payment Processing:</strong> <span style="color: #00D564;">✅ Normal</span></li>
<li><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</li>
</ul>
</div>
""".format(datetime=datetime), unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2025 Squeeze AI. All rights reserved.")
