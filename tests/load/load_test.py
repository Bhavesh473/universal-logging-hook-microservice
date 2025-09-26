# Placeholder for performance testing (use locust; add locust to requirements.txt if needed)
from locust import HttpUser, task, between

class LoggingUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def post_log(self):
        self.client.post("/logs", json={"level": "info", "message": "load test", "source": "app"}, headers={"X-API-KEY": "your_secret_key"})

# Run with: locust -f tests/load/load_test.py --host=http://localhost:8000
