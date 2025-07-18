# 🚀 Domain Deployment Guide: squeeze-ai.com

## Overview
This guide will help you deploy your Squeeze-Ai application to your purchased domain `squeeze-ai.com` for Stripe verification and production use.

## 🏗️ Deployment Options

### Option 1: Railway (Recommended - Easiest)
**Cost**: ~$5/month | **Setup Time**: 15 minutes | **Stripe Compatible**: ✅

#### Step 1: Prepare Your App
```bash
# 1. Create a Procfile in your project root
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# 2. Create requirements.txt if not exists
pip freeze > requirements.txt

# 3. Create runtime.txt (optional but recommended)
echo "python-3.11.0" > runtime.txt
```

#### Step 2: Deploy to Railway
1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Connect GitHub**: Link your GitHub account
3. **Push to GitHub**: 
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```
4. **Create Railway Project**: Click "New Project" → "Deploy from GitHub repo"
5. **Select Repository**: Choose your squeeze-ai repository
6. **Auto-deploy**: Railway will automatically deploy your app

#### Step 3: Configure Environment Variables
In Railway dashboard, go to your project → Variables tab:
```
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
XAI_API_KEY=your_xai_api_key
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SECRET_KEY=your_secret_key_here
ADMIN_USERNAME=squeeze_admin
ADMIN_PASSWORD=$2b$12$LjSIanrOArjo2DOy9Pql1eEQnW.jDdJ6Uqq5Laj5p05MmMtsX6M9O
```

#### Step 4: Connect Your Domain
1. **Get Railway URL**: Copy your Railway app URL (e.g., `https://squeeze-ai-production.up.railway.app`)
2. **Add Custom Domain**: In Railway dashboard, go to Settings → Domains
3. **Add Domain**: Enter `squeeze-ai.com` and `www.squeeze-ai.com`
4. **Get DNS Records**: Railway will provide DNS records

#### Step 5: Configure DNS in Namecheap
1. **Login to Namecheap**: Go to your Namecheap account
2. **Manage Domain**: Click "Manage" next to squeeze-ai.com
3. **Advanced DNS**: Go to Advanced DNS tab
4. **Add Records**:
   ```
   Type: A Record
   Host: @
   Value: [Railway IP from dashboard]
   TTL: 30 min

   Type: CNAME Record
   Host: www
   Value: [Railway domain from dashboard]
   TTL: 30 min
   ```

---

### Option 2: DigitalOcean App Platform
**Cost**: ~$12/month | **Setup Time**: 20 minutes | **Stripe Compatible**: ✅

#### Step 1: Prepare Your App
```bash
# Create .do/app.yaml
mkdir -p .do
cat > .do/app.yaml << 'EOF'
name: squeeze-ai
services:
- name: web
  source_dir: /
  github:
    repo: your-username/squeeze-ai
    branch: main
  run_command: streamlit run app.py --server.port=8080 --server.address=0.0.0.0
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  envs:
  - key: PORT
    value: "8080"
domains:
- domain: squeeze-ai.com
- domain: www.squeeze-ai.com
EOF
```

#### Step 2: Deploy to DigitalOcean
1. **Sign up**: Go to [digitalocean.com](https://digitalocean.com)
2. **Create App**: Go to Apps → Create App
3. **Connect GitHub**: Link your repository
4. **Configure**: Use the app.yaml configuration
5. **Add Environment Variables**: Same as Railway above
6. **Deploy**: Click "Create Resources"

#### Step 3: Configure Domain
1. **Get App URL**: Copy your DigitalOcean app URL
2. **Add Domain**: In app settings, add squeeze-ai.com
3. **Update DNS**: DigitalOcean will provide DNS records for Namecheap

---

### Option 3: AWS Elastic Beanstalk
**Cost**: ~$15/month | **Setup Time**: 30 minutes | **Stripe Compatible**: ✅

#### Step 1: Prepare Your App
```bash
# Create .ebextensions/01_streamlit.config
mkdir -p .ebextensions
cat > .ebextensions/01_streamlit.config << 'EOF'
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application.py
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current:$PYTHONPATH
  aws:elasticbeanstalk:container:python:environment:
    STREAMLIT_SERVER_PORT: 8501
EOF

# Create application.py
cat > application.py << 'EOF'
import subprocess
import sys
import os

def run_streamlit():
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ])

if __name__ == "__main__":
    run_streamlit()
EOF
```

#### Step 2: Deploy to AWS
1. **Install AWS CLI**: Download and install AWS CLI
2. **Install EB CLI**: `pip install awsebcli`
3. **Initialize**: `eb init squeeze-ai`
4. **Create Environment**: `eb create squeeze-ai-prod`
5. **Deploy**: `eb deploy`

#### Step 3: Configure Domain
1. **Route 53**: Set up hosted zone for squeeze-ai.com
2. **Update Namecheap**: Point nameservers to AWS Route 53
3. **SSL Certificate**: Request SSL certificate in AWS Certificate Manager

---

## 🌐 DNS Configuration (Namecheap)

### For Railway/DigitalOcean:
```
Type: A Record
Host: @
Value: [Your hosting provider's IP]
TTL: 30 min

Type: CNAME Record
Host: www
Value: [Your hosting provider's domain]
TTL: 30 min
```

### For AWS:
```
Type: NS Record
Host: @
Value: [AWS Route 53 nameservers]
TTL: 1 hour
```

## 🔒 SSL Certificate Setup

### Railway/DigitalOcean:
- SSL certificates are automatically provided
- Your site will be accessible at `https://squeeze-ai.com`

### AWS:
- Request SSL certificate in AWS Certificate Manager
- Add certificate to your load balancer
- Update Route 53 records

## 🚀 Production Deployment Steps

### Step 1: Update Production Settings
```bash
# Update app.py for production
# Add this at the top of app.py:
import os
if os.environ.get('ENVIRONMENT') == 'production':
    st.set_page_config(
        page_title="Squeeze-Ai.com - Stock Squeeze Analysis",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
```

### Step 2: Environment Variables
Ensure all environment variables are set in your hosting platform:
```
STRIPE_SECRET_KEY=sk_live_... (use live keys for production)
STRIPE_PUBLISHABLE_KEY=pk_live_...
XAI_API_KEY=your_xai_api_key
EMAIL_ADDRESS=support@squeeze-ai.com
EMAIL_PASSWORD=your_app_password
SECRET_KEY=your_production_secret_key
ADMIN_USERNAME=squeeze_admin
ADMIN_PASSWORD=your_hashed_password
ENVIRONMENT=production
```

### Step 3: Test Deployment
1. **Check Domain**: Visit `https://squeeze-ai.com`
2. **Test Authentication**: Try logging in with test accounts
3. **Test Admin Panel**: Access `https://squeeze-ai.com/admin.py`
4. **Verify SSL**: Ensure HTTPS is working properly

## 📝 Post-Deployment Checklist

- [ ] Domain resolves to your application
- [ ] HTTPS/SSL certificate is active
- [ ] User authentication works
- [ ] Admin panel accessible
- [ ] Database functionality working
- [ ] Email notifications working
- [ ] Stripe webhook endpoints accessible
- [ ] All environment variables set
- [ ] Error logging configured

## 🔧 Troubleshooting

### Common Issues:

1. **Domain not resolving**: Check DNS propagation (can take 24-48 hours)
2. **SSL certificate issues**: Verify domain ownership and DNS records
3. **App not starting**: Check logs for missing environment variables
4. **Database errors**: Ensure SQLite file is properly initialized

### Debugging Commands:
```bash
# Check DNS propagation
nslookup squeeze-ai.com

# Test SSL certificate
curl -I https://squeeze-ai.com

# Check app logs (Railway)
railway logs

# Check app logs (DigitalOcean)
doctl apps logs <app-id>
```

## 💡 Recommended: Start with Railway

For the fastest deployment to get Stripe verification:

1. **Deploy to Railway** (15 minutes)
2. **Configure DNS** (wait 2-24 hours for propagation)
3. **Test your live site** at squeeze-ai.com
4. **Submit to Stripe** for verification

## 🎯 Next Steps After Deployment

1. **Stripe Integration**: Once live, update your Stripe settings with your domain
2. **Google Analytics**: Add tracking code for user analytics
3. **Monitoring**: Set up uptime monitoring
4. **Backup**: Configure database backups
5. **CDN**: Consider Cloudflare for performance

## 📞 Support

If you encounter issues:
- Check the hosting platform's documentation
- Review DNS propagation status
- Verify all environment variables are set
- Check application logs for errors

Your application will be live at `https://squeeze-ai.com` once deployment is complete!