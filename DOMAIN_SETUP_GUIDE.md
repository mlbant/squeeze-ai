# 🌐 Domain Setup Guide for squeeze-ai.com

## Step 1: Push to GitHub

1. **Create a GitHub repository:**
   - Go to https://github.com/new
   - Repository name: `squeeze-ai`
   - Make it **Private** (recommended for production apps)
   - Don't initialize with README (we already have one)

2. **Add GitHub remote and push:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/squeeze-ai.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io/
   - Sign in with your GitHub account

2. **Deploy your app:**
   - Click "New app"
   - Select your GitHub repository: `squeeze-ai`
   - Main file path: `app.py`
   - Click "Deploy!"

3. **Add Environment Variables:**
   In Streamlit Cloud settings, add these secrets:
   ```
   STRIPE_SECRET_KEY = "sk_live_51RkvPvGRjwgoUS3I..."
   STRIPE_PUBLISHABLE_KEY = "pk_live_51RkvPvGRjwgoUS3I..."
   SECRET_KEY = "your_generated_secret_key"
   ADMIN_USERNAME = "squeeze_admin"
   ADMIN_PASSWORD = "your_hashed_password"
   ```

## Step 3: Get Your Streamlit App URL

After deployment, you'll get a URL like:
`https://your-app-name-randomstring.streamlit.app`

## Step 4: Update DNS Records

Now update your DNS records in Namecheap:

### Current DNS Records (to be updated):
- **CNAME Record**: `www` → `parkingpage.namecheap.com` ❌ (Remove this)
- **URL Redirect**: `@` → `http://www.squeeze-ai.com/` ❌ (Remove this)

### New DNS Records (to add):
1. **CNAME Record**: 
   - Host: `www`
   - Value: `your-app-name-randomstring.streamlit.app`
   - TTL: `Automatic`

2. **CNAME Record**:
   - Host: `@` (or leave blank for root domain)
   - Value: `your-app-name-randomstring.streamlit.app`
   - TTL: `Automatic`

## Step 5: Configure Custom Domain in Streamlit

1. **In Streamlit Cloud settings:**
   - Go to your app settings
   - Find "Custom domain" section
   - Add: `squeeze-ai.com`
   - Add: `www.squeeze-ai.com`

## Step 6: SSL Certificate

Streamlit Cloud automatically provides SSL certificates for custom domains.

## Step 7: Test Your Domain

After DNS propagation (5-60 minutes):
- Visit: https://squeeze-ai.com
- Visit: https://www.squeeze-ai.com
- Both should redirect to your Squeeze AI app!

## 🚨 Important Notes

1. **DNS Propagation**: Changes can take 5-60 minutes to take effect globally
2. **SSL**: Streamlit handles SSL certificates automatically
3. **Environment Variables**: Make sure all your production secrets are added in Streamlit Cloud
4. **Database**: Your SQLite database will reset on each deployment (consider upgrading to PostgreSQL for production)

## 🎉 You're Live!

Once complete, your Squeeze AI app will be accessible at:
- https://squeeze-ai.com
- https://www.squeeze-ai.com

With full:
- ✅ Live Stripe payments ($29/month subscriptions)
- ✅ User authentication and registration
- ✅ Real-time stock squeeze analysis
- ✅ Admin panel at squeeze-ai.com/admin
- ✅ Professional UI/UX
- ✅ SSL security

## Alternative: Quick Custom Domain Setup

If you want to skip Streamlit's custom domain feature, you can:

1. **Use a CNAME record pointing to your Streamlit URL**
2. **Set up Cloudflare** (free) for:
   - Custom domain routing
   - Additional SSL/security
   - Better performance/caching

Would you like me to help with the Cloudflare setup instead?
