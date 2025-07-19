import streamlit as st
import os
from datetime import datetime

class Analytics:
    """Google Analytics and tracking implementation for Streamlit"""
    
    def __init__(self):
        # Use provided Google Analytics ID as fallback
        self.ga_tracking_id = os.getenv('GOOGLE_ANALYTICS_ID', 'G-CHHPMK0XWG')
        self.debug_mode = os.getenv('ENVIRONMENT', 'development') != 'production'
    
    def inject_google_analytics(self):
        """Inject Google Analytics 4 (gtag) tracking code"""
        if not self.ga_tracking_id:
            if self.debug_mode:
                st.warning("⚠️ Google Analytics ID not configured. Set GOOGLE_ANALYTICS_ID environment variable.")
            return
        
        # Google Analytics 4 tracking code (exact format from Google)
        ga_code = f"""
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={self.ga_tracking_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());

          gtag('config', '{self.ga_tracking_id}');
        </script>
        """
        
        # Inject the code into the page
        st.html(ga_code)
        
        if self.debug_mode:
            st.success(f"✅ Google Analytics loaded (ID: {self.ga_tracking_id})")
    
    def track_event(self, event_name, event_category="user_interaction", event_label="", value=0):
        """Track custom events"""
        if not self.ga_tracking_id:
            return
        
        # JavaScript code to track custom events
        event_code = f"""
        <script>
          if (typeof gtag !== 'undefined') {{
            gtag('event', '{event_name}', {{
              'event_category': '{event_category}',
              'event_label': '{event_label}',
              'value': {value}
            }});
          }}
        </script>
        """
        
        st.html(event_code)
        
        if self.debug_mode:
            st.info(f"📊 Event tracked: {event_name} - {event_category}")
    
    def track_page_view(self, page_title, page_path):
        """Track page views"""
        if not self.ga_tracking_id:
            return
        
        page_view_code = f"""
        <script>
          if (typeof gtag !== 'undefined') {{
            gtag('config', '{self.ga_tracking_id}', {{
              page_title: '{page_title}',
              page_path: '{page_path}'
            }});
          }}
        </script>
        """
        
        st.html(page_view_code)
    
    def track_conversion(self, conversion_name, transaction_id="", value=0, currency="USD"):
        """Track conversions (e.g., subscriptions, purchases)"""
        if not self.ga_tracking_id:
            return
        
        conversion_code = f"""
        <script>
          if (typeof gtag !== 'undefined') {{
            gtag('event', 'conversion', {{
              'send_to': '{self.ga_tracking_id}',
              'event_category': 'ecommerce',
              'event_label': '{conversion_name}',
              'transaction_id': '{transaction_id}',
              'value': {value},
              'currency': '{currency}'
            }});
          }}
        </script>
        """
        
        st.html(conversion_code)
        
        if self.debug_mode:
            st.success(f"💰 Conversion tracked: {conversion_name} - ${value}")

# Create global analytics instance
analytics = Analytics()