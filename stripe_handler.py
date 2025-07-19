import stripe
import streamlit as st
from database import UserDatabase
import os
import dotenv
dotenv.load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeHandler:
    def __init__(self):
        self.db = UserDatabase()
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    def _get_domain_url(self):
        # Get the appropriate domain URL for redirects
        if os.getenv('ENVIRONMENT') == 'production':
            return 'https://squeeze-ai.com'
        elif os.getenv('RENDER'):
            return 'https://squeeze-ai.onrender.com'
        else:
            return 'http://localhost:8501'
    
    def create_checkout_session(self, user_id, email, success_url, cancel_url):
        """Create Stripe checkout session"""
        self.last_error = None  # Store last error for debugging
        try:
            # Debug: Log the API key status
            api_key = os.getenv('STRIPE_SECRET_KEY')
            print(f"DEBUG: API key exists: {bool(api_key)}")
            print(f"DEBUG: API key starts with sk_: {api_key.startswith('sk_') if api_key else False}")
            print(f"DEBUG: Creating session for user {user_id}, email {email}")
            print(f"DEBUG: Success URL: {success_url}")
            print(f"DEBUG: Cancel URL: {cancel_url}")
            
            if not api_key:
                print("ERROR: STRIPE_SECRET_KEY not found in environment")
                return None
            # Create or get customer
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(
                    email=email,
                    metadata={'user_id': str(user_id)}
                )
            
            # Create checkout session with 14-day free trial
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Squeeze Ai Pro',
                            'description': 'Unlimited squeeze analysis, real-time alerts, and premium features. 14-day free trial!',
                            'images': ['https://squeeze-ai.com/logo.png'],
                        },
                        'unit_amount': 2900,  # $29.00
                        'recurring': {
                            'interval': 'month',
                            'interval_count': 1,
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                subscription_data={
                    'trial_period_days': 14,  # 14-day free trial
                    'metadata': {
                        'user_id': str(user_id)
                    }
                },
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id)
                }
            )
            
            return session
            
        except stripe.error.StripeError as e:
            error_msg = f"Stripe error: {str(e)}"
            self.last_error = error_msg
            print(error_msg)
            # Also write to a file that can be checked
            try:
                with open('stripe_errors.log', 'a') as f:
                    from datetime import datetime
                    f.write(f"{datetime.now()}: {error_msg}\n")
            except:
                pass
            return None
        except Exception as e:
            error_msg = f"General error in create_checkout_session: {str(e)}"
            self.last_error = error_msg
            print(error_msg)
            try:
                with open('stripe_errors.log', 'a') as f:
                    from datetime import datetime
                    f.write(f"{datetime.now()}: {error_msg}\n")
            except:
                pass
            return None
    
    def create_customer_portal_session(self, user_id):
        """Create customer portal session for subscription management"""
        try:
            # Get user's Stripe customer ID
            sub = self.db.get_user_subscription(user_id)
            if not sub or not sub.get('stripe_customer_id'):
                return None
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=sub['stripe_customer_id'],
                return_url=self._get_domain_url()
            )
            
            return session
            
        except stripe.error.StripeError as e:
            print(f"Portal error: {str(e)}")
            return None
    
    def handle_checkout_success(self, session_id):
        """Handle successful checkout"""
        try:
            # Retrieve session
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Get subscription
            subscription = stripe.Subscription.retrieve(session.subscription)
            
            # Update database
            user_id = int(session.metadata.get('user_id'))
            self.db.update_subscription(
                user_id=user_id,
                stripe_customer_id=session.customer,
                stripe_subscription_id=subscription.id,
                plan_type='pro'
            )
            
            return True
            
        except Exception as e:
            print(f"Error processing payment: {str(e)}")
            return False
    
    def cancel_subscription(self, user_id):
        """Cancel user's subscription"""
        try:
            sub = self.db.get_user_subscription(user_id)
            if sub and sub.get('stripe_subscription_id'):
                # Cancel at period end
                stripe.Subscription.modify(
                    sub['stripe_subscription_id'],
                    cancel_at_period_end=True
                )
                return True
            return False
        except Exception as e:
            print(f"Error canceling subscription: {str(e)}")
            return False
    
    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhooks with proper security validation"""
        if not self.webhook_secret:
            print("ERROR: Webhook secret not configured")
            return False
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            # Log webhook event for security monitoring
            self._log_webhook_event(event['type'], event['id'])
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                return self.handle_checkout_success(session['id'])
            
            elif event['type'] == 'customer.subscription.updated':
                subscription = event['data']['object']
                return self._update_subscription_status(subscription)
            
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                return self._handle_subscription_cancelled(subscription)
            
            elif event['type'] == 'invoice.payment_failed':
                invoice = event['data']['object']
                return self._handle_payment_failed(invoice)
            
            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                return self._handle_payment_succeeded(invoice)
            
            else:
                print(f"Unhandled webhook event type: {event['type']}")
                return True  # Return True for unhandled but valid events
            
        except stripe.error.SignatureVerificationError as e:
            print(f"Webhook signature verification failed: {str(e)}")
            return False
        except ValueError as e:
            print(f"Invalid webhook payload: {str(e)}")
            return False
        except Exception as e:
            print(f"Webhook processing error: {str(e)}")
            return False
    
    def _log_webhook_event(self, event_type, event_id):
        """Log webhook events for security monitoring"""
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('squeeze_ai.db')
        cursor = conn.cursor()
        
        # Create webhook logs table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            INSERT INTO webhook_logs (event_type, event_id)
            VALUES (?, ?)
        ''', (event_type, event_id))
        
        conn.commit()
        conn.close()
    
    def _update_subscription_status(self, subscription):
        """Update subscription status from webhook"""
        try:
            conn = sqlite3.connect('squeeze_ai.db')
            cursor = conn.cursor()
            
            # Find user by Stripe customer ID
            cursor.execute('''
                SELECT user_id FROM subscriptions 
                WHERE stripe_subscription_id = ?
            ''', (subscription['id'],))
            
            result = cursor.fetchone()
            if result:
                user_id = result[0]
                
                # Update subscription status
                cursor.execute('''
                    UPDATE subscriptions 
                    SET status = ?, expires_at = datetime('now', '+1 month')
                    WHERE user_id = ?
                ''', (subscription['status'], user_id))
                
                conn.commit()
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating subscription status: {str(e)}")
            return False
    
    def _handle_subscription_cancelled(self, subscription):
        """Handle cancelled subscription"""
        try:
            conn = sqlite3.connect('squeeze_ai.db')
            cursor = conn.cursor()
            
            # Find user and update to free plan
            cursor.execute('''
                UPDATE subscriptions 
                SET status = 'cancelled', plan_type = 'free'
                WHERE stripe_subscription_id = ?
            ''', (subscription['id'],))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error handling subscription cancellation: {str(e)}")
            return False
    
    def _handle_payment_failed(self, invoice):
        """Handle failed payment"""
        try:
            # Log payment failure
            print(f"Payment failed for invoice: {invoice['id']}")
            
            # Here you would typically:
            # 1. Send email notification to user
            # 2. Update subscription status
            # 3. Log the event for follow-up
            
            return True
        except Exception as e:
            print(f"Error handling payment failure: {str(e)}")
            return False
    
    def _handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        try:
            # Log successful payment
            print(f"Payment succeeded for invoice: {invoice['id']}")
            
            # Update subscription status if needed
            if invoice.get('subscription'):
                subscription = stripe.Subscription.retrieve(invoice['subscription'])
                self._update_subscription_status(subscription)
            
            return True
        except Exception as e:
            print(f"Error handling payment success: {str(e)}")
            return False
