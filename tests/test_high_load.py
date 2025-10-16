import sys
import os
import time
import subprocess
import json
from datetime import datetime, timezone

# add python client lib to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_dir = os.path.join(project_root, "src", "integration", "client_libs", "python")
sys.path.insert(0, python_dir)

from universal_logger import UniversalLogger

# Configuration (tune these)
JUICE_CONTAINER = "juice-shop"
TAIL_LINES = 500                 # how many recent container log lines to fetch
BATCH_SIZE = 200                 # how many logs to send to UniversalLogger per batch
PAUSE_BETWEEN_BATCHES = 0.2      # seconds pause between batches
HIGHLOAD_EVENTS_THRESHOLD = 200  # if total events in window >= this -> highload
HIGHLOAD_ERROR_RATIO = 0.10      # if (WARN+ERROR)/total >= this -> highload
TIME_WINDOW_MINUTES = 5          # estimate window length in minutes (for events/min metric)

logger = UniversalLogger("http://localhost:9880")

def read_juice_shop_docker_logs(tail_lines=TAIL_LINES):
    try:
        output = subprocess.check_output(
            ["docker", "logs", JUICE_CONTAINER, "--tail", str(tail_lines)],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30
        )
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to read docker logs: {e}")
        return []
    except Exception as e:
        print(f"✗ Error reading docker logs: {e}")
        return []
    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip()]
    return lines

def parse_line_to_event(line):
    # Try JSON first
    try:
        parsed = json.loads(line)
        level = parsed.get("level", parsed.get("severity", "INFO")).upper()
        message = parsed.get("message", line)
        timestamp = parsed.get("timestamp")
        return {"level": level, "message": message, "raw": line, "timestamp": timestamp}
    except Exception:
        # Heuristics: look for common level words
        up = line.upper()
        if "ERROR" in up:
            level = "ERROR"
        elif "WARN" in up or "WARNING" in up:
            level = "WARN"
        elif "FATAL" in up or "CRITICAL" in up:
            level = "FATAL"
        else:
            level = "INFO"
        return {"level": level, "message": line, "raw": line, "timestamp": None}

def make_structured_events_from_lines(lines):
    events = []
    for ln in lines:
        ev = parse_line_to_event(ln)
        events.append(ev)
    return events

def evaluate_highload(events):
    total = len(events)
    if total == 0:
        return {"highload": False, "reason": "no_events", "total": 0}

    errs = sum(1 for e in events if e["level"] in ("ERROR", "FATAL"))
    warns = sum(1 for e in events if e["level"] == "WARN")
    info = sum(1 for e in events if e["level"] == "INFO")
    error_warn = errs + warns
    error_ratio = error_warn / total

    # Estimate events per minute using TIME_WINDOW_MINUTES
    events_per_min = total / max(0.001, TIME_WINDOW_MINUTES)

    # Decision rules: require both a minimum event volume and an elevated error ratio
    if total >= HIGHLOAD_EVENTS_THRESHOLD and error_ratio >= HIGHLOAD_ERROR_RATIO:
        return {"highload": True, "reason": "high_volume_and_error_ratio", "total": total, "events_per_min": events_per_min, "error_ratio": error_ratio}
    # keep previous total-only rule if you want to trigger on sheer volume
    if total >= HIGHLOAD_EVENTS_THRESHOLD * 5:
        return {"highload": True, "reason": "very_high_volume", "total": total, "events_per_min": events_per_min, "error_ratio": error_ratio}
    return {"highload": False, "reason": "normal", "total": total, "events_per_min": events_per_min, "error_ratio": error_ratio}

def send_logs_in_batches(events, batch_size=BATCH_SIZE):
    total = len(events)
    sent = 0
    if total == 0:
        print("No logs found to send.")
        return
    print(f"Start streaming {total} Juice Shop log lines in batches of {batch_size}...")
    for i in range(0, total, batch_size):
        batch = events[i:i+batch_size]
        batch_sent = 0
        for ev in batch:
            level = ev.get("level", "INFO")
            message = ev.get("message", ev.get("raw", ""))
            source = "juice-shop"
            metadata = {"raw": ev.get("raw", "")}
            try:
                ok = logger.log(level, message, source, metadata)
            except Exception as e:
                ok = False
                print(f"✗ Exception while sending log: {e}")
            if ok:
                batch_sent += 1
        sent += batch_sent
        print(f"Batch {i//batch_size + 1}: sent {batch_sent}/{len(batch)}")
        del batch
        time.sleep(PAUSE_BETWEEN_BATCHES)
    print(f"Streaming complete: {sent}/{total} logs sent.")

if __name__ == "__main__":
    print("=== High-Load Test (Juice Shop docker logs -> UniversalLogger) ===")
    lines = read_juice_shop_docker_logs()
    events = make_structured_events_from_lines(lines)

    # send to UniversalLogger in controlled batches (optional - comment out if you don't want to resend)
    send_logs_in_batches(events, batch_size=BATCH_SIZE)

    # Evaluate highload from the same events
    result = evaluate_highload(events)

   # human-friendly volume label
total = result.get("total", 0)
if total == 0:
    volume_label = "none"
elif total < 100:
    volume_label = "low"
elif total < 1000:
    volume_label = "medium"
else:
    volume_label = "high"

verdict = "highload=yes" if result["highload"] else "highload=no"

print("\n=== High-Load Summary ===")
print(f"Volume = {total} ({volume_label})  # thresholds: low<100, 100-999 medium, >=1000 high")
print(f"Reason: {result.get('reason')}")
if "events_per_min" in result:
    print(f"Estimated events/min (window {TIME_WINDOW_MINUTES} min): {result.get('events_per_min'):.1f}")
if "error_ratio" in result:
    print(f"Warn+Error ratio: {result.get('error_ratio'):.2%}")
print(f"Final verdict: {verdict}")
print("=========================\n")