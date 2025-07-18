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
    .privacy-section {
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

st.title("🔒 Privacy Policy")
st.markdown("*Last updated: January 15, 2025*")

st.markdown("""
<div class="privacy-section">
<h2>1. Information We Collect</h2>
<h3>Personal Information</h3>
<ul>
<li><strong>Account Information:</strong> Username, email address, password (encrypted)</li>
<li><strong>Profile Data:</strong> Name, preferences, subscription status</li>
<li><strong>Payment Information:</strong> Processed securely through Stripe (we don't store card details)</li>
</ul>

<h3>Usage Information</h3>
<ul>
<li><strong>Activity Data:</strong> Stocks searched, scans performed, features used</li>
<li><strong>Technical Data:</strong> IP address, browser type, device information</li>
<li><strong>Performance Data:</strong> Page load times, error logs, system performance</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>2. How We Use Your Information</h2>
<ul>
<li><strong>Service Delivery:</strong> Provide squeeze analysis, maintain your account</li>
<li><strong>Personalization:</strong> Customize your experience and recommendations</li>
<li><strong>Communication:</strong> Send important updates, security alerts</li>
<li><strong>Improvement:</strong> Analyze usage patterns to enhance our platform</li>
<li><strong>Security:</strong> Detect fraud, prevent abuse, ensure platform security</li>
<li><strong>Legal Compliance:</strong> Meet regulatory requirements and legal obligations</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>3. Information Sharing</h2>
<p><strong>We do NOT sell your personal information.</strong></p>

<h3>We may share information with:</h3>
<ul>
<li><strong>Service Providers:</strong> Stripe for payments, hosting providers for infrastructure</li>
<li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
<li><strong>Business Transfers:</strong> In case of merger, acquisition, or sale of assets</li>
<li><strong>Consent:</strong> When you explicitly authorize sharing</li>
</ul>

<h3>We do NOT share with:</h3>
<ul>
<li>Advertisers or marketing companies</li>
<li>Data brokers or aggregators</li>
<li>Social media platforms</li>
<li>Unauthorized third parties</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>4. Data Security</h2>
<p>We implement industry-standard security measures:</p>
<ul>
<li><strong>Encryption:</strong> All data encrypted in transit and at rest</li>
<li><strong>Access Controls:</strong> Strict employee access limitations</li>
<li><strong>Monitoring:</strong> 24/7 security monitoring and threat detection</li>
<li><strong>Regular Audits:</strong> Periodic security assessments and updates</li>
<li><strong>Secure Infrastructure:</strong> Protected servers and databases</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>5. Your Privacy Rights</h2>
<p>You have the right to:</p>
<ul>
<li><strong>Access:</strong> Request a copy of your personal data</li>
<li><strong>Correction:</strong> Update or correct inaccurate information</li>
<li><strong>Deletion:</strong> Request deletion of your account and data</li>
<li><strong>Portability:</strong> Export your data in a readable format</li>
<li><strong>Opt-out:</strong> Unsubscribe from marketing communications</li>
<li><strong>Restriction:</strong> Limit how we process your information</li>
</ul>

<p>To exercise these rights, contact us at support@squeeze-ai.com</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>6. Cookies and Tracking</h2>
<h3>We use cookies for:</h3>
<ul>
<li><strong>Authentication:</strong> Keep you logged in securely</li>
<li><strong>Preferences:</strong> Remember your settings and choices</li>
<li><strong>Analytics:</strong> Understand how you use our platform</li>
<li><strong>Performance:</strong> Optimize loading times and functionality</li>
</ul>

<h3>Cookie Types:</h3>
<ul>
<li><strong>Essential:</strong> Required for basic functionality (cannot be disabled)</li>
<li><strong>Functional:</strong> Enhance user experience and preferences</li>
<li><strong>Analytics:</strong> Help us improve our service (can be disabled)</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>7. Data Retention</h2>
<ul>
<li><strong>Account Data:</strong> Retained while your account is active</li>
<li><strong>Usage Data:</strong> Kept for 2 years for analytics and improvement</li>
<li><strong>Payment Data:</strong> Retained per legal requirements (typically 7 years)</li>
<li><strong>Support Data:</strong> Kept for 3 years for quality assurance</li>
<li><strong>Deleted Accounts:</strong> Data permanently deleted within 30 days</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>8. International Data Transfers</h2>
<p>Your data may be processed in countries other than your own. We ensure:</p>
<ul>
<li>Adequate protection through legal frameworks</li>
<li>Standard contractual clauses with service providers</li>
<li>Compliance with applicable data protection laws</li>
<li>Regular assessment of transfer mechanisms</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>9. Children's Privacy</h2>
<p>Squeeze Ai is not intended for users under 18 years old. We do not knowingly collect personal information from children. If we discover we have collected information from a child, we will delete it immediately.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>10. Third-Party Services</h2>
<h3>We integrate with:</h3>
<ul>
<li><strong>Stripe:</strong> Payment processing (see Stripe's privacy policy)</li>
<li><strong>Yahoo Finance:</strong> Market data (public information only)</li>
<li><strong>xAI:</strong> Ai analysis (anonymized data only)</li>
</ul>
<p>These services have their own privacy policies and practices.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>11. California Privacy Rights (CCPA)</h2>
<p>California residents have additional rights:</p>
<ul>
<li>Right to know what personal information is collected</li>
<li>Right to delete personal information</li>
<li>Right to opt-out of sale (we don't sell data)</li>
<li>Right to non-discrimination for exercising privacy rights</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>12. European Privacy Rights (GDPR)</h2>
<p>EU residents have rights under GDPR:</p>
<ul>
<li>Legal basis for processing (legitimate interest, consent, contract)</li>
<li>Right to object to processing</li>
<li>Right to lodge complaints with supervisory authorities</li>
<li>Data Protection Officer contact: support@squeeze-ai.com</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>13. Changes to This Policy</h2>
<p>We may update this privacy policy to reflect:</p>
<ul>
<li>Changes in our practices</li>
<li>Legal or regulatory requirements</li>
<li>New features or services</li>
</ul>
<p>We'll notify you of significant changes via email or platform notification.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-section">
<h2>14. Contact Us</h2>
<p>For privacy-related questions or requests:</p>
<ul>
<li><strong>Email:</strong> support@squeeze-ai.com</li>
<li><strong>Contact Form:</strong> <a href="/contact" style="color: #00D564;">Contact Us</a></li>
<li><strong>Mail:</strong> Squeeze Ai Privacy Team, [Address]</li>
</ul>
<p>We'll respond to privacy requests within 30 days.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2025 Squeeze Ai. All rights reserved.")
