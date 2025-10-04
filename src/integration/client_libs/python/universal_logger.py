import requests
from datetime import datetime
import socket
import os

class UniversalLogger:
    """Universal Logger Client - Sends logs to Fluentd"""
    
    def __init__(self, fluentd_url="http://localhost:9880", auth_token=None):
        self.fluentd_url = fluentd_url
        self.auth_token = auth_token
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()
    
    def log(self, level, message, source, metadata=None):
        """Send log to Fluentd"""
        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'message': message,
            'source': source,
            'metadata': metadata or {},
            'hostname': self.hostname,
            'process_id': self.process_id
        }
        
        try:
            response = requests.post(
                self.fluentd_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✓ Log sent: {level} - {message}")
                return True
            else:
                print(f"✗ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            print(f"[FALLBACK] {level}: {message}")
            return False 