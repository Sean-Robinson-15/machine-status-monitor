from flask import Flask, jsonify, send_from_directory
from pythonping import ping
import threading
import time
import sys
import os
from datetime import datetime

def resource_path(rel):
    """Resolve a path that works both in dev and inside a PyInstaller bundle."""
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

app = Flask(__name__, static_folder=resource_path('static'))

MACHINES = {
    "HEPWIN2022-02": "HEPWIN2022-02 - TSE SolidWorks",
    "HEPWIN2019-06": "HEPWIN2019-06 - TSE Web Service",
    "HEPWIN2022-07": "HEPWIN2022-07 - TSE Mathmatica",
    "HEPWIN2019-09": "HEPWIN2019-09 - AD / DNS ",
    "HEPWIN2019-15": "HEPWIN2019-15 - Wamp DEV",
    "HEPWIN2019-16": "HEPWIN2019-16 - Wamp PROD",
    "HEPWIN2019-21": "HEPWIN2019-21 - TSE Web Access",
    "HEPWIN2019-29": "HEPWIN2019-29 - Bridging VM",
    "HEPWIN2019-30": "HEPWIN2019-30 - ADMIN VM",
    "HEPWIN2019-33": "HEPWIN2019-33 - TEST FOC Node",
    "HEPWIN2019-34": "HEPWIN2019-34 - TEST FOC Node",
    "HEPWIN2019-35": "HEPWIN2019-35 - File Server",
    "HEPWIN2019-36": "HEPWIN2019-36 - File Server",
    "HEPWIN2019-60": "HEPWIN2019-60 - PROD FOC Node",
    "HEPWIN2019-61": "HEPWIN2019-61 - PROD FOC Node",
    "HEPWIN2019-62": "HEPWIN2019-62 - TEST FOC Node",
    "HEPWIN2019-63": "HEPWIN2019-63 - TEST FOC Node",
    "HEPWIN2019-64": "HEPWIN2019-64 - PROD FOC Node",
    "HEPWIN2019-67": "HEPWIN2019-67 - PROD FOC Node",
    "HEPWIN2019-72": "HEPWIN2019-72 - PROD FOC Node",
    "HEPWIN2019-73": "HEPWIN2019-73 - PROD FOC Node",
    "HEPWIN2022-08": "HEPWIN2022-08 - DHCP",
    "HEPWIN2022-17": "HEPWIN2022-17 - Printing",
    "HEPWIN2022-18": "HEPWIN2022-18 - IIS",
    "HEPWIN2019-19": "HEPWIN2019-19 - Veeam",
    "8.8.8.8": "Google DNS",
    "130.246.40.240": "RAL Upton DNS"
}

status_data = {}
lock = threading.Lock()

def check_machine(host):
    try:
        # Use 1 ping with 2 second timeout
        result = ping(host, count=1, timeout=2, size=56)
        is_up = result.success()
        latency = result.rtt_avg_ms if is_up else None
    except Exception:
        is_up = False
        latency = None
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    with lock:
        if host not in status_data:
            status_data[host] = {
                'host': host,
                'description': MACHINES.get(host, host),
                'is_up': is_up,
                'last_check': now,
                'latency_ms': latency,
                'up_since': now if is_up else None,
                'down_since': None if is_up else now,
                'uptime_percentage': 100.0 if is_up else 0.0
            }
        else:
            prev = status_data[host]
            was_up = prev['is_up']
            
            if is_up and not was_up:
                # Came back up
                status_data[host]['up_since'] = now
                status_data[host]['down_since'] = None
            elif not is_up and was_up:
                # Went down
                status_data[host]['down_since'] = now
                status_data[host]['up_since'] = None
            elif not is_up and not was_up:
                # Still down, set down_since if not already set
                if not prev['down_since']:
                    status_data[host]['down_since'] = now
            
            status_data[host].update({
                'is_up': is_up,
                'last_check': now,
                'latency_ms': latency
            })
    
    return is_up

def monitor_loop():
    while True:
        for host in MACHINES.keys():
            check_machine(host)
        time.sleep(5)  # Check every 5 seconds

# Initialize status data
for host, description in MACHINES.items():
    status_data[host] = {
        'host': host,
        'description': description,
        'is_up': False,
        'last_check': None,
        'latency_ms': None,
        'up_since': None,
        'down_since': None,
        'uptime_percentage': 0.0
    }

# Start monitoring thread
monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
monitor_thread.start()

@app.route('/')
def index():
    return send_from_directory(resource_path('static'), 'index.html')

@app.route('/api/status')
def api_status():
    with lock:
        # Calculate uptime duration
        result = []
        now = datetime.utcnow()
        for host, data in status_data.items():
            item = data.copy()
            if item['is_up'] and item['up_since']:
                up_since_dt = datetime.fromisoformat(item['up_since'].replace('Z', ''))
                duration = now - up_since_dt
                item['up_duration_seconds'] = int(duration.total_seconds())
            elif not item['is_up'] and item['down_since']:
                down_since_dt = datetime.fromisoformat(item['down_since'].replace('Z', ''))
                duration = now - down_since_dt
                item['down_duration_seconds'] = int(duration.total_seconds())
            else:
                item['up_duration_seconds'] = 0
                item['down_duration_seconds'] = 0
            result.append(item)
        return jsonify(result)

@app.route('/api/machines')
def api_machines():
    return jsonify([{ 'host': k, 'description': v } for k, v in MACHINES.items()])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)