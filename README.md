# 🚀 Squeeze AI - Stock Squeeze Analysis Platform

A comprehensive AI-powered platform for analyzing short squeeze opportunities in the stock market. Built with Streamlit, featuring real-time data analysis, user authentication, payment processing, and advanced security measures.

## ✨ Features

### Core Functionality
- **Real-time Squeeze Scanner**: Analyze thousands of stocks for squeeze potential
- **Individual Stock Analysis**: Deep dive into specific stocks with historical data
- **AI-Powered Insights**: Advanced algorithms to identify squeeze opportunities
- **Interactive Charts**: Beautiful visualizations with Altair and Plotly
- **Filtering System**: Filter by sector, market cap, and volatility

### User Management
- **Secure Authentication**: Multi-factor authentication with session management
- **User Registration**: Easy sign-up process with email verification
- **Guest Access**: Limited trial access for new users
- **Password Recovery**: Secure password reset via email

### Payment Integration
- **Stripe Integration**: Secure subscription management
- **Tiered Access**: Free and Pro subscription tiers
- **Webhook Handling**: Real-time payment processing
- **Subscription Management**: Easy upgrade/downgrade options

### Security Features
- **Enterprise-grade Security**: Comprehensive security implementation
- **Rate Limiting**: Protection against abuse and DDoS
- **Input Validation**: SQL injection and XSS prevention
- **Secure Sessions**: Token-based authentication with expiration
- **Admin Panel**: Secure administrative interface

## 🛠️ Technology Stack

- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python with SQLite database
- **Authentication**: Streamlit-authenticator with bcrypt
- **Payments**: Stripe API integration
- **Data**: yfinance for real-time stock data
- **AI**: xAI API for intelligent analysis
- **Deployment**: Docker, Docker Compose, Nginx
- **Security**: Comprehensive security measures

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### Option 1: Windows Users
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd squeeze-ai
   ```

2. **Run the deployment script**
   ```bash
   deploy.bat
   ```
   
3. **Follow the menu options**
   - Choose option 6 for full setup
   - Then option 4 to run the application

### Option 2: Linux/Mac Users
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd squeeze-ai
   ```

2. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```
   
3. **Follow the menu options**
   - Choose option 6 for full deployment

### Option 3: Manual Setup
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

3. **Initialize database**
   ```bash
   python database.py
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file with the following variables:

```bash
# Stripe Settings (get from stripe.com dashboard)
STRIPE_SECRET_KEY=sk_live_your_actual_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret

# xAI API (get from x.ai)
XAI_API_KEY=xai-your_actual_xai_key

# Email Settings (for password reset)
EMAIL_ADDRESS=your_production_email@domain.com
EMAIL_PASSWORD=your_app_specific_password

# Admin Settings - CHANGE THESE IMMEDIATELY
ADMIN_USERNAME=your_secure_admin_username
ADMIN_PASSWORD=your_secure_hashed_password

# App Secret (generate new)
SECRET_KEY=your_generated_secret_key_here

# Security Settings
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_PER_MINUTE=60
FORCE_HTTPS=true
```

### Generate Secure Credentials
```python
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate hashed admin password
python -c "import bcrypt; print(bcrypt.hashpw('your_password'.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8'))"
```

## 🐳 Docker Deployment

### Local Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Production Docker Deployment
1. **Set up SSL certificates** in the `ssl/` directory
2. **Configure domain** in `nginx.conf`
3. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 🌐 Deployment Options

### 1. Streamlit Cloud (Recommended for beginners)
- Push code to GitHub
- Connect to Streamlit Cloud
- Add environment variables
- Deploy automatically

### 2. Heroku
- Create `Procfile`
- Configure buildpacks
- Set environment variables
- Deploy via Git

### 3. AWS/GCP/Azure
- Use container services
- Set up load balancer
- Configure SSL certificates
- Set up monitoring

### 4. VPS/Dedicated Server
- Install dependencies
- Configure reverse proxy
- Set up SSL with Let's Encrypt
- Configure systemd service

## 🔒 Security

This application implements enterprise-grade security measures:

- **Authentication**: Secure user authentication with session management
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: Protection against abuse
- **SSL/TLS**: Encrypted connections
- **Security Headers**: HSTS, CSP, and other security headers
- **Database Security**: Parameterized queries and access controls

See `SECURITY_GUIDE.md` for detailed security information.

## 📊 Features Overview

### Free Tier
- Limited squeeze scanner (top 1 result)
- Single stock analysis (1 per session)
- Basic charts and metrics
- Guest access

### Pro Tier ($29/month)
- Full squeeze scanner (top 5 results)
- Unlimited stock analysis
- Advanced filtering options
- Historical performance data
- Real-time alerts
- Priority support

## 🛠️ Development

### Project Structure
```
squeeze-ai/
├── app.py                 # Main Streamlit application
├── backend.py             # Backend logic and data processing
├── database.py            # Database operations
├── secure_auth.py         # Authentication system
├── stripe_handler.py      # Payment processing
├── admin.py              # Admin panel
├── security_config.py    # Security configuration
├── pages/                # Additional pages
│   ├── terms.py
│   ├── privacy.py
│   └── contact.py
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── nginx.conf          # Nginx configuration
├── deploy.sh           # Linux/Mac deployment script
├── deploy.bat          # Windows deployment script
└── README.md           # This file
```

### Adding New Features
1. **Backend Logic**: Add functions to `backend.py`
2. **Database Changes**: Update `database.py`
3. **Frontend**: Modify `app.py` or create new pages
4. **Security**: Update `security_config.py` if needed

### Testing
```bash
# Run basic tests
python -m pytest tests/

# Test specific components
python backend.py
python database.py
```

## 📈 Monitoring & Analytics

### Application Monitoring
- Error tracking with Sentry
- Performance metrics
- User engagement tracking
- Payment processing monitoring

### Business Metrics
- User registration rates
- Subscription conversion rates
- Feature usage analytics
- Revenue tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Documentation
- `PRODUCTION_SETUP.md` - Detailed deployment guide
- `SECURITY_GUIDE.md` - Security implementation details
- `API_DOCS.md` - API documentation (if applicable)

### Getting Help
- Create an issue on GitHub
- Check the FAQ section
- Contact support: support@squeezeai.com

### Common Issues
1. **Database Connection Error**: Ensure SQLite is properly installed
2. **Stripe Webhook Issues**: Check webhook endpoint configuration
3. **Authentication Problems**: Verify environment variables
4. **Performance Issues**: Check rate limiting settings

## 🔄 Updates & Maintenance

### Regular Tasks
- Update dependencies monthly
- Monitor security patches
- Review user feedback
- Optimize performance

### Version Updates
- Follow semantic versioning
- Maintain changelog
- Test thoroughly before deployment
- Backup database before major updates

## 🎯 Roadmap

### Short-term (1-3 months)
- Mobile app development
- Advanced filtering options
- Real-time notifications
- API access for developers

### Medium-term (3-6 months)
- Machine learning improvements
- Social features
- Portfolio tracking
- Advanced analytics

### Long-term (6+ months)
- Multi-market support
- Enterprise features
- White-label solutions
- Advanced AI integration

---

**Built with ❤️ for the trading community**

For detailed deployment instructions, see `PRODUCTION_SETUP.md`
For security information, see `SECURITY_GUIDE.md`
