# tests/view_juice_shop_logs.py
import subprocess
import time

print("\n" + "="*70)
print("JUICE SHOP LOGS VIEWER")
print("="*70 + "\n")

while True:
    subprocess.run(["docker", "logs", "--tail", "15", "universal-logging-fluentd"])
    print("\n" + "="*70)
    print("Refreshing in 5 seconds... (Ctrl+C to stop)")
    print("="*70 + "\n")
    time.sleep(5) 