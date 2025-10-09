import sys
import os

# Debug: Print current working directory and script path
print(f"Current dir: {os.getcwd()}")
print(f"Script path: {os.path.abspath(__file__)}")

# Calculate path to the python/ folder: from tests/ -> root -> src/integration/client_libs/python/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Up to root from tests/
python_dir = os.path.join(project_root, 'src', 'integration', 'client_libs', 'python')
print(f"Adding to path: {python_dir}")

# Add the python/ directory to sys.path
if os.path.exists(python_dir):
    sys.path.insert(0, python_dir)
    print("✓ python/ directory found and added to path.")
else:
    print("✗ python/ directory not found. Check path: src/integration/client_libs/python/")

# Now try import
try:
    from universal_logger import UniversalLogger
    print("✓ Import successful!")
except ModuleNotFoundError as e:
    print(f"✗ Import failed: {e}")
    # Fallback: Direct load the .py file
    logger_file = os.path.join(python_dir, 'universal_logger.py')
    if os.path.exists(logger_file):
        print(f"Found file: {logger_file}. Loading directly...")
        import importlib.util
        spec = importlib.util.spec_from_file_location("universal_logger", logger_file)
        universal_logger = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(universal_logger)
        UniversalLogger = universal_logger.UniversalLogger
        print("✓ Direct load successful!")
    else:
        print("✗ Logger file not found. Check file name/path.")
        sys.exit(1)

# Rest of the test
logger = UniversalLogger()

# Test 1: Simulate network error (stop Fluentd temporarily)
print("\n=== Testing Network Error with Retries ===")
# IMPORTANT: In another PowerShell terminal, run: docker-compose down
# Then run this script – should retry 3x and fallback
success = logger.log("ERROR", "Simulated network failure", "error-test")
print(f"Network test result: {success}")  # Should be False with fallback

# Restart Fluentd: In the other terminal, run: docker-compose up -d
# Wait 5s, then continue...

# Test 2: Rate limiting (send many logs fast)
print("\n=== Testing Rate Limiting ===")
successes = 0
for i in range(150):  # >100 to trigger limit
    success = logger.log("INFO", f"High volume log {i}", "rate-test")
    if success:
        successes += 1
    if i == 10:  # Pause briefly to simulate real bursts
        import time
        time.sleep(1)
print(f"Rate limited: Sent {successes} out of 150")

# Check errors.log (in project root)
print("\n=== Errors Logged ===")
errors_file = os.path.join(project_root, 'errors.log')
try:
    with open(errors_file, 'r') as f:
        print(f.read())
except FileNotFoundError:
    print("No errors.log yet – normal if no failures occurred.") 