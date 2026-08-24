# Machine Status Monitor

Simple real-time webpage to display up/down status of local machines via ping.

## Features

- Real-time monitoring of 18 HEPWIN machines
- Auto-refreshes every 30 seconds without page reload
- Tracks how long machines have been up/down
- Shows latency/ping times
- Beautiful responsive UI with status indicators
- Uptime percentage statistics

## Machines Monitored

- HEPWIN2019-06, HEPWIN2019-09, HEPWIN2019-15, HEPWIN2019-16
- HEPWIN2019-21, HEPWIN2019-29, HEPWIN2019-30, hepwin2019-35
- HEPWIN2019-36, HEPWIN2019-60, HEPWIN2019-61, HEPWIN2019-64
- HEPWIN2019-67, HEPWIN2019-72, HEPWIN2019-73, HEPWIN2022-07
- HEPWIN2022-08, HEPWIN2022-17

## Setup

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python server.py
```

3. Open browser to: http://localhost:5000

The server will automatically:
- Start pinging all machines every 30 seconds
- Track up/down duration for each machine
- Serve the web interface

## How it works

1. **Backend (server.py)**: Flask server that pings machines using pythonping
2. **Monitoring**: Background thread checks all machines every 30 seconds
3. **Frontend**: Static HTML/CSS/JS that polls `/api/status` endpoint
4. **Auto-update**: JavaScript fetches new data every 30 seconds without refresh

## Customization

Edit the `MACHINES` list in `server.py` to add/remove machines.

Change check interval by modifying `time.sleep(30)` in the monitor loop.

## Notes

- Ping requires network access to the machines
- Some machines may need firewall exceptions for ICMP
- Works best when server is on same network as monitored machines
- For production, consider using gunicorn instead of Flask dev server
