# src/integration/auto_discovery.py

import docker
from datetime import datetime

def discover_containers(api_url, auth_token=None):
    """
    Detect running Docker containers and send discovery logs to the API.
    
    Args:
        api_url (str): The base URL of the logging microservice API.
        auth_token (str, optional): Authentication token for API requests.
    
    Returns:
        list: Names of discovered containers.
    """
    client = docker.from_client()
    headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
    
    try:
        containers = client.containers.list()
        for container in containers:
            container_id = container.id[:12]  # Shortened ID
            container_name = container.name
            logs = container.logs(tail=10).decode('utf-8')  # Get recent logs
            
            payload = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': 'INFO',
                'message': f'Discovered container: {container_name}',
                'source': 'auto_discovery',
                'metadata': {'container_id': container_id, 'logs_sample': logs}
            }
            
            # Mock API call (replace with actual request when API is ready)
            # import requests
            # response = requests.post(f'{api_url}/logs', json=payload, headers=headers)
            # if response.status_code != 200:
            #     print(f"Failed to log discovery for {container_name}: {response.text}")
            
            print(f"Discovered: {container_name} (ID: {container_id})")  # Placeholder output
        
        return [c.name for c in containers]
    
    except docker.errors.APIError as e:
        print(f"Docker API error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# Example usage (uncomment to test locally)
# if __name__ == "__main__":
#     discover_containers('http://localhost:8000')