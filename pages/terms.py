import streamlit as st


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
    .terms-section {
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
</style>
""", unsafe_allow_html=True)

if st.button("← Back to Home", type="secondary"):
    try:
        st.switch_page("app.py")
    except Exception as e:
        # Fallback navigation
        st.rerun()

st.title("📋 Terms of Service")
st.markdown("*Last updated: January 15, 2025*")

st.markdown("""
<div class="terms-section">
<h2>1. Acceptance of Terms</h2>
<p>By accessing and using Squeeze Ai ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>2. Description of Service</h2>
<p>Squeeze Ai is a financial analysis platform that provides:</p>
<ul>
<li>Stock squeeze potential analysis and scoring</li>
<li>Market data visualization and charts</li>
<li>Educational content about short squeeze mechanics</li>
<li>Historical price and volume data</li>
</ul>
<p><strong>IMPORTANT:</strong> Squeeze Ai is for educational and informational purposes only. It is NOT investment advice.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>3. Investment Disclaimer</h2>
<p><strong>NOT INVESTMENT ADVICE:</strong> The information provided by Squeeze Ai does not constitute investment advice, financial advice, trading advice, or any other sort of advice. You should not treat any of the website's content as such.</p>
<p><strong>DO YOUR OWN RESEARCH:</strong> Before making any investment decisions, you should conduct your own research and consult with qualified financial advisors.</p>
<p><strong>HIGH RISK:</strong> Short squeeze investments are extremely high-risk and volatile. You may lose all of your investment.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>4. User Responsibilities</h2>
<p>You agree to:</p>
<ul>
<li>Use the service only for lawful purposes</li>
<li>Not attempt to gain unauthorized access to our systems</li>
<li>Not use the service to manipulate markets or engage in illegal activities</li>
<li>Maintain the confidentiality of your account credentials</li>
<li>Accept full responsibility for all activities under your account</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>5. Data Accuracy</h2>
<p>While we strive to provide accurate information:</p>
<ul>
<li>Market data may be delayed or contain errors</li>
<li>Squeeze scores are algorithmic estimates, not guarantees</li>
<li>Historical performance does not predict future results</li>
<li>We do not guarantee the accuracy, completeness, or timeliness of any information</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>6. Subscription Terms</h2>
<p><strong>Pro Subscription:</strong></p>
<ul>
<li>Monthly subscription fee of $29.00</li>
<li>Automatic renewal unless cancelled</li>
<li>Cancel anytime through your account settings</li>
<li>No refunds for partial months</li>
<li>Price changes will be communicated 30 days in advance</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>7. Limitation of Liability</h2>
<p>Squeeze Ai and its operators shall not be liable for:</p>
<ul>
<li>Any investment losses or financial damages</li>
<li>Decisions made based on information from our platform</li>
<li>Service interruptions or technical issues</li>
<li>Data inaccuracies or system errors</li>
<li>Third-party actions or market volatility</li>
</ul>
<p><strong>Maximum liability is limited to the amount paid for the service in the past 12 months.</strong></p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>8. Privacy and Data</h2>
<p>Your privacy is important to us. Please review our <span style="color: #00D564;">Privacy Policy</span> (available in sidebar navigation) to understand how we collect, use, and protect your information.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>9. Prohibited Uses</h2>
<p>You may not use Squeeze Ai to:</p>
<ul>
<li>Engage in market manipulation or pump-and-dump schemes</li>
<li>Distribute malware or harmful code</li>
<li>Violate any applicable laws or regulations</li>
<li>Infringe on intellectual property rights</li>
<li>Harass other users or our staff</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>10. Termination</h2>
<p>We reserve the right to:</p>
<ul>
<li>Terminate or suspend accounts for violations of these terms</li>
<li>Modify or discontinue the service at any time</li>
<li>Remove content that violates our policies</li>
</ul>
<p>You may terminate your account at any time by contacting us.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>11. Changes to Terms</h2>
<p>We may update these terms from time to time. Changes will be posted on this page with an updated "Last modified" date. Continued use of the service after changes constitutes acceptance of the new terms.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>12. Contact Information</h2>
<p>If you have questions about these Terms of Service, please contact us:</p>
<ul>
<li>Email: support@squeeze-ai.com</li>
<li>Contact Form: <span style="color: #00D564;">Contact Us</span> (available in sidebar navigation)</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="terms-section">
<h2>13. Governing Law</h2>
<p>These terms shall be governed by and construed in accordance with the laws of the United States. Any disputes shall be resolved in the appropriate courts.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2025 Squeeze Ai. All rights reserved.")
