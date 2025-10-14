"""Test enriched logging with metrics and correlation"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger
import time
import uuid

def test_enriched_logging():
    print("\n" + "="*70)
    print("TESTING ENRICHED LOGGING")
    print("="*70 + "\n")
    
    # Create logger with service name
    logger = UniversalLogger(
        "http://localhost:9880",
        service_name="enriched-test-service"
    )
    
    print(f"📋 Session ID: {logger.session_id}")
    print(f"🖥️  Hostname: {logger.hostname}")
    print(f"🔢 Process ID: {logger.process_id}\n")
    
    # Test 1: Basic enriched log
    print("Test 1: Basic enriched log with metrics")
    logger.log("INFO", "Service started", "enriched-test", {
        "version": "1.0.0",
        "environment": "production"
    })
    time.sleep(0.5)
    
    # Test 2: Simulated request flow with same request_id
    request_id = str(uuid.uuid4())
    print(f"\nTest 2: Request flow (Request ID: {request_id[:8]}...)")
    
    logger.log("INFO", "Request received", "enriched-test", {
        "endpoint": "/api/users",
        "method": "GET"
    }, request_id=request_id)
    time.sleep(0.3)
    
    logger.log("DEBUG", "Database query executed", "enriched-test", {
        "query_time_ms": 45,
        "rows_returned": 10
    }, request_id=request_id)
    time.sleep(0.3)
    
    logger.log("INFO", "Response sent", "enriched-test", {
        "status_code": 200,
        "response_time_ms": 78
    }, request_id=request_id)
    
    # Test 3: Error with correlation
    print("\nTest 3: Error with correlation")
    error_request_id = str(uuid.uuid4())
    
    logger.log("ERROR", "Database connection failed", "enriched-test", {
        "error_code": "DB_001",
        "retry_attempt": 1
    }, request_id=error_request_id)
    time.sleep(0.3)
    
    logger.log("WARN", "Retrying connection", "enriched-test", {
        "retry_attempt": 2
    }, request_id=error_request_id)
    
    # Test 4: Distributed tracing
    print("\nTest 4: Distributed tracing")
    trace_data = {
        "trace_id": str(uuid.uuid4()),
        "span_id": str(uuid.uuid4()),
        "parent_span_id": None
    }
    
    logger.log_with_trace("INFO", "Microservice A called", "service-a", trace_data, {
        "operation": "fetch_user"
    })
    
    print("\n" + "="*70)
    print("ENRICHED LOGGING TEST COMPLETED!")
    print("="*70)
    print("\nFeatures demonstrated:")
    print("  ✓ Session ID correlation")
    print("  ✓ Request ID tracking")
    print("  ✓ System metrics (CPU, Memory)")
    print("  ✓ Sequence numbering")
    print("  ✓ Distributed tracing")
    print("\nView logs: docker logs universal-logging-fluentd --tail 30")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_enriched_logging()