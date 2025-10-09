"""Test improved timestamp parsing"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger
import time
from datetime import datetime, timezone

def test_timestamp_parsing():
    print("\n" + "="*70)
    print("TESTING TIMESTAMP PARSING")
    print("="*70 + "\n")
    
    logger = UniversalLogger("http://localhost:9880")
    
    # Test 1: No timestamp provided (should use current UTC)
    print("Test 1: Auto-generate UTC timestamp")
    logger.log("INFO", "Test without timestamp", "timestamp-test")
    time.sleep(0.5)
    
    # Test 2: Timestamp with timezone
    print("Test 2: Timestamp with timezone (+05:30)")
    logger.log("INFO", "Test with IST timezone", "timestamp-test", 
               {"timestamp": "2025-10-04T18:30:00+05:30"})
    time.sleep(0.5)
    
    # Test 3: Timestamp without timezone (should assume UTC)
    print("Test 3: Timestamp without timezone")
    logger.log("INFO", "Test without timezone info", "timestamp-test",
               {"timestamp": "2025-10-04T13:00:00"})
    time.sleep(0.5)
    
    # Test 4: Timestamp with 'Z' (UTC indicator)
    print("Test 4: Timestamp with Z (UTC)")
    logger.log("INFO", "Test with UTC Z marker", "timestamp-test",
               {"timestamp": "2025-10-04T13:00:00Z"})
    time.sleep(0.5)
    
    # Test 5: Invalid timestamp (should fallback to current time)
    print("Test 5: Invalid timestamp format")
    logger.log("INFO", "Test with invalid timestamp", "timestamp-test",
               {"timestamp": "invalid-time-format"})
    
    print("\n" + "="*70)
    print("TIMESTAMP PARSING TEST COMPLETED!")
    print("="*70)
    print("\nCheck logs:")
    print("  docker logs universal-logging-fluentd --tail 15")
    print("\nAll timestamps should be in UTC format")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_timestamp_parsing() 