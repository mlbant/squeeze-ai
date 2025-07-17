# 🧪 Stripe Subscription Testing Guide

## ✅ Setup Complete

Your app is now configured for testing with Stripe test keys:
- ✅ **Test Secret Key**: `sk_test_51RkvPvGRjwgoUS3I...`
- ✅ **Test Publishable Key**: `pk_test_51RkvPvGRjwgoUS3I...`

## 🔄 Next Steps

### 1. Restart Your App
Since you updated the environment variables, restart your Streamlit app:
```bash
# Stop current app (Ctrl+C) then restart
streamlit run app.py
```

### 2. Test the Payment Flow

#### Step 1: Create a Test User
1. Go to your app
2. Sign up with a test email (e.g., `test@example.com`)
3. Log in with your test account

#### Step 2: Try to Upgrade to Pro
1. Go to "Top Squeezes" tab
2. Click "🚀 Scan Market"
3. Click "🔓 Unlock Pro Access - $29/month"
4. **OR** go to Settings tab and click "Upgrade to Pro - $29/month"

#### Step 3: Use Stripe Test Cards
When you reach the Stripe checkout page, use these **test card numbers**:

## 💳 Stripe Test Card Numbers

### ✅ Successful Payment Cards:
- **Visa**: `4242424242424242`
- **Visa (debit)**: `4000056655665556`
- **Mastercard**: `5555555555554444`
- **American Express**: `378282246310005`

### ❌ Declined Payment Cards (for testing failures):
- **Generic decline**: `4000000000000002`
- **Insufficient funds**: `4000000000009995`
- **Lost card**: `4000000000009987`

### 📝 Test Card Details:
- **Expiry Date**: Any future date (e.g., `12/25`)
- **CVC**: Any 3-digit number (e.g., `123`)
- **ZIP Code**: Any 5-digit number (e.g., `12345`)
- **Name**: Any name (e.g., `Test User`)

## 🧪 Testing Scenarios

### Test 1: Successful Subscription
1. Use card: `4242424242424242`
2. Complete the checkout
3. Verify you're redirected back to your app
4. Check that your subscription status shows "Pro"

### Test 2: Failed Payment
1. Use card: `4000000000000002`
2. Verify the payment fails gracefully
3. Check that you remain on Free tier

### Test 3: Subscription Management
1. After successful test subscription
2. Go to Settings → Cancel Subscription
3. Verify cancellation works

## 📊 Monitor Test Results

### In Your Stripe Dashboard:
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Make sure you're in **Test Mode** (toggle in top-left)
3. Check **Payments** section for test transactions
4. Check **Subscriptions** section for test subscriptions

### In Your App:
1. Check user's subscription status in Settings
2. Verify Pro features are unlocked after payment
3. Check that activity tracking works

## 🔍 What to Look For

### ✅ Success Indicators:
- Stripe checkout page loads properly
- Test payment processes successfully
- User is redirected back to your app
- Subscription status changes to "Pro"
- Pro features become available (all 5 stocks in scanner)

### ❌ Issues to Watch For:
- Stripe checkout doesn't load
- Payment processing errors
- Redirect issues after payment
- Subscription status doesn't update
- Pro features don't unlock

## 🚀 After Testing Successfully

Once everything works with test cards:

### Switch Back to Live Mode:
1. **Update .env** with live keys:
   ```bash
   STRIPE_SECRET_KEY=sk_live_51RkvPvGRjwgoUS3I...
   STRIPE_PUBLISHABLE_KEY=pk_live_51RkvPvGRjwgoUS3I...
   ```

2. **Restart your app**

3. **Switch Stripe Dashboard to Live Mode**

4. **Deploy to production**

## 🛠️ Troubleshooting

### If Checkout Doesn't Load:
- Check browser console for errors
- Verify Stripe keys are correct
- Ensure app was restarted after key changes

### If Payment Doesn't Process:
- Verify you're using test card numbers exactly as shown
- Check Stripe dashboard for error details
- Ensure you're in test mode

### If Redirect Fails:
- Check the success_url in your app code
- Verify domain matches your app's URL

## 📞 Need Help?

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Check your Stripe dashboard for transaction details
3. Verify all environment variables are loaded correctly

**Ready to test! Use the test cards above to simulate real subscription payments. 🧪💳**
