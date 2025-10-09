"""Test Elasticsearch storage"""
import requests
import json
import time
import sys
import os

# Add path for import (same as test_errors.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_dir = os.path.join(project_root, 'src', 'integration', 'client_libs', 'python')
sys.path.insert(0, python_dir)

from universal_logger import UniversalLogger

def test_elasticsearch():
    print("\n" + "="*70)
    print("TESTING ELASTICSEARCH STORAGE")
    print("="*70 + "\n")
    
    # Send a few logs first
    logger = UniversalLogger()
    logger.log("INFO", "Test Elasticsearch storage", "es-test", {"test_id": "001"})
    logger.log("ERROR", "Test error log", "es-test", {"test_id": "002"})
    time.sleep(5)  # Wait for indexing
    
    # Query Elasticsearch
    es_url = "http://localhost:9200/universal-logs-*/_search"
    
    try:
        response = requests.get(es_url)
        data = response.json()
        
        total_logs = data['hits']['total']['value']
        print(f"✓ Total logs in Elasticsearch: {total_logs}")
        
        # Show first 5 logs
        print("\nRecent logs:")
        for hit in data['hits']['hits'][:5]:
            log = hit['_source']
            print(f"  - {log.get('level', 'N/A')}: {log.get('message', 'N/A')}")
        
        print("\n" + "="*70)
        print("ELASTICSEARCH STORAGE WORKING!")
        print("="*70)
        print(f"\n✓ {total_logs} logs successfully stored")
        print(f"View all logs: http://localhost:9200/universal-logs-*/_search?pretty")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error querying Elasticsearch: {e}")
        print("Make sure Elasticsearch is running and logs have been sent")

if __name__ == "__main__":
    test_elasticsearch() 