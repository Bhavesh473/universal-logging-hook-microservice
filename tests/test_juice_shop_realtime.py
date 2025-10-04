"""Real-time monitoring of Juice Shop activity"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger
import time

logger = UniversalLogger("http://localhost:9880")

print("\n" + "="*70)
print("JUICE SHOP REAL-TIME ACTIVITY MONITOR")
print("="*70)
print("\nMonitoring started. Perform actions in Juice Shop...")
print("Press Ctrl+C to stop\n")

# Monitor different types of activities
activities = [
    ("User registration", {"email": "your_email@example.com"}),
    ("User login successful", {"email": "your_email@example.com"}),
    ("Product viewed", {"product": "Apple Juice", "category": "Drinks"}),
    ("Item added to basket", {"product": "Apple Juice", "price": 1.99}),
    ("Checkout attempted", {"items": 3, "total": 15.99}),
]

for activity, metadata in activities:
    logger.log("INFO", activity, "juice-shop", metadata)
    print(f"✓ Logged: {activity}")
    time.sleep(2)

print("\n" + "="*70)
print("Check Fluentd logs: docker logs universal-logging-fluentd --tail 10")
print("="*70 + "\n") 