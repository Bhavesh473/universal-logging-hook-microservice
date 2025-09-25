# src/integration/log_forwarder.py

import time
from datetime import datetime
from client_libs.python.universal_logger import UniversalLogger  # Assuming this is the path

def forward_logs(log_file_path, api_url, auth_token=None, interval=0.1):
    """
    Continuously reads a log file and forwards new lines to the logging microservice API.
    
    Args:
        log_file_path (str): Path to the log file to monitor.
        api_url (str): The base URL of the logging microservice API.
        auth_token (str, optional): Authentication token for API requests.
        interval (float, optional): Time to sleep between checks (seconds).
    
    Raises:
        FileNotFoundError: If the log file does not exist.
        Exception: If the API request fails.
    """
    logger = UniversalLogger(api_url, auth_token)
    
    try:
        with open(log_file_path, 'r') as file:
            file.seek(0, 2)  # Move to the end of the file
            while True:
                line = file.readline()
                if line:
                    payload = {
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'level': 'INFO',
                        'message': line.strip(),
                        'source': 'legacy_forwarder',
                        'metadata': {'file': log_file_path}
                    }
                    logger.log(payload['level'], payload['message'], payload['source'], payload['metadata'])
                time.sleep(interval)
    except FileNotFoundError:
        print(f"Log file not found: {log_file_path}")
    except Exception as e:
        print(f"Error forwarding logs: {e}")

# Example usage (uncomment to test locally)
# if __name__ == "__main__":
#     forward_logs('/var/log/app.log', 'http://localhost:8000')