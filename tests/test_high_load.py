import sys
import os
import time
import random

# Add path for import (same as test_errors.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_dir = os.path.join(project_root, 'src', 'integration', 'client_libs', 'python')
sys.path.insert(0, python_dir)

from universal_logger import UniversalLogger

# Optional: Monitor memory (install: pip install psutil)
try:
    import psutil
    def get_memory_usage():
        return psutil.Process().memory_info().rss / 1024 / 1024  # MB
except ImportError:
    def get_memory_usage():
        return "psutil not installed"

logger = UniversalLogger(rate_limit_calls=500, rate_limit_period=60)  # Higher limit for test

def generate_fake_logs(count=10000, batch_size=1000):
    """Generate fake logs like Juice Shop events"""
    all_logs = []
    for i in range(count):
        metadata = {
            'user_id': f'user_{random.randint(1, 100)}',
            'action': random.choice(['login', 'sql_injection', 'xss_attempt', 'purchase']),
            'ip': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}'
        }
        all_logs.append(('INFO', f'Fake event {i}', 'juice-shop-test', metadata))
    return all_logs

def send_logs_in_batches(logs, batch_size=1000):
    """Stream logs in batches to avoid memory spikes"""
    total_sent = 0
    start_memory = get_memory_usage()
    print(f"Start memory: {start_memory} MB")
    
    for batch_start in range(0, len(logs), batch_size):
        batch = logs[batch_start:batch_start + batch_size]
        print(f"Processing batch {batch_start//batch_size + 1} ({len(batch)} logs)...")
        
        batch_success = 0
        for level, message, source, metadata in batch:
            success = logger.log(level, message, source, metadata)
            if success:
                batch_success += 1
        
        print(f"Batch sent: {batch_success}/{len(batch)}")
        total_sent += batch_success
        
        # Clear batch from memory
        del batch
        # GC hint (optional)
        import gc
        gc.collect()
        
        # Check memory after batch
        current_memory = get_memory_usage()
        print(f"Memory after batch: {current_memory} MB (delta: {current_memory - start_memory:.1f} MB)")
        time.sleep(0.1)  # Brief pause to simulate real load
    
    end_memory = get_memory_usage()
    print(f"\nTotal sent: {total_sent}/{len(logs)} | Final memory: {end_memory} MB (net delta: {end_memory - start_memory:.1f} MB)")

if __name__ == "__main__":
    print("=== Testing High-Load Batching (10k Logs) ===")
    logs = generate_fake_logs(10000, 1000)  # Generate all at once (for demo; in prod, stream from file)
    send_logs_in_batches(logs, batch_size=1000) 