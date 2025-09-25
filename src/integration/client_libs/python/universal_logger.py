# src/integration/client_libs/python/universal_logger.py

import requests
from datetime import datetime

class UniversalLogger:
    """
    A Python client for sending logs to the Universal Logging Microservice API.
    
    Args:
        api_url (str): The base URL of the logging microservice API.
        auth_token (str, optional): Authentication token for API requests.
    """
    
    def __init__(self, api_url, auth_token=None):
        self.api_url = api_url
        self.headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
    
    def log(self, level, message, source, metadata=None):
        """
        Send a log entry to the microservice API.
        
        Args:
            level (str): The log level (e.g., 'INFO', 'ERROR').
            message (str): The log message content.
            source (str): The source of the log (e.g., app name).
            metadata (dict, optional): Additional metadata for the log.
        
        Returns:
            dict: The API response data.
        
        Raises:
            Exception: If the API request fails.
        """
        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'message': message,
            'source': source,
            'metadata': metadata or {}
        }
        
        try:
            response = requests.post(
                f'{self.api_url}/logs',
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send log: {str(e)}")

# Example usage (uncomment to test locally)
# if __name__ == "__main__":
#     logger = UniversalLogger('http://localhost:8000')
#     logger.log('INFO', 'Test log', 'my_app', {'key': 'value'}) 