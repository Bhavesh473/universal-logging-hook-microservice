"""Demo: Correlation across multiple services"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'integration', 'client_libs', 'python'))

from universal_logger import UniversalLogger
import time
import uuid

def simulate_microservices():
    print("\n" + "="*70)
    print("CORRELATION DEMO: Multi-Service Request Flow")
    print("="*70 + "\n")
    
    # Create loggers for different services
    api_gateway = UniversalLogger("http://localhost:9880", service_name="api-gateway")
    auth_service = UniversalLogger("http://localhost:9880", service_name="auth-service")
    user_service = UniversalLogger("http://localhost:9880", service_name="user-service")
    db_service = UniversalLogger("http://localhost:9880", service_name="database-service")
    
    # Shared request ID for correlation
    request_id = str(uuid.uuid4())
    
    print(f"🔗 Request ID: {request_id}")
    print(f"📊 Simulating user login flow across 4 services...\n")
    
    # Step 1: API Gateway receives request
    print("1️⃣  API Gateway: Request received")
    api_gateway.log("INFO", "POST /api/login received", "api-gateway", {
        "client_ip": "192.168.1.100",
        "user_agent": "Mozilla/5.0"
    }, request_id=request_id)
    time.sleep(0.3)
    
    # Step 2: API Gateway calls Auth Service
    print("2️⃣  API Gateway → Auth Service")
    api_gateway.log("DEBUG", "Forwarding to auth service", "api-gateway", {
        "target_service": "auth-service"
    }, request_id=request_id)
    time.sleep(0.2)
    
    # Step 3: Auth Service validates token
    print("3️⃣  Auth Service: Validating credentials")
    auth_service.log("INFO", "Validating user credentials", "auth-service", {
        "username": "user@example.com"
    }, request_id=request_id)
    time.sleep(0.3)
    
    # Step 4: Auth Service calls User Service
    print("4️⃣  Auth Service → User Service")
    auth_service.log("DEBUG", "Fetching user profile", "auth-service", {
        "target_service": "user-service"
    }, request_id=request_id)
    time.sleep(0.2)
    
    # Step 5: User Service queries database
    print("5️⃣  User Service → Database")
    user_service.log("DEBUG", "Querying user data", "user-service", {
        "query": "SELECT * FROM users WHERE email=?"
    }, request_id=request_id)
    time.sleep(0.2)
    
    # Step 6: Database executes query
    print("6️⃣  Database: Query executed")
    db_service.log("INFO", "Query executed successfully", "database-service", {
        "execution_time_ms": 23,
        "rows_affected": 1
    }, request_id=request_id)
    time.sleep(0.3)
    
    # Step 7: Response flows back
    print("7️⃣  User Service: User found")
    user_service.log("INFO", "User profile retrieved", "user-service", {
        "user_id": "12345"
    }, request_id=request_id)
    time.sleep(0.2)
    
    print("8️⃣  Auth Service: Token generated")
    auth_service.log("INFO", "JWT token generated", "auth-service", {
        "token_expiry": "24h"
    }, request_id=request_id)
    time.sleep(0.2)
    
    print("9️⃣  API Gateway: Response sent")
    api_gateway.log("INFO", "Login successful", "api-gateway", {
        "status_code": 200,
        "total_time_ms": 450
    }, request_id=request_id)
    
    print("\n" + "="*70)
    print("✅ CORRELATION DEMO COMPLETED!")
    print("="*70)
    print(f"\n🔍 All logs share request_id: {request_id[:16]}...")
    print("📊 This enables:")
    print("  • Tracing request flow across services")
    print("  • Identifying bottlenecks")
    print("  • Debugging distributed systems")
    print("\n💡 View correlated logs:")
    print(f"   docker logs universal-logging-fluentd --tail 50 | grep {request_id[:16]}")
    print("="*70 + "\n")

if __name__ == "__main__":
    simulate_microservices()