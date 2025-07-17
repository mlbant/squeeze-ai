# 🔐 Streamlit Cloud Environment Variables

Copy these exact values into your Streamlit Cloud app settings under "Secrets":

```toml
# Stripe Settings - LIVE KEYS (get from stripe.com dashboard)
STRIPE_SECRET_KEY = "sk_live_YOUR_LIVE_SECRET_KEY_HERE"
STRIPE_PUBLISHABLE_KEY = "pk_live_YOUR_LIVE_PUBLISHABLE_KEY_HERE"
STRIPE_WEBHOOK_SECRET = "whsec_YOUR_WEBHOOK_SECRET_HERE"

# Admin Settings - PRODUCTION READY
ADMIN_USERNAME = "squeeze_admin"
ADMIN_PASSWORD = "$2b$12$LjSIanrOArjo2DOy9Pql1eEQnW.jDdJ6Uqq5Laj5p05MmMtsX6M9O"

# App Secret - PRODUCTION READY
SECRET_KEY = "QaG8EaYfI12u1vb7fyPXs4l1nQ_65I4JA5_jrQQU2Qc"

# Security Settings
SESSION_TIMEOUT = 3600
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_PER_MINUTE = 60
FORCE_HTTPS = true

# Optional - Email Settings (for password reset)
EMAIL_ADDRESS = "your_production_email@gmail.com"
EMAIL_PASSWORD = "your_gmail_app_password"

# Optional - xAI API (for AI features)
XAI_API_KEY = "your_xai_api_key_here"
```

## 🚨 IMPORTANT: Get Your Live Stripe Keys

1. **Go to your Stripe Dashboard**: https://dashboard.stripe.com/
2. **Switch to LIVE mode** (toggle in top left)
3. **Get your Live keys**:
   - Go to Developers → API keys
   - Copy your **Live Secret key** (starts with `sk_live_`)
   - Copy your **Live Publishable key** (starts with `pk_live_`)
4. **Set up webhook**:
   - Go to Developers → Webhooks
   - Add endpoint: `https://your-streamlit-app-url.streamlit.app/webhook`
   - Select events: `checkout.session.completed`, `invoice.payment_succeeded`
   - Copy the webhook secret (starts with `whsec_`)

## 📝 How to Add to Streamlit Cloud

1. **In your Streamlit Cloud app dashboard**:
   - Click on your app
   - Go to "Settings" → "Secrets"
   - Paste the above TOML format
   - Click "Save"

## ⚠️ Security Notes

- **Never commit these to GitHub** (they're in .gitignore)
- **Use LIVE keys only in production**
- **Test keys are safe for development**
- **Admin password is already hashed and secure**

Your app is ready for production with these settings!
