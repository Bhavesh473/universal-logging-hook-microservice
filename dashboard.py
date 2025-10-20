# dashboard.py - UNIVERSAL LOGGING DASHBOARD (with sensitive-event highlighting & filter)

from flask import Flask, jsonify, render_template_string, request
import glob, json, os, subprocess, re
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
LOG_GLOB_PATTERNS = [
    "events_test.log",
    "events.log",
    "errors.log",
    "logs/*.log",
    "logs/**/*.log",
    "logs/*.txt"
]

VOLUME_THRESHOLD = 200
ERROR_RATIO_THRESHOLD = 0.10
TIME_WINDOW_MINUTES = 5
MAX_EVENTS_RETURN = 1000

# Keywords / patterns considered "sensitive" (case-insensitive)
SENSITIVE_PATTERNS = [
    r"\bPOST\b", r"\bPUT\b", r"\bDELETE\b",
    r"login", r"logout", r"\bbasket\b", r"\bbasketitems\b",
    r"/api/", r"/rest/", r"\bbasket\b", r"\bcart\b"
]
SENSITIVE_RE = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)

def find_log_files():
    files = []
    for pat in LOG_GLOB_PATTERNS:
        matched = sorted(glob.glob(pat, recursive=True))
        matched = [f for f in matched if os.path.isfile(f)]
        files.extend(matched)
    seen = set()
    uniq = []
    for f in files:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq

def parse_log_line_to_dict(line):
    line = line.strip()
    if not line:
        return None
    try:
        parsed = json.loads(line)
        msg = parsed.get("message", parsed.get("msg", ""))
        source = parsed.get("source", parsed.get("service", "unknown"))
        entry = {
            "timestamp": parsed.get("timestamp") or datetime.utcnow().isoformat() + "Z",
            "level": str(parsed.get("level", "INFO")).upper(),
            "message": msg,
            "source": source,
            "metadata": parsed,
            "raw": line
        }
        entry["sensitive"] = bool(SENSITIVE_RE.search(json.dumps(parsed) + " " + str(msg)))
        return entry
    except Exception:
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                parsed = json.loads(parts[2])
                msg = parsed.get("message", parsed.get("msg", ""))
                entry = {
                    "timestamp": parsed.get("timestamp") or datetime.utcnow().isoformat() + "Z",
                    "level": str(parsed.get("level", "INFO")).upper(),
                    "message": msg,
                    "source": parsed.get("source", parsed.get("service", "unknown")),
                    "metadata": parsed,
                    "raw": parts[2]
                }
                entry["sensitive"] = bool(SENSITIVE_RE.search(json.dumps(parsed) + " " + str(msg)))
                return entry
            except Exception:
                pass
        up = line.upper()
        if "ERROR" in up or "FATAL" in up:
            level = "ERROR"
        elif "WARN" in up or "WARNING" in up:
            level = "WARN"
        elif "DEBUG" in up:
            level = "DEBUG"
        else:
            level = "INFO"
        msg = line[:2000]
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": msg,
            "source": "unknown",
            "metadata": {},
            "raw": line
        }
        entry["sensitive"] = bool(SENSITIVE_RE.search(line))
        return entry

def read_logs_from_docker():
    """Read real-time logs from Docker containers (includes juice-proxy)."""
    logs = []
    # Adjust container names if different in your environment
    containers = [
        "universal-logging-fluentd",
        "juice-proxy",
        "juice-shop",
        "universal-logging-redis"
    ]

    for container in containers:
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", "500", container],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            raw_lines = result.stdout.splitlines()
        except subprocess.TimeoutExpired:
            app.logger.warning(f"Timeout reading logs for {container}")
            raw_lines = []
        except Exception as e:
            app.logger.warning(f"Error reading logs for {container}: {e}")
            raw_lines = []

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            log_entry = None

            # If it's a JSON object line (nginx access.json or fluentd forwarded JSON)
            if line.startswith("{") and line.endswith("}"):
                try:
                    obj = json.loads(line)
                    msg = (obj.get("method", "") + " " + obj.get("path", "")).strip() or obj.get("message", "") or obj.get("msg", "")
                    log_entry = {
                        "timestamp": obj.get("timestamp") or obj.get("time") or obj.get("received_at") or datetime.utcnow().isoformat() + "Z",
                        "level": str(obj.get("level", "INFO")).upper(),
                        "message": msg,
                        "source": obj.get("source") or obj.get("service") or container,
                        "metadata": obj,
                        "raw": line
                    }
                    log_entry["sensitive"] = bool(SENSITIVE_RE.search(json.dumps(obj) + " " + str(msg)))
                except Exception:
                    log_entry = None
            else:
                # try to extract JSON substring if present
                if "{" in line and "}" in line:
                    try:
                        json_start = line.index("{")
                        json_str = line[json_start:]
                        obj = json.loads(json_str)
                        msg = (obj.get("method", "") + " " + obj.get("path", "")).strip() or obj.get("message", "") or obj.get("msg", "")
                        log_entry = {
                            "timestamp": obj.get("timestamp") or obj.get("time") or obj.get("received_at") or datetime.utcnow().isoformat() + "Z",
                            "level": str(obj.get("level", "INFO")).upper(),
                            "message": msg,
                            "source": obj.get("source") or obj.get("service") or container,
                            "metadata": obj,
                            "raw": line
                        }
                        log_entry["sensitive"] = bool(SENSITIVE_RE.search(json.dumps(obj) + " " + str(msg)))
                    except Exception:
                        log_entry = None

            # fallback plain text parsing
            if not log_entry:
                up = line.upper()
                if "ERROR" in up or "FATAL" in up:
                    level = "ERROR"
                elif "WARN" in up or "WARNING" in up:
                    level = "WARN"
                elif "DEBUG" in up:
                    level = "DEBUG"
                else:
                    level = "INFO"

                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": level,
                    "message": line[:1000],
                    "source": container,
                    "metadata": {},
                    "raw": line
                }
                log_entry["sensitive"] = bool(SENSITIVE_RE.search(line))

            logs.append(log_entry)

    # try to sort newest first by timestamp string (ISO-like)
    try:
        logs.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    except Exception:
        pass

    return logs

def read_logs():
    """Read logs - try Docker first, then files"""
    docker_logs = read_logs_from_docker()
    if docker_logs:
        app.logger.info(f"Read {len(docker_logs)} logs from Docker")
        return docker_logs

    logs = []
    files = find_log_files()
    app.logger.debug(f"Found log files: {files}")
    for file in files:
        try:
            if not os.path.exists(file):
                continue
            if os.path.isdir(file):
                app.logger.debug(f"Skipping directory: {file}")
                continue
            if os.path.getsize(file) == 0:
                app.logger.debug(f"Skipping empty file: {file}")
                continue
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    parsed = parse_log_line_to_dict(line)
                    if parsed:
                        logs.append(parsed)
        except Exception as e:
            app.logger.warning(f"Error reading {file}: {e}")
    return logs

def evaluate_metrics(logs):
    total = len(logs)
    errs = sum(1 for e in logs if e["level"] in ("ERROR", "FATAL"))
    warns = sum(1 for e in logs if e["level"] == "WARN")
    sensitive_count = sum(1 for e in logs if e.get("sensitive"))
    error_warn = errs + warns
    error_ratio = (error_warn / total) if total > 0 else 0.0
    events_per_min = total / max(0.001, TIME_WINDOW_MINUTES)

    if total == 0:
        volume_label = "none"
    elif total < 100:
        volume_label = "low"
    elif total < 1000:
        volume_label = "medium"
    else:
        volume_label = "high"

    highload = (total >= VOLUME_THRESHOLD) and (error_ratio >= ERROR_RATIO_THRESHOLD)
    reason = "volume_and_error_ratio" if highload else ("no_events" if total == 0 else "normal")

    return {
        "total": total,
        "errs": errs,
        "warns": warns,
        "sensitive": sensitive_count,
        "error_warn": error_warn,
        "error_ratio": error_ratio,
        "events_per_min": events_per_min,
        "volume_label": volume_label,
        "highload": highload,
        "reason": reason
    }

@app.route("/api/logs")
def api_logs():
    limit = request.args.get("limit", type=int) or MAX_EVENTS_RETURN
    time_window = request.args.get("time_window", type=int) or TIME_WINDOW_MINUTES
    level_filter = request.args.get("level", "").strip().upper()
    source_filter = request.args.get("source", "").strip().lower()
    text_search = request.args.get("search", "").strip().lower()
    sensitive_filter = request.args.get("sensitive", "").strip().lower()  # "1", "true", etc.

    logs = read_logs()

    # Apply filters
    filtered_logs = []
    for log in logs:
        if level_filter and log["level"] != level_filter:
            continue
        if source_filter and source_filter not in str(log.get("source", "")).lower():
            continue
        if text_search:
            haystack = (str(log.get("message", "")) + json.dumps(log.get("metadata", {}))).lower()
            if text_search not in haystack:
                continue
        if sensitive_filter:
            if sensitive_filter in ("1", "true", "yes", "on"):
                if not log.get("sensitive"):
                    continue
        filtered_logs.append(log)

    # newest first to UI expects reversed order in some places — keep newest first
    # but the JS expects newest first already, so no extra reverse here.
    # If you prefer newest first in UI, ensure JS lists without re-reverse.
    # For compatibility with existing UI, we will keep newest-first order.
    # Calculate metrics on ALL logs
    metrics = evaluate_metrics(logs)

    limited = filtered_logs[:max(0, min(limit, MAX_EVENTS_RETURN))]

    return jsonify({
        "metrics": metrics,
        "logs": limited,
        "filtered_count": len(filtered_logs),
        "total_count": len(logs)
    })

# --------- Frontend template (IMPROVED VISIBILITY) ---------
TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"/><title>Universal Logging Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { background:#0b1220; color:#e6eef8; }
.card { background:#0f1724; border:1px solid rgba(255,255,255,0.12); }

/* IMPROVED METRICS VISIBILITY */
.card .d-flex.gap-2 strong {
    color: #c5d3e8;
    font-size: 0.95rem;
    font-weight: 600;
}
.card .d-flex.gap-2 span {
    color: #ffffff !important;
    font-weight: 700;
    font-size: 1.2rem;
    text-shadow: 0 0 4px rgba(255,255,255,0.3);
}

/* IMPROVED FILTER TEXT VISIBILITY */
.applied-filters {
    font-size: 1rem;
    color: #e0f0ff !important;
    padding: 10px;
    background: rgba(45, 156, 219, 0.15);
    border-radius: 6px;
    border-left: 3px solid #2d9cdb;
    font-weight: 600;
}

/* IMPROVED HEADER VISIBILITY */
h6.mb-0, h6.tiny {
    color: #e6f4ff !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Graph container - better background */
#level-chart {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 10px;
}

.badge-ERROR{background:#e02424; font-weight:700;}
.badge-FATAL{background:#8B0000; font-weight:700;}
.badge-WARN{background:#ff8c00;color:#000; font-weight:700;}
.badge-INFO{background:#2d9cdb; font-weight:700;}
.badge-DEBUG{background:#6b7280; font-weight:700;}

.mono{font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", monospace;}
.tiny{font-size:.82rem;color:#b8c9dc;}
.meta{font-size:.85rem;background:rgba(255,255,255,0.05);padding:12px;border-radius:6px;max-height:300px;overflow-y:auto;border:1px solid rgba(255,255,255,0.1);}
.no-logs{padding:30px;text-align:center;color:#9fb0c9;}
.table-row:hover{background:rgba(255,255,255,0.08);cursor:pointer;}

.sensitive-row{ 
    background: linear-gradient(90deg, rgba(255,255,0,0.08), rgba(255,140,0,0.04)); 
    border-left: 4px solid rgba(255,140,0,0.9); 
}
.sensitive-tag{ 
    color:#ff8c00; 
    font-weight:700; 
    margin-left:8px; 
    font-size:.9rem; 
    background:rgba(255,140,0,0.2); 
    padding:2px 8px; 
    border-radius:4px; 
}

/* FIXED STATUS BADGE - NO OVERLAP */
.status-badge{
    position:fixed;
    top:10px;
    right:10px;
    padding:8px 14px;
    border-radius:6px;
    background:#0f1724;
    border:2px solid #2d9cdb;
    z-index:1000; 
    font-weight:600;
    font-size:0.85rem;
}

/* Live indicator */
.live-on{color:#00ff00; font-weight:700; font-size:1.1rem;}
.live-off{color:#888; font-size:1.1rem;}

/* Better label visibility */
.form-label {
    color: #d0e0f0 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* Sensitive count highlight */
#sensitive-count {
    background: rgba(255,140,0,0.25);
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 1rem !important;
}

/* HEADER BUTTON LAYOUT - NO OVERLAP */
.header-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
</style>
</head><body>

<!-- FIXED: Status badge stays in corner -->
<div class="status-badge">
  <span class="tiny">Docker: <span id="docker-status">Loading...</span></span>
</div>

<div class="container-fluid p-3">
  <!-- FIXED: Better button layout -->
  <div class="d-flex align-items-center mb-3 flex-wrap">
    <h2 class="me-3 mb-0">🍊 Universal Logging Dashboard</h2>
    <div class="tiny muted me-3">Live: <span id="live-indicator" class="live-off">OFF</span></div>
    
    <!-- FIXED: Buttons on left side, no overlap -->
    <div class="header-controls ms-auto">
      <button id="live-toggle" class="btn btn-sm btn-outline-light">Start Live</button>
      <div class="form-check form-switch mb-0">
        <input class="form-check-input" type="checkbox" id="sensitive-only">
        <label class="form-check-label tiny" for="sensitive-only" style="color:#e0f0ff !important; font-weight:600;">Show only sensitive</label>
      </div>
    </div>
  </div>
 
  <div class="row g-3">
    <div class="col-12 col-md-3">
      <div class="card p-3 mb-3">
        <h6 class="tiny">Filters</h6>
        <div class="mb-2"><label class="form-label tiny">Level</label>
          <select id="level-filter" class="form-select form-select-sm">
            <option value="">All</option><option>ERROR</option><option>FATAL</option><option>WARN</option><option>INFO</option><option>DEBUG</option>
          </select></div>
        <div class="mb-2"><label class="form-label tiny">Source (substring)</label>
          <input id="source-filter" class="form-control form-control-sm" placeholder="service or source"></div>
        <div class="mb-2"><label class="form-label tiny">Search (message or metadata)</label>
          <input id="text-search" class="form-control form-control-sm" placeholder="search text"></div>
        <div class="mb-2"><label class="form-label tiny">Time window (minutes)</label>
          <input id="time-window" type="number" value="5" min="1" class="form-control form-control-sm"></div>
        <button id="apply-filters" class="btn btn-sm btn-primary mt-2">Apply Filters</button>
        <div class="mt-2 tiny muted">Reading from: Docker + Files</div>
      </div>
     
      <div class="card p-3">
        <h6 class="tiny">Metrics <span id="sensitive-count"></span></h6>
        <div class="d-flex gap-2 flex-column">
          <div><strong>Total:</strong> <span id="metric-total">0</span></div>
          <div><strong>Filtered:</strong> <span id="metric-filtered">0</span></div>
          <div><strong>Errors:</strong> <span id="metric-errs" style="color:#ff6b6b !important;">0</span></div>
          <div><strong>Warns:</strong> <span id="metric-warns" style="color:#ff8c00 !important;">0</span></div>
          <div><strong>Events/min:</strong> <span id="metric-epm">0</span></div>
          <div><strong>Error ratio:</strong> <span id="metric-ratio">0%</span></div>
          <div><strong>Volume:</strong> <span id="metric-volume-label">none</span></div>
          <div class="mt-2"><strong>Highload:</strong> <span id="metric-highload">no</span></div>
        </div>
      </div>
    </div>
   
    <div class="col-12 col-md-9">
      <div class="card p-3 mb-3">
        <div class="d-flex align-items-center mb-2">
          <h6 class="mb-0">Real-Time Log Tail</h6>
          <div class="ms-auto tiny muted" style="color:#b8c9dc !important; font-weight:600;">Click row to expand metadata | Newest first</div>
        </div>
        <div id="applied-filters" class="applied-filters">No filters applied</div>
        <div class="mb-3" style="max-width:500px;">
          <canvas id="level-chart" height="90"></canvas>
        </div>
        <div id="logs-container" style="max-height:60vh; overflow:auto;"></div>
      </div>
    </div>
  </div>
</div>

<template id="row-tpl">
  <div class="p-2 table-row" role="button" style="border-bottom:1px solid rgba(255,255,255,0.05);">
    <div class="d-flex">
      <div style="width:140px;" class="mono tiny" data-ts></div>
      <div style="width:90px;" class="tiny" data-level></div>
      <div class="flex-fill" data-message style="padding-right:10px; color:#e6f4ff; font-weight:500;"></div>
      <div style="width:180px;" class="tiny text-end" data-source></div>
    </div>
    <div class="mt-1 small meta" data-meta style="display:none;"></div>
  </div>
</template>

<!-- Add Chart.js and JavaScript here -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
// Your JavaScript code here
</script>

</body></html>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
let live = false, pollInterval = null;
const POLL_MS = 2000;
const MAX_ROWS = 200;
let levelChart = null;

function initChart(){
  const ctx = document.getElementById('level-chart').getContext('2d');
  levelChart = new Chart(ctx, {
    type: 'bar',
    data: { labels: ['ERROR','WARN','INFO'], datasets: [{ label: 'Count', data: [0,0,0] }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true }, x: {} } }
  });
}

function updateChartFromMetrics(metrics){
  if(!levelChart) initChart();
  const errs = metrics.errs || 0;
  const warns = metrics.warns || 0;
  const infos = Math.max(0, (metrics.total || 0) - errs - warns);
  levelChart.data.datasets[0].data = [errs, warns, infos];
  levelChart.update();
}

function getFilterParams(){
  return {
    level: document.getElementById('level-filter').value.trim(),
    source: document.getElementById('source-filter').value.trim(),
    search: document.getElementById('text-search').value.trim(),
    time_window: document.getElementById('time-window').value || '5',
    sensitive_only: document.getElementById('sensitive-only').checked
  };
}

function updateAppliedFiltersDisplay(){
  const params = getFilterParams();
  const lvl = params.level || 'any';
  const src = params.source || 'any';
  const txt = params.search || '*';
  const mins = params.time_window;
  const s = params.sensitive_only ? ' • Sensitive only' : '';
  document.getElementById('applied-filters').innerText = `Filters: Level=${lvl} • Source=${src} • Text="${txt}" • Window=${mins}m${s}`;
}

function humanTime(ts){
  if(!ts) return '---';
  try{
    const d = new Date(ts);
    if(isNaN(d)) return ts;
    const sec = Math.floor((Date.now()-d.getTime())/1000);
    if(sec<60) return sec+'s ago';
    if(sec<3600) return Math.floor(sec/60)+'m ago';
    return d.toLocaleString();
  }catch(e){return ts;}
}

function badgeFor(level){
  if(level==='ERROR') return '<span class="badge badge-ERROR">ERROR</span>';
  if(level==='FATAL') return '<span class="badge badge-FATAL">FATAL</span>';
  if(level==='WARN') return '<span class="badge badge-WARN">WARN</span>';
  if(level==='INFO') return '<span class="badge badge-INFO">INFO</span>';
  return '<span class="badge badge-DEBUG">DEBUG</span>';
}

function escapeHtml(s){ return String(s).replace(/[&<>"']/g, m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m]); }

function renderLogs(data){
  const container = document.getElementById('logs-container');
  const logs = data.logs || [];
  const metrics = data.metrics || {};

  document.getElementById('docker-status').innerHTML = data.total_count > 0 ? '<span style="color:#00ff00">✓ Connected</span>' : '<span style="color:#ff8c00">⚠ No Logs</span>';
  document.getElementById('metric-total').innerText = metrics.total || 0;
  document.getElementById('metric-filtered').innerText = data.filtered_count || 0;
  document.getElementById('metric-errs').innerText = metrics.errs || 0;
  document.getElementById('metric-warns').innerText = metrics.warns || 0;
  document.getElementById('metric-epm').innerText = (metrics.events_per_min||0).toFixed(1);
  document.getElementById('metric-ratio').innerText = ((metrics.error_ratio||0)*100).toFixed(2) + '%';
  document.getElementById('metric-volume-label').innerText = metrics.volume_label || 'none';
  document.getElementById('metric-highload').innerText = (metrics.highload ? 'yes' : 'no');
  document.getElementById('sensitive-count').innerText = metrics.sensitive ? 'Sensitive: ' + metrics.sensitive : '';

  updateAppliedFiltersDisplay();
  updateChartFromMetrics(metrics);

  if(logs.length === 0){
    container.innerHTML = '<div class="no-logs">No logs found. Make sure Fluentd / docker logs are running.<br><br>Try: <code>docker logs universal-logging-fluentd --tail 20</code></div>';
    return;
  }

  container.innerHTML = '';
  const tpl = document.getElementById('row-tpl');
  let count = 0;

  for(let i=0; i<logs.length && count<MAX_ROWS; i++){
    const log = logs[i];
    const clone = tpl.content.cloneNode(true);

    const tsEl = clone.querySelector('[data-ts]');
    tsEl.innerText = humanTime(log.timestamp);

    const levelEl = clone.querySelector('[data-level]');
    levelEl.innerHTML = badgeFor(log.level || 'INFO');

    const messageEl = clone.querySelector('[data-message]');
    messageEl.innerText = log.message || '---';
    messageEl.style.whiteSpace = 'normal';
    messageEl.style.wordWrap = 'break-word';

    clone.querySelector('[data-source]').innerText = log.source || '---';

    const metaDiv = clone.querySelector('[data-meta]');
    metaDiv.innerHTML = '<pre style="margin:0;">' + escapeHtml(JSON.stringify(log.metadata||{},null,2)) + '</pre>';

    const row = clone.querySelector('.table-row');
    if(log.sensitive){
      row.classList.add('sensitive-row');
      const sourceDiv = clone.querySelector('[data-source]');
      sourceDiv.innerHTML += '<span class="sensitive-tag">SENSITIVE</span>';
    }

    row.addEventListener('click', () => {
      metaDiv.style.display = metaDiv.style.display === 'none' ? 'block' : 'none';
    });

    container.appendChild(clone);
    count++;
  }
}

async function pollOnce(){
  try{
    const params = getFilterParams();
    const query = new URLSearchParams({
      limit: 500,
      level: params.level,
      source: params.source,
      search: params.search,
      time_window: params.time_window,
      sensitive: params.sensitive_only ? '1' : ''
    });

    const resp = await fetch(`/api/logs?${query}`);
    const data = await resp.json();
    renderLogs(data);
  }catch(e){
    console.error('poll error', e);
    document.getElementById('docker-status').innerHTML = '<span style="color:#e02424">✗ Error</span>';
  }
}

document.getElementById('live-toggle').addEventListener('click', function(){
  live = !live;
  const indicator = document.getElementById('live-indicator');
  indicator.innerText = live ? 'ON' : 'OFF';
  indicator.className = live ? 'live-on' : 'live-off';
  this.innerText = live ? 'Stop Live' : 'Start Live';
  if(live){ pollOnce(); pollInterval = setInterval(pollOnce, POLL_MS); } else { clearInterval(pollInterval); pollInterval=null; }
});

document.getElementById('apply-filters').addEventListener('click', () => { pollOnce(); });

['level-filter','source-filter','text-search','time-window','sensitive-only'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener('keydown', (ev) => { if(ev.key === 'Enter') { ev.preventDefault(); pollOnce(); } });
  el.addEventListener('change', () => { if(id === 'sensitive-only') pollOnce(); });
});

// Initial load
pollOnce();
</script>
</body></html>
"""

@app.route("/")
def page():
    patterns = ", ".join(LOG_GLOB_PATTERNS)
    return render_template_string(TEMPLATE, TIME_WINDOW_MINUTES=TIME_WINDOW_MINUTES, patterns=patterns)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🍊 UNIVERSAL LOGGING DASHBOARD - STARTING")
    print("="*70)
    print("\n📊 Dashboard Features:")
    print("  ✓ Real-time Fluentd Docker logs")
    print("  ✓ File-based logs (fallback)")
    print("  ✓ Live auto-refresh")
    print("  ✓ Multi-level filtering")
    print("  ✓ Source-based search")
    print("  ✓ Full-text search")
    print("  ✓ Sensitive-event highlighting & filter")
    print("\n🚀 Access dashboard at: http://localhost:5000")
    print("="*70 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
