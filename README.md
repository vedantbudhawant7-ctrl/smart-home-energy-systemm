# Smart Home Energy Monitoring and Control System

A student-friendly website prototype built with Python Flask and SQLite.

## Features
- Energy dashboard with current simulated power, logged energy and estimated cost
- Appliance ON/OFF controls (software simulation only)
- Daily energy summary
- Reading history
- Configurable electricity tariff
- Responsive layout for desktop and mobile

## Requirements
- Python 3.9+ recommended
- Internet is not required after Flask is installed

## Run in VS Code

1. Extract this ZIP and open the `smart_home_energy_system` folder in VS Code.
2. Open Terminal > New Terminal.
3. (Optional but recommended) create a virtual environment:

   Windows:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   ```

   Ubuntu/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install Flask:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the website:
   ```bash
   python app.py
   ```
   On Ubuntu/Linux, use `python3 app.py` if `python` is not available.

6. Open this address in your browser:
   http://127.0.0.1:5000

The `energy.db` SQLite database is created automatically on first run.

## Important project limitations
- The initial chart data and readings are simulated demonstration values.
- Appliance buttons change only the software database; they do not operate real hardware.
- To get actual real-time readings, integrate a correctly rated, isolated energy-meter module and ESP32/ESP8266 firmware with an authenticated API.
- Household mains voltage is dangerous. Any real wiring, relay/contactor installation, or mains testing must be done by a qualified person with proper isolation and protection.
- Before deployment, change `app.secret_key`, add proper user authentication, CSRF protection, validation, HTTPS, and secure access control. Do not expose the Flask development server directly to the public internet.
