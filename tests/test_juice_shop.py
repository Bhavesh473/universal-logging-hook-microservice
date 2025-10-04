"""Test Universal Logging with OWASP Juice Shop"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger
import time

def simulate_juice_shop_activity():
    print("\n" + "="*70)
    print("JUICE SHOP LOGGING SIMULATION")
    print("="*70 + "\n")
    
    # Create logger
    logger = UniversalLogger("http://localhost:9880")
    
    print("Simulating Juice Shop user activity...\n")
    
    # Simulate various Juice Shop events
    logger.log("INFO", "User visited homepage", "juice-shop", 
               {"url": "/", "ip": "192.168.1.100"})
    time.sleep(0.5)
    
    logger.log("INFO", "Product search performed", "juice-shop",
               {"search_term": "apple juice", "results": 5})
    time.sleep(0.5)
    
    logger.log("WARN", "Failed login attempt", "juice-shop",
               {"username": "admin", "attempts": 3})
    time.sleep(0.5)
    
    logger.log("ERROR", "SQL Injection detected", "juice-shop",
               {"payload": "' OR 1=1--", "blocked": True})
    time.sleep(0.5)
    
    logger.log("INFO", "Order placed successfully", "juice-shop",
               {"order_id": "ORD-12345", "amount": 29.99})
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETED!")
    print("="*70)
    print("\nView logs:")
    print("  docker logs universal-logging-fluentd --tail 20")
    print("="*70 + "\n")

if __name__ == "__main__":
    simulate_juice_shop_activity() 