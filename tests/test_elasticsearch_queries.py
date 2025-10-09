import requests
import json

ES_URL = "http://localhost:9200"

def search_by_level(level):
    query = {"query": {"match": {"level": level}}}
    response = requests.post(f"{ES_URL}/universal-logs-*/_search", json=query, headers={"Content-Type": "application/json"})
    data = response.json()
    count = data['hits']['total']['value']
    print(f"✓ Found {count} logs with level '{level}'")

def search_by_source(source):
    query = {"query": {"match": {"source": source}}}
    response = requests.post(f"{ES_URL}/universal-logs-*/_search", json=query, headers={"Content-Type": "application/json"})
    data = response.json()
    count = data['hits']['total']['value']
    print(f"✓ Found {count} logs from source '{source}'")

def get_stats():
    try:
        response = requests.get(f"{ES_URL}/universal-logs-*/_stats")
        data = response.json()
        if '_all' in data and 'total' in data['_all'] and 'docs' in data['_all']['total']:
            doc_count = data['_all']['total']['docs']['count']
            total_size = data['_all']['total']['store']['size_in_bytes'] / 1024
            print(f"\nStatistics: Documents {doc_count}, Size {total_size:.2f} KB")
        else:
            print("\nStatistics: No indices yet")
    except Exception as e:
        print(f"\nStatistics error: {e}")

if __name__ == "__main__":
    print("\n=== QUERY TESTS ===")
    search_by_level("INFO")
    search_by_level("ERROR")
    search_by_source("es-test")
    search_by_source("juice-shop")
    get_stats()
    print("=== COMPLETE ===") 