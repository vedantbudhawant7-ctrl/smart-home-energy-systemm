from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-demo-secret"
DB_PATH = Path(__file__).with_name("energy.db")

DEVICES = [
    {"name": "Light", "icon": "💡", "watts": 60},
    {"name": "Fan", "icon": "🌀", "watts": 70},
    {"name": "Television", "icon": "📺", "watts": 100},
    {"name": "Washing Machine", "icon": "🧺", "watts": 450},
]

def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect_db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK(id=1), tariff REAL NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS devices (
            name TEXT PRIMARY KEY, is_on INTEGER NOT NULL, watts REAL NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
            power_w REAL NOT NULL, energy_kwh REAL NOT NULL, cost REAL NOT NULL,
            note TEXT NOT NULL)""")
        con.execute("INSERT OR IGNORE INTO settings(id, tariff) VALUES(1, 8.0)")
        for d in DEVICES:
            con.execute("INSERT OR IGNORE INTO devices(name,is_on,watts) VALUES(?,?,?)",
                        (d["name"], 0, d["watts"]))
        count = con.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        if count == 0:
            # Clearly marked demonstration data, not actual sensor readings.
            for i in range(23, -1, -1):
                power = random.randint(80, 420)
                energy = power / 1000
                tariff = 8.0
                stamp = (datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
                con.execute("INSERT INTO readings(timestamp,power_w,energy_kwh,cost,note) VALUES(?,?,?,?,?)",
                            (stamp, power, energy, energy * tariff, "Demo data"))
        con.commit()

def current_power(con):
    rows = con.execute("SELECT watts FROM devices WHERE is_on=1").fetchall()
    return sum(row["watts"] for row in rows)

def add_reading(note="Manual demo sample"):
    with connect_db() as con:
        power = current_power(con)
        tariff = con.execute("SELECT tariff FROM settings WHERE id=1").fetchone()["tariff"]
        # A small energy interval (one minute) for this demo sample.
        energy = power / 1000 / 60
        con.execute("INSERT INTO readings(timestamp,power_w,energy_kwh,cost,note) VALUES(?,?,?,?,?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), power, energy, energy * tariff, note))
        con.commit()

BASE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Home Energy</title>
<style>
:root{--navy:#10213b;--blue:#2677f5;--bg:#f3f6fb;--text:#15243b;--muted:#68778d;--line:#e3eaf3}
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--text)}
.layout{display:flex;min-height:100vh}.sidebar{width:225px;background:var(--navy);color:white;padding:24px 16px;flex-shrink:0}
.brand{font-size:19px;font-weight:700;margin:4px 8px 6px}.subbrand{font-size:11px;color:#c1d1e8;margin:0 8px 28px}
.nav a{display:block;color:#d8e4f6;text-decoration:none;padding:12px 13px;border-radius:8px;margin:5px 0;font-size:14px}
.nav a.active,.nav a:hover{background:var(--blue);color:white}.main{flex:1;padding:28px;min-width:0}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:22px}.top h1{margin:0;font-size:26px}.sub{color:var(--muted);font-size:14px;margin-top:7px}
.tag{font-size:12px;background:#fff3d8;color:#855b00;border-radius:20px;padding:8px 12px}
.cards{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:15px;margin-bottom:18px}
.card{background:white;border:1px solid var(--line);border-radius:13px;padding:19px;box-shadow:0 3px 12px #14284a08}
.metric-label{font-size:13px;color:var(--muted)}.metric{font-size:25px;font-weight:700;margin-top:10px}.green{color:#139a66}
.columns{display:grid;grid-template-columns:1.25fr 1fr;gap:18px}.card h2{font-size:17px;margin:0 0 16px}
.chart{height:230px;display:flex;align-items:end;gap:7px;border-bottom:1px solid var(--line);padding:15px 5px 0}
.bar-wrap{height:100%;flex:1;display:flex;flex-direction:column;justify-content:end;align-items:center;gap:7px;min-width:0}
.bar{width:70%;max-width:25px;background:linear-gradient(180deg,#58a0ff,#2677f5);border-radius:5px 5px 0 0;min-height:4px}
.bar-label{font-size:10px;color:var(--muted);padding-bottom:7px}
.device{display:flex;align-items:center;gap:10px;padding:13px 0;border-bottom:1px solid var(--line)}
.device:last-child{border-bottom:0}.device-icon{font-size:23px;width:32px}.device-info{flex:1}.device-name{font-weight:600;font-size:14px}.device-watts{font-size:12px;color:var(--muted);margin-top:4px}
button,.button{border:0;border-radius:7px;background:var(--blue);color:white;padding:10px 13px;cursor:pointer;font-size:13px;text-decoration:none;display:inline-block}
button.off{background:#dfe6ef;color:#34445b}button.greenbtn{background:#12a56d}
.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:15px}.notice{padding:12px 14px;border-radius:8px;background:#e8f5ff;color:#15528b;margin-bottom:15px;font-size:14px}
.alert{padding:12px 14px;border-radius:8px;background:#fff0e7;color:#99451c;margin-bottom:15px;font-size:14px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:12px 9px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600;background:#f9fbfe}
.field{margin:14px 0}.field label{display:block;font-size:13px;margin-bottom:7px}.field input{padding:11px;border:1px solid #ccd7e6;border-radius:7px;width:100%;max-width:320px;font-size:14px}
.small{font-size:12px;color:var(--muted);line-height:1.6}.footer{margin-top:20px;color:var(--muted);font-size:12px}
@media(max-width:950px){.cards{grid-template-columns:repeat(2,1fr)}.columns{grid-template-columns:1fr}.sidebar{width:185px}}
@media(max-width:620px){.layout{display:block}.sidebar{width:100%;padding:15px}.subbrand{margin-bottom:12px}.nav{display:flex;overflow:auto;gap:5px}.nav a{white-space:nowrap}.main{padding:16px}.cards{grid-template-columns:1fr 1fr}.top h1{font-size:21px}.metric{font-size:21px}}
</style></head>
<body><div class="layout">
<aside class="sidebar"><div class="brand">⌂ Smart Home</div><div class="subbrand">ENERGY MONITORING & CONTROL</div>
<nav class="nav">
<a class="{{ 'active' if page=='dashboard' else '' }}" href="{{ url_for('dashboard') }}">⌂ &nbsp; Dashboard</a>
<a class="{{ 'active' if page=='usage' else '' }}" href="{{ url_for('usage') }}">▥ &nbsp; Energy Usage</a>
<a class="{{ 'active' if page=='devices' else '' }}" href="{{ url_for('devices_page') }}">⚡ &nbsp; Appliance Control</a>
<a class="{{ 'active' if page=='history' else '' }}" href="{{ url_for('history') }}">◷ &nbsp; History</a>
<a class="{{ 'active' if page=='settings' else '' }}" href="{{ url_for('settings') }}">⚙ &nbsp; Settings</a>
</nav><div class="footer" style="color:#b9c8dd">Student prototype • Demo mode</div></aside>
<main class="main">
{% with messages=get_flashed_messages() %}{% if messages %}{% for message in messages %}<div class="notice">{{ message }}</div>{% endfor %}{% endif %}{% endwith %}
<div class="top"><div><h1>{{ heading }}</h1><div class="sub">{{ subtitle }}</div></div><span class="tag">● Demo data</span></div>
{{ content|safe }}
<div class="footer">Smart Home Energy Monitoring and Control System · Educational prototype. Values are simulated until connected to a real energy sensor.</div>
</main></div></body></html>
"""

def page(page, heading, subtitle, content, **context):
    return render_template_string(BASE, page=page, heading=heading, subtitle=subtitle,
                                  content=render_template_string(content, **context))

@app.route("/")
def dashboard():
    with connect_db() as con:
        power = current_power(con)
        tariff = con.execute("SELECT tariff FROM settings WHERE id=1").fetchone()["tariff"]
        devices = con.execute("SELECT * FROM devices ORDER BY name").fetchall()
        total = con.execute("SELECT COALESCE(SUM(energy_kwh),0) e, COALESCE(SUM(cost),0) c FROM readings").fetchone()
        readings = con.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 12").fetchall()
    chart = list(reversed(readings))
    max_power = max([r["power_w"] for r in chart] or [1])
    bars = "".join(f'<div class="bar-wrap"><div class="bar" style="height:{max(4, int(r["power_w"]/max_power*100))}%"></div><div class="bar-label">{r["timestamp"][-5:]}</div></div>' for r in chart)
    content = r"""
<div class="cards">
<div class="card"><div class="metric-label">Current Power</div><div class="metric">{{ power }} W</div></div>
<div class="card"><div class="metric-label">Logged Energy</div><div class="metric">{{ '%.3f'|format(total.e) }} kWh</div></div>
<div class="card"><div class="metric-label">Estimated Cost</div><div class="metric">₹ {{ '%.2f'|format(total.c) }}</div></div>
<div class="card"><div class="metric-label">Energy Tariff</div><div class="metric green">₹ {{ '%.2f'|format(tariff) }}/kWh</div></div>
</div>
<div class="columns">
<section class="card"><h2>Recent Power Samples</h2><div class="small">Power (W) · latest recorded samples</div><div class="chart">{{ bars|safe }}</div>
<div class="actions"><form method="post" action="{{ url_for('sample') }}"><button>＋ Add Demo Sample</button></form><a class="button" href="{{ url_for('usage') }}">View usage</a></div></section>
<section class="card"><h2>Appliance Status</h2>
{% for d in devices %}<div class="device"><div class="device-icon">{{ icons.get(d.name,'🔌') }}</div><div class="device-info"><div class="device-name">{{ d.name }}</div><div class="device-watts">{{ d.watts }} W rated load · {{ 'ON' if d.is_on else 'OFF' }}</div></div><form method="post" action="{{ url_for('toggle', name=d.name) }}"><button class="{{ 'greenbtn' if d.is_on else 'off' }}">{{ 'Turn OFF' if d.is_on else 'Turn ON' }}</button></form></div>{% endfor %}
<div class="small">These controls change simulated device state only. Do not connect this demo directly to mains wiring.</div>
</section></div>
"""
    icons = {d["name"]: d["icon"] for d in DEVICES}
    return page("dashboard", "Energy Dashboard", "Monitor household energy use from one place.", content,
                power=power, tariff=tariff, total=total, devices=devices, bars=bars, icons=icons)

@app.route("/devices")
def devices_page():
    with connect_db() as con:
        devices = con.execute("SELECT * FROM devices ORDER BY name").fetchall()
    icons = {d["name"]: d["icon"] for d in DEVICES}
    content = r"""
<div class="card"><h2>Appliance Control</h2><div class="notice">Prototype mode: ON/OFF changes are stored in SQLite and used to calculate simulated current power.</div>
{% for d in devices %}<div class="device"><div class="device-icon">{{ icons.get(d.name,'🔌') }}</div><div class="device-info"><div class="device-name">{{ d.name }}</div><div class="device-watts">Rated power: {{ d.watts }} W</div></div><span class="tag">{{ 'ON' if d.is_on else 'OFF' }}</span><form method="post" action="{{ url_for('toggle', name=d.name) }}"><button class="{{ 'off' if d.is_on else 'greenbtn' }}">{{ 'Turn OFF' if d.is_on else 'Turn ON' }}</button></form></div>{% endfor %}
</div>
"""
    return page("devices", "Appliance Control", "Switch supported devices in the software prototype.", content, devices=devices, icons=icons)

@app.route("/toggle/<path:name>", methods=["POST"])
def toggle(name):
    with connect_db() as con:
        row = con.execute("SELECT is_on FROM devices WHERE name=?", (name,)).fetchone()
        if row:
            con.execute("UPDATE devices SET is_on=? WHERE name=?", (0 if row["is_on"] else 1, name))
            con.commit()
            flash(f"{name} switched {'off' if row['is_on'] else 'on'} in demo mode.")
    add_reading("Device control demo")
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/sample", methods=["POST"])
def sample():
    add_reading()
    flash("A demo sample was added to history.")
    return redirect(url_for("dashboard"))

@app.route("/usage")
def usage():
    with connect_db() as con:
        rows = con.execute("SELECT substr(timestamp,1,10) day, SUM(energy_kwh) energy, SUM(cost) cost, AVG(power_w) avg_power FROM readings GROUP BY substr(timestamp,1,10) ORDER BY day DESC LIMIT 14").fetchall()
    content = r"""
<div class="card"><h2>Daily Energy Summary</h2><p class="small">Calculated from saved readings. This demo stores a small simulated energy interval for each sample.</p>
<table><thead><tr><th>Date</th><th>Recorded energy (kWh)</th><th>Estimated cost (₹)</th><th>Average power (W)</th></tr></thead><tbody>
{% for r in rows %}<tr><td>{{ r.day }}</td><td>{{ '%.4f'|format(r.energy) }}</td><td>{{ '%.2f'|format(r.cost) }}</td><td>{{ '%.1f'|format(r.avg_power) }}</td></tr>{% else %}<tr><td colspan="4">No readings yet.</td></tr>{% endfor %}
</tbody></table></div>
"""
    return page("usage", "Energy Usage", "Review saved daily readings and estimated cost.", content, rows=rows)

@app.route("/history")
def history():
    with connect_db() as con:
        rows = con.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 100").fetchall()
    content = r"""
<div class="card"><h2>Reading History</h2><table><thead><tr><th>Date / Time</th><th>Power (W)</th><th>Energy (kWh)</th><th>Cost (₹)</th><th>Source</th></tr></thead><tbody>
{% for r in rows %}<tr><td>{{ r.timestamp }}</td><td>{{ '%.1f'|format(r.power_w) }}</td><td>{{ '%.5f'|format(r.energy_kwh) }}</td><td>{{ '%.4f'|format(r.cost) }}</td><td>{{ r.note }}</td></tr>{% else %}<tr><td colspan="5">No readings available.</td></tr>{% endfor %}
</tbody></table></div>
"""
    return page("history", "History & Logs", "Inspect recorded energy samples.", content, rows=rows)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    with connect_db() as con:
        if request.method == "POST":
            try:
                tariff = float(request.form.get("tariff", "8"))
                if tariff <= 0 or tariff > 1000:
                    raise ValueError
                con.execute("UPDATE settings SET tariff=? WHERE id=1", (tariff,))
                con.commit()
                flash("Electricity tariff updated.")
                return redirect(url_for("settings"))
            except ValueError:
                flash("Enter a tariff greater than ₹0 and no more than ₹1000 per kWh.")
        tariff = con.execute("SELECT tariff FROM settings WHERE id=1").fetchone()["tariff"]
    content = r"""
<div class="card"><h2>Electricity Cost Settings</h2><p class="small">Set a simplified per-unit tariff. Actual electricity bills may include slabs, fixed charges, taxes, and other adjustments.</p>
<form method="post"><div class="field"><label for="tariff">Tariff (₹ per kWh)</label><input id="tariff" name="tariff" type="number" min="0.01" max="1000" step="0.01" value="{{ '%.2f'|format(tariff) }}" required></div><button type="submit">Save tariff</button></form>
<hr style="border:0;border-top:1px solid #e3eaf3;margin:22px 0"><h2>Hardware integration notes</h2><p class="small">For a real implementation, connect an appropriately rated isolated energy-meter module to an ESP32/ESP8266 and send authenticated readings to a backend API. This starter project does not read physical sensors or switch actual appliances.</p></div>
"""
    return page("settings", "Settings", "Configure your estimated electricity cost.", content, tariff=tariff)

if __name__ == "__main__":
    init_db()
    if __name__ == "__main__":
    app.run(debug=True)
