# Production Setup Guide for Squeeze AI

## 🚀 Pre-Deployment Checklist

### 1. Environment Variables Configuration
Replace placeholder values in `.env` with actual production credentials:

```bash
# Stripe Settings (from stripe.com dashboard)
STRIPE_SECRET_KEY=sk_live_your_actual_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret

# xAI API (from x.ai)
XAI_API_KEY=xai-your_actual_xai_key

# Email Settings (for password reset)
EMAIL_ADDRESS=your_production_email@domain.com
EMAIL_PASSWORD=your_app_specific_password

# Admin Settings - CHANGE THESE IMMEDIATELY
ADMIN_USERNAME=your_secure_admin_username
ADMIN_PASSWORD=your_secure_hashed_password

# Generate new secret key
SECRET_KEY=your_generated_secret_key_here
```

### 2. Generate Secure Credentials
```python
# Generate secret key:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate hashed admin password:
python -c "import bcrypt; print(bcrypt.hashpw('your_password'.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8'))"
```

### 3. Database Initialization
```bash
# Initialize the database
python database.py

# Create admin user
python admin.py
```

### 4. Test Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Easiest)
1. Push code to GitHub repository
2. Connect to Streamlit Cloud
3. Add environment variables in Streamlit Cloud settings
4. Deploy automatically

### Option 2: Heroku
1. Create Procfile: `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
2. Add buildpacks for Python
3. Configure environment variables
4. Deploy via Git

### Option 3: AWS/GCP/Azure
1. Use container deployment (Docker)
2. Set up load balancer
3. Configure SSL certificates
4. Set up monitoring

### Option 4: VPS/Dedicated Server
1. Install Python and dependencies
2. Use reverse proxy (Nginx)
3. Set up SSL with Let's Encrypt
4. Configure systemd service

## 🔧 Production Configuration

### Nginx Configuration (if using VPS)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Systemd Service (for VPS)
```ini
[Unit]
Description=Squeeze AI Streamlit App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/squeeze-ai
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/streamlit run app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📊 Monitoring & Analytics

### 1. Application Monitoring
- Set up error tracking (Sentry)
- Monitor performance metrics
- Track user engagement
- Monitor payment processing

### 2. Security Monitoring
- Monitor failed login attempts
- Track admin panel access
- Set up alerts for suspicious activity
- Regular security audits

### 3. Business Metrics
- User registration rates
- Subscription conversion rates
- Feature usage analytics
- Revenue tracking

## 🔒 Security Hardening

### 1. SSL/TLS Configuration
- Force HTTPS redirect
- Use strong cipher suites
- Implement HSTS headers
- Regular certificate renewal

### 2. Database Security
- Regular backups
- Access controls
- Connection encryption
- Update security patches

### 3. API Security
- Rate limiting
- Input validation
- Webhook verification
- Error handling

## 🚀 Performance Optimization

### 1. Caching Strategy
- Implement Redis for session storage
- Cache stock data for consistency
- Use CDN for static assets
- Database query optimization

### 2. Scalability
- Horizontal scaling with load balancer
- Database connection pooling
- Async processing for heavy tasks
- Container orchestration

## 📈 Marketing & Launch

### 1. Pre-Launch
- Beta testing with select users
- Performance testing
- Security audit
- Content creation

### 2. Launch Strategy
- Social media presence
- SEO optimization
- Content marketing
- Paid advertising

### 3. Post-Launch
- User feedback collection
- Feature iterations
- Customer support
- Growth optimization

## 💰 Monetization Strategy

### Current: Subscription Model ($29/month)
- Free tier with limited features
- Pro tier with full access
- Clear value proposition

### Future Opportunities
- Annual subscription discounts
- Enterprise plans
- API access tiers
- White-label solutions

## 🔄 Maintenance & Updates

### Regular Tasks
- Dependency updates
- Security patches
- Feature enhancements
- Bug fixes

### Monitoring
- Server health checks
- Database performance
- User activity tracking
- Revenue metrics

## 📞 Support & Documentation

### User Support
- Help documentation
- FAQ section
- Email support
- Live chat (future)

### Developer Documentation
- API documentation
- Deployment guides
- Troubleshooting guides
- Contributing guidelines
