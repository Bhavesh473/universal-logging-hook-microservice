"""Working test for Fluentd integration"""
import sys
import os
import time

# Add path to client library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger

def main():
    print("\n" + "="*70)
    print("TESTING UNIVERSAL LOGGING WITH FLUENTD")
    print("="*70 + "\n")
    
    # Create logger pointing to Fluentd
    logger = UniversalLogger("http://localhost:9880")
    
    print("Sending 5 test logs...\n")
    
    # Send test logs
    logger.log("INFO", "Application started successfully", "test-app")
    time.sleep(0.5)
    
    logger.log("DEBUG", "Debug information", "test-app", {"env": "dev"})
    time.sleep(0.5)
    
    logger.log("WARN", "High memory usage", "test-app", {"usage": "85%"})
    time.sleep(0.5)
    
    logger.log("ERROR", "Database connection failed", "test-app", {"retry": 3})
    time.sleep(0.5)
    
    logger.log("FATAL", "System crash", "test-app", {"code": "SYS001"})
    
    print("\n" + "="*70)
    print("TEST COMPLETED!")
    print("="*70)
    print("\nTo view logs:")
    print("  1. docker logs universal-logging-fluentd")
    print("  2. cat logs/events.log.*")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()   