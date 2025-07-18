# 🚀 Quick Deploy to squeeze-ai.com

## Fastest Path: Railway Deployment (15 minutes)

### Step 1: Push to GitHub
```bash
# Add all files for deployment
git add .
git commit -m "Ready for production deployment"
git push origin main
```

### Step 2: Deploy to Railway
1. **Go to**: [railway.app](https://railway.app)
2. **Sign up**: Use your GitHub account
3. **New Project**: Click "New Project"
4. **Deploy from GitHub**: Select your squeeze-ai repository
5. **Wait**: Railway will automatically deploy (2-3 minutes)

### Step 3: Add Environment Variables
In Railway dashboard → Your Project → Variables:
```
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
XAI_API_KEY=your_xai_api_key
EMAIL_ADDRESS=acusumano618@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
SECRET_KEY=your_secret_key_here
ADMIN_USERNAME=squeeze_admin
ADMIN_PASSWORD=$2b$12$LjSIanrOArjo2DOy9Pql1eEQnW.jDdJ6Uqq5Laj5p05MmMtsX6M9O
ENVIRONMENT=production
```

### Step 4: Get Your Railway URL
- Copy the URL from Railway dashboard (e.g., `https://squeeze-ai-production.up.railway.app`)
- **Test it**: Make sure your app loads and works

### Step 5: Connect Your Domain
1. **Railway Dashboard**: Go to Settings → Domains
2. **Add Domain**: Enter `squeeze-ai.com`
3. **Add WWW**: Enter `www.squeeze-ai.com`
4. **Copy DNS Records**: Railway will show you the DNS records

### Step 6: Configure DNS in Namecheap
1. **Login**: Go to namecheap.com and login
2. **Manage Domain**: Click "Manage" next to squeeze-ai.com
3. **Advanced DNS**: Click "Advanced DNS" tab
4. **Add Records**:
   ```
   Type: A Record
   Host: @
   Value: [Railway IP Address]
   TTL: 30 min

   Type: CNAME Record
   Host: www
   Value: [Railway domain].railway.app
   TTL: 30 min
   ```

### Step 7: Wait for DNS Propagation
- **Time**: 2-24 hours (usually 2-4 hours)
- **Check**: Use [dnschecker.org](https://dnschecker.org) to monitor progress
- **Test**: Try accessing squeeze-ai.com

## ⚡ Even Faster Alternative: Streamlit Community Cloud

### Step 1: Deploy to Streamlit Cloud
1. **Go to**: [share.streamlit.io](https://share.streamlit.io)
2. **Sign up**: Use GitHub account
3. **New App**: Click "New app"
4. **Select Repo**: Choose your squeeze-ai repository
5. **Deploy**: Click "Deploy!"

### Step 2: Get Your Streamlit URL
- Copy the URL (e.g., `https://your-app.streamlit.app`)
- **Test it**: Verify your app works

### Step 3: Use Cloudflare for Custom Domain
1. **Sign up**: Go to [cloudflare.com](https://cloudflare.com)
2. **Add Site**: Add squeeze-ai.com
3. **Change Nameservers**: Update nameservers in Namecheap
4. **Page Rules**: Redirect squeeze-ai.com to your Streamlit app

## 🎯 Recommended: Railway + Custom Domain

**Why Railway?**
- ✅ Fastest deployment (15 minutes)
- ✅ Automatic SSL certificates
- ✅ Custom domain support
- ✅ Environment variables
- ✅ Stripe webhook compatible
- ✅ Only ~$5/month

**Total Time**: ~2-4 hours (including DNS propagation)

## 🔧 After Deployment

1. **Test Everything**:
   - Visit https://squeeze-ai.com
   - Test user login/registration
   - Test admin panel: https://squeeze-ai.com/admin.py
   - Verify all features work

2. **Update Stripe**:
   - Add your domain to Stripe settings
   - Update webhook URLs to https://squeeze-ai.com/webhooks
   - Test payment processing

3. **Monitor**:
   - Check Railway logs for any errors
   - Monitor uptime and performance
   - Set up alerts if needed

## 📞 Need Help?

If you encounter issues:
1. Check Railway logs for errors
2. Verify all environment variables are set
3. Test DNS propagation
4. Ensure Stripe keys are correct

Your app will be live at **https://squeeze-ai.com** once DNS propagates!