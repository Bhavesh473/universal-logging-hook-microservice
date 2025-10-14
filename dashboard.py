from flask import Flask, render_template_string
import glob
import json
import os

app = Flask(__name__)

def read_logs():
    logs = []
    for file in glob.glob("logs/events.log.*.log"):
        if os.path.getsize(file) == 0:
            continue  # Skip empty files
        try:
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 3:
                        json_str = parts[2]
                        try:
                            log = json.loads(json_str)
                            logs.append(log)
                        except json.JSONDecodeError as e:
                            print(f"JSON error in {file}: {e}")
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return logs

@app.route('/')
def dashboard():
    logs = read_logs()
    html = """
    <h1>Universal Logging Dashboard</h1>
    <table border="1">
        <tr>
            <th>Timestamp</th>
            <th>Level</th>
            <th>Message</th>
            <th>Source</th>
            <th>Metadata</th>
        </tr>
        {% for log in logs %}
        <tr>
            <td>{{ log.timestamp if log.timestamp is defined else '—' }}</td>
            <td>{{ log.level if log.level is defined else '—' }}</td>
            <td>{{ log.message if log.message is defined else '—' }}</td>
            <td>{{ log.source if log.source is defined else '—' }}</td>
            <td>{{ log.metadata | tojson if log.metadata is defined else '{}' }}</td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, logs=logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)