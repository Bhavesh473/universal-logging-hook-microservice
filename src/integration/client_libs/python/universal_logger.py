import requests
from datetime import datetime
import socket
import os
import uuid
import psutil

try:
    from pytz import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc

class UniversalLogger:
    """Universal Logger with Metrics and Correlation"""
    
    def __init__(self, fluentd_url="http://localhost:9880", auth_token=None, service_name=None):
        self.fluentd_url = fluentd_url
        self.auth_token = auth_token
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()
        
        # Generate unique session ID for correlation
        self.session_id = str(uuid.uuid4())
        
        # Store service name
        self.service_name = service_name or "unknown-service"
        
        # Track log sequence for this session
        self.log_sequence = 0
    
    def _ensure_utc_timestamp(self, timestamp=None):
        """Ensure timestamp is in UTC format"""
        if timestamp is None:
            return datetime.now(UTC).isoformat()
        
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC).isoformat()
            except Exception:
                return datetime.now(UTC).isoformat()
        
        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            return timestamp.astimezone(UTC).isoformat()
        
        return datetime.now(UTC).isoformat()
    
    def _get_system_metrics(self):
        """Collect system metrics"""
        try:
            process = psutil.Process(self.process_id)
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_usage_mb": process.memory_info().rss / (1024 * 1024),
                "memory_percent": process.memory_percent(),
                "disk_usage_percent": psutil.disk_usage('/').percent
            }
        except Exception as e:
            return {"metrics_error": str(e)}
    
    def log(self, level, message, source, metadata=None, request_id=None):
        """
        Send enriched log to Fluentd
        
        Args:
            level: Log level (INFO, ERROR, etc.)
            message: Log message
            source: Source of log (app name)
            metadata: Additional metadata dict
            request_id: Optional request ID for correlation
        """
        if metadata is None:
            metadata = {}
        
        # Increment sequence
        self.log_sequence += 1
        
        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Ensure UTC timestamp
        timestamp = self._ensure_utc_timestamp(metadata.get('timestamp'))
        
        # Get system metrics
        metrics = self._get_system_metrics()
        
        # Build enriched payload
        payload = {
            'timestamp': timestamp,
            'level': level.upper(),
            'message': message,
            'source': source,
            
            # Correlation fields
            'session_id': self.session_id,
            'request_id': request_id,
            'sequence': self.log_sequence,
            
            # System info
            'hostname': self.hostname,
            'process_id': self.process_id,
            'service_name': self.service_name,
            
            # Metrics
            'metrics': metrics,
            
            # User metadata
            'metadata': metadata
        }
        
        try:
            response = requests.post(
                self.fluentd_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✓ Log sent: {level} - {message} [Session: {self.session_id[:8]}...]")
                return True
            else:
                print(f"✗ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            print(f"[FALLBACK] {level}: {message}")
            return False
    
    def log_with_trace(self, level, message, source, trace_data=None, metadata=None):
        """
        Log with distributed tracing context
        
        Args:
            trace_data: Dict with 'trace_id', 'span_id', 'parent_span_id'
        """
        if metadata is None:
            metadata = {}
        
        if trace_data:
            metadata['trace'] = trace_data
        
        return self.log(level, message, source, metadata)