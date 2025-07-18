# 🚀 Deploy to Render (Railway Alternative)

Railway has persistent Streamlit environment conflicts. **Render** is much more reliable for Streamlit apps.

## Quick Steps

### 1. Create Account
- Go to [render.com](https://render.com)
- Sign up with GitHub

### 2. Create Web Service
- Click "New +" → "Web Service"
- Connect: `mlbant/squeeze-ai`
- Name: `squeeze-ai`
- Environment: `Python 3`

### 3. Configuration
**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### 4. Environment Variables
Copy values from `KEEP_THIS_LOCAL_ONLY.txt`:
- STRIPE_SECRET_KEY
- STRIPE_PUBLISHABLE_KEY  
- ADMIN_USERNAME
- ADMIN_PASSWORD
- SECRET_KEY
- SENDER_EMAIL
- SENDER_APP_PASSWORD
- XAI_API_KEY

### 5. Deploy & Test
1. Click "Create Web Service"
2. Wait 5-10 minutes
3. Test your Render URL

### 6. Custom Domain
1. Settings → Custom Domains
2. Add: `squeeze-ai.com`
3. Update Namecheap DNS with Render's instructions

## Why Render Works Better
✅ No environment variable conflicts  
✅ Free SSL certificates  
✅ Custom domain support  
✅ Streamlit optimized  
✅ Production ready