import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import dotenv

dotenv.load_dotenv()

class EmailService:
    def __init__(self):
        # Email configuration - Google Workspace SMTP
        self.smtp_server = "smtp.gmail.com"  # Google Workspace uses same SMTP as Gmail
        self.smtp_port = 587
        self.sender_email = os.getenv("SENDER_EMAIL")  # Your Google Workspace email
        self.sender_password = os.getenv("SENDER_APP_PASSWORD")  # Google Workspace App Password
        self.support_email = os.getenv("SUPPORT_EMAIL", "support@squeeze-ai.com")
        
    def send_email(self, to_email, subject, html_body, text_body=None):
        """Send an email using Gmail SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            # Create the plain-text and HTML version of your message
            if text_body:
                part1 = MIMEText(text_body, "plain")
                message.attach(part1)
            
            part2 = MIMEText(html_body, "html")
            message.attach(part2)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_welcome_email(self, user_email, username):
        """Send welcome email to new users"""
        subject = "Welcome to Squeeze Ai! 🚀"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0e1117; color: #fafafa; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #00D564; color: #0e1117; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #1f2937; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ background-color: #00D564; color: #0e1117; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #9ca3af; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Squeeze Ai! 🚀</h1>
                </div>
                <div class="content">
                    <h2>Hi {username}!</h2>
                    <p>Thank you for joining Squeeze Ai - your Ai-powered short squeeze analysis platform.</p>
                    
                    <h3>What you can do now:</h3>
                    <ul>
                        <li>🔍 <strong>Free Market Scan:</strong> Discover top squeeze candidates</li>
                        <li>📊 <strong>Free Stock Analysis:</strong> Analyze any stock for squeeze potential</li>
                        <li>📈 <strong>Interactive Charts:</strong> View historical price data</li>
                    </ul>
                    
                    <h3>Want more? Upgrade to Pro:</h3>
                    <ul>
                        <li>✅ Unlimited market scans and stock analysis</li>
                        <li>✅ Advanced filtering options</li>
                        <li>✅ Portfolio tracking with real-time updates</li>
                        <li>✅ Priority support</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="https://squeeze-ai.com" class="button">Start Analyzing Stocks</a>
                    </div>
                    
                    <p>Need help? Reply to this email or contact our support team.</p>
                    
                    <p>Happy trading!<br>
                    The Squeeze Ai Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Squeeze Ai. All rights reserved.</p>
                    <p>This email was sent to {user_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to Squeeze Ai! 🚀
        
        Hi {username}!
        
        Thank you for joining Squeeze Ai - your Ai-powered short squeeze analysis platform.
        
        What you can do now:
        - Free Market Scan: Discover top squeeze candidates
        - Free Stock Analysis: Analyze any stock for squeeze potential
        - Interactive Charts: View historical price data
        
        Want more? Upgrade to Pro for unlimited access and portfolio tracking.
        
        Get started: https://squeeze-ai.com
        
        Happy trading!
        The Squeeze Ai Team
        """
        
        return self.send_email(user_email, subject, html_body, text_body)
    
    def send_password_reset_email(self, user_email, username, reset_token):
        """Send modern password reset email with secure reset link"""
        subject = "Reset Your Squeeze Ai Password"
        
        # Create reset link (you'll need to implement the reset page)
        reset_url = f"https://squeeze-ai.com?reset_token={reset_token}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #0e1117;
                    color: #fafafa;
                    line-height: 1.6;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 40px auto; 
                    background: #1f2937;
                    border-radius: 12px;
                    overflow: hidden;
                    border: 1px solid #374151;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                }}
                .header {{ 
                    background: #00D564;
                    color: #0e1117;
                    padding: 40px 40px 30px;
                    text-align: center;
                }}
                .header h1 {{ 
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    color: #0e1117;
                }}
                .header p {{ 
                    font-size: 16px;
                    opacity: 0.8;
                    color: #0e1117;
                }}
                .content {{ 
                    padding: 40px;
                    background: #1f2937;
                }}
                .greeting {{ 
                    font-size: 18px;
                    font-weight: 600;
                    color: #fafafa;
                    margin-bottom: 20px;
                }}
                .message {{ 
                    font-size: 16px;
                    color: #9ca3af;
                    margin-bottom: 30px;
                    line-height: 1.7;
                }}
                .reset-button {{ 
                    display: inline-block;
                    background: #00D564;
                    color: #0e1117;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 14px rgba(0, 213, 100, 0.3);
                    transition: all 0.3s ease;
                    margin: 20px 0;
                }}
                .reset-button:hover {{ 
                    background: #00E56F;
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0, 213, 100, 0.4);
                }}
                .expiry-notice {{ 
                    background: #374151;
                    border: 1px solid #4b5563;
                    color: #fbbf24;
                    padding: 16px;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .help-text {{ 
                    font-size: 14px;
                    color: #9ca3af;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #374151;
                }}
                .footer {{ 
                    background: #0e1117;
                    padding: 30px 40px;
                    text-align: center;
                    border-top: 1px solid #374151;
                }}
                .footer p {{ 
                    font-size: 14px;
                    color: #9ca3af;
                    margin: 5px 0;
                }}
                .logo {{ 
                    font-size: 24px;
                    font-weight: 800;
                    margin-bottom: 8px;
                    color: #0e1117;
                }}
                @media (max-width: 600px) {{
                    .container {{ margin: 20px; }}
                    .header, .content {{ padding: 30px 20px; }}
                    .footer {{ padding: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">Squeeze Ai</div>
                    <h1>Reset Your Password</h1>
                    <p>Secure and easy password reset</p>
                </div>
                
                <div class="content">
                    <div class="greeting">Hi {username},</div>
                    
                    <div class="message">
                        We received a request to reset your Squeeze Ai password. Click the button below to create a new password for your account.
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" class="reset-button">Reset My Password</a>
                    </div>
                    
                    <div class="expiry-notice">
                        <strong>⏰ Important:</strong> This reset link will expire in 1 hour for security reasons.
                    </div>
                    
                    <div class="help-text">
                        <p><strong>Didn't request this reset?</strong><br>
                        If you didn't request a password reset, you can safely ignore this email. Your account remains secure.</p>
                        
                        <p><strong>Having trouble?</strong><br>
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <span style="word-break: break-all; color: #00D564; font-family: monospace;">{reset_url}</span></p>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Squeeze Ai Team</strong></p>
                    <p>Ai-Powered Stock Analysis Platform</p>
                    <p style="margin-top: 15px;">© 2025 Squeeze Ai. All rights reserved.</p>
                    <p>This email was sent to {user_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Reset Your Squeeze Ai Password
        
        Hi {username},
        
        We received a request to reset your Squeeze Ai password.
        
        Click this link to reset your password: {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request this reset, you can safely ignore this email.
        
        Best regards,
        The Squeeze Ai Team
        
        ---
        Squeeze Ai - Ai-Powered Stock Analysis Platform
        © 2025 Squeeze Ai. All rights reserved.
        This email was sent to {user_email}
        """
        
        return self.send_email(user_email, subject, html_body, text_body)
    
    def send_contact_form_email(self, user_name, user_email, subject, message, priority):
        """Send contact form submission to support team"""
        email_subject = f"[Squeeze Ai Contact] {subject} - {priority} Priority"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #00D564; color: #fff; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #fff; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #ddd; }}
                .info-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .priority-high {{ border-left: 4px solid #ef4444; }}
                .priority-medium {{ border-left: 4px solid #f59e0b; }}
                .priority-low {{ border-left: 4px solid #10b981; }}
                .message-content {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Contact Form Submission</h1>
                </div>
                <div class="content">
                    <div class="info-box priority-{priority.lower()}">
                        <h3>Contact Information</h3>
                        <p><strong>Name:</strong> {user_name}</p>
                        <p><strong>Email:</strong> {user_email}</p>
                        <p><strong>Subject:</strong> {subject}</p>
                        <p><strong>Priority:</strong> {priority}</p>
                        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</p>
                    </div>
                    
                    <h3>Message:</h3>
                    <div class="message-content">
                        {message.replace(chr(10), '<br>')}
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p><strong>Response Required:</strong> Please respond to {user_email} within:</p>
                        <ul>
                            <li>High Priority: 2-4 hours</li>
                            <li>Medium Priority: 12-24 hours</li>
                            <li>Low Priority: 24-48 hours</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(self.support_email, email_subject, html_body)
    
    def send_contact_confirmation_email(self, user_email, user_name, subject):
        """Send confirmation email to user who submitted contact form"""
        email_subject = "We received your message - Squeeze Ai Support"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0e1117; color: #fafafa; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #00D564; color: #0e1117; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #1f2937; padding: 30px; border-radius: 0 0 8px 8px; }}
                .info-box {{ background-color: #374151; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #9ca3af; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Message Received! 📧</h1>
                </div>
                <div class="content">
                    <h2>Hi {user_name}!</h2>
                    <p>Thank you for contacting Squeeze Ai support. We've received your message and will respond as soon as possible.</p>
                    
                    <div class="info-box">
                        <h3>Your Message Details:</h3>
                        <p><strong>Subject:</strong> {subject}</p>
                        <p><strong>Submitted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</p>
                        <p><strong>Reference ID:</strong> #{datetime.now().strftime('%Y%m%d%H%M%S')}</p>
                    </div>
                    
                    <h3>Response Times:</h3>
                    <ul>
                        <li><strong>High Priority:</strong> 2-4 hours</li>
                        <li><strong>Medium Priority:</strong> 12-24 hours</li>
                        <li><strong>Low Priority:</strong> 24-48 hours</li>
                    </ul>
                    
                    <p>In the meantime, you can check our FAQ section or explore more features on the platform.</p>
                    
                    <p>Best regards,<br>
                    The Squeeze Ai Support Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Squeeze Ai. All rights reserved.</p>
                    <p>This email was sent to {user_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Message Received! 📧
        
        Hi {user_name}!
        
        Thank you for contacting Squeeze Ai support. We've received your message and will respond as soon as possible.
        
        Your Message Details:
        Subject: {subject}
        Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST
        Reference ID: #{datetime.now().strftime('%Y%m%d%H%M%S')}
        
        Response Times:
        - High Priority: 2-4 hours
        - Medium Priority: 12-24 hours  
        - Low Priority: 24-48 hours
        
        Best regards,
        The Squeeze Ai Support Team
        """
        
        return self.send_email(user_email, email_subject, html_body, text_body)

# Create global email service instance
email_service = EmailService()