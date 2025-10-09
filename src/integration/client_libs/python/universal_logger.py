import requests
from datetime import datetime
import socket
import os
import logging  # For error logging
import time     # For custom rate limiting

try:
    from pytz import UTC
except ImportError:
    # Fallback if pytz not installed
    from datetime import timezone
    UTC = timezone.utc

class UniversalLogger:
    """Universal Logger Client - Sends logs to Fluentd with proper timestamp handling, error handling, and rate limiting"""
    
    def __init__(self, fluentd_url="http://localhost:9880", auth_token=None, rate_limit_calls=100, rate_limit_period=60):
        self.fluentd_url = fluentd_url
        self.auth_token = auth_token
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()
        
        # Custom rate limiter: max_calls per period (seconds), e.g., 100/min
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period
        self._call_times = []  # List of recent call timestamps
        
        # Setup error logging to file (creates errors.log if missing)
        logging.basicConfig(
            filename='errors.log',
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s - PID: %(process)d'
        )
        self.logger = logging.getLogger(__name__)
    
    def _rate_limited(self):
        """Custom rate limiter: Enforce max calls per period with sleep if exceeded"""
        now = time.time()
        # Remove old timestamps outside the window
        self._call_times = [t for t in self._call_times if now - t < self.rate_limit_period]
        
        if len(self._call_times) >= self.rate_limit_calls:
            # Too many recent calls – sleep until oldest expires
            sleep_time = self.rate_limit_period - (now - self._call_times[0])
            if sleep_time > 0:
                print(f"✗ Rate limited: Sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            # Recheck after sleep
            self._rate_limited()  # Recursive check (safe for short sleeps)
        else:
            # OK to proceed – add current time
            self._call_times.append(now)
    
    def _ensure_utc_timestamp(self, timestamp=None):
        """Ensure timestamp is a UTC datetime object, handling parsing and defaults"""
        if timestamp is None:
            # Create new UTC timestamp
            return datetime.now(UTC)
        
        # If timestamp is string, parse it
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # Convert to UTC if needed
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC)
            except ValueError as e:
                print(f"Invalid timestamp '{timestamp}': {e}. Using current UTC.")
                return datetime.now(UTC)
        
        # If timestamp is datetime object
        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            return timestamp.astimezone(UTC)
        
        # Fallback
        print(f"Invalid timestamp type '{type(timestamp)}'. Using current UTC.")
        return datetime.now(UTC)
    
    def log(self, level, message, source, metadata=None, max_retries=3):
        """Send log to Fluentd with standardized UTC timestamp, rate limiting, and retries"""
        if metadata is None:
            metadata = {}
        
        # Get UTC datetime object
        dt = self._ensure_utc_timestamp(metadata.get('timestamp'))
        
        # Standardize timestamp string in metadata
        metadata['timestamp'] = dt.isoformat()
        
        payload = {
            'time': dt.timestamp(),  # Unix float for Fluentd event time (avoids parsing issues)
            'level': level.upper(),
            'message': message,
            'source': source,
            'metadata': metadata,
            'hostname': self.hostname,
            'process_id': self.process_id
        }
        
        # Apply custom rate limiting
        try:
            self._rate_limited()
        except Exception as rate_error:
            self.logger.error(f"Rate limit error: {rate_error}")
            print(f"✗ Rate limited: {message}")
            return False
        
        # Retry loop for network/HTTP errors
        for attempt in range(max_retries):
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
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt < max_retries - 1:
                        print(f"⚠ Retry {attempt + 1}/{max_retries}: {error_msg}")
                    else:
                        self.logger.error(f"Failed after {max_retries} retries: {error_msg} | Payload: {payload}")
                        print(f"✗ Failed after retries: {error_msg}")
                        return False
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Network error: {e}"
                if attempt < max_retries - 1:
                    print(f"⚠ Retry {attempt + 1}/{max_retries}: {error_msg}")
                else:
                    self.logger.error(f"Network failed after {max_retries} retries: {error_msg} | Payload: {payload}")
                    print(f"✗ Network failed: {error_msg} | [FALLBACK] {level}: {message}")
                    return False
        
        return False  # Fallback if all retries fail 