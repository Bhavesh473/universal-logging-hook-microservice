# tests/test_juice_shop_security.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger
import time

logger = UniversalLogger("http://localhost:9880")

print("\nTesting Security Event Logging...\n")

# Log security events
security_events = [
    ("SQL Injection attempt", "ERROR", {"payload": "' OR 1=1--", "endpoint": "/rest/products/search"}),
    ("XSS attempt detected", "WARN", {"payload": "<script>alert('XSS')</script>", "blocked": True}),
    ("Brute force login", "WARN", {"attempts": 5, "username": "admin"}),
    ("Admin panel access attempt", "ERROR", {"unauthorized": True, "ip": "192.168.1.100"}),
]

for event, level, metadata in security_events:
    logger.log(level, event, "juice-shop-security", metadata)
    print(f"✓ Logged: {level} - {event}")
    time.sleep(1)

print("\nSecurity events logged successfully!") 