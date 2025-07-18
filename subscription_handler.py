import os
import time
import tempfile

class SubscriptionHandler:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.activation_file = os.path.join(self.temp_dir, 'squeeze_ai_subscription_activation.txt')
    
    def mark_subscription_pending(self):
        """Mark that a subscription activation is pending"""
        with open(self.activation_file, 'w') as f:
            f.write(f"{time.time()}")
    
    def check_and_activate_subscription(self):
        """Check if subscription activation is pending and return True if found"""
        if os.path.exists(self.activation_file):
            try:
                with open(self.activation_file, 'r') as f:
                    activation_time = float(f.read().strip())
                
                # Check if activation is recent (within 5 minutes)
                if time.time() - activation_time < 300:
                    # Remove the activation file
                    os.remove(self.activation_file)
                    return True
                else:
                    # Clean up old activation file
                    os.remove(self.activation_file)
            except (ValueError, OSError):
                # Clean up invalid activation file
                try:
                    os.remove(self.activation_file)
                except:
                    pass
        return False
    
    def cleanup_old_activations(self):
        """Clean up old activation files"""
        try:
            if os.path.exists(self.activation_file):
                os.remove(self.activation_file)
        except:
            pass