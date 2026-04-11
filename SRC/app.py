import os
import time
import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta

# --- Twilio SMS Integration ---
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("[WARNING] twilio package not installed. Run: pip install twilio")

# Twilio Configuration - Replace with your actual credentials
TWILIO_ACCOUNT_SID = 'ACb52548537ae425e91a38823937901409'   # From twilio.com/console
TWILIO_AUTH_TOKEN  = 'ccc42b8b4afe47a1ab1a364ff48da3e1'     # From twilio.com/console
TWILIO_FROM_NUMBER = '+17712328309'               # Your Twilio phone number
TWILIO_TO_NUMBER   = '+919025036336'              # Recipient phone number (E.164 format)

# Global Safety & Control Flags
ENABLE_SMS = True           # Master toggle for SMS
AUTO_SUPPRESS_SMS = False    # Flips to True if Twilio daily limit hit
SMS_COOLDOWN_SECONDS = 30 * 60
_last_sms_time: float = 0.0

def send_sms(message_body: str):
    """Generic SMS sender with a 30-minute cooldown to avoid spam."""
    global _last_sms_time
    now = time.time()
    if not ENABLE_SMS or AUTO_SUPPRESS_SMS:
        return
    if not TWILIO_AVAILABLE:
        print("[SMS] Twilio unavailable. Would have sent:", message_body)
        return
    if 'YOUR_TWILIO' in TWILIO_ACCOUNT_SID:
        print("[SMS] Twilio credentials not configured. Skipping SMS.")
        return
    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message_body,
            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER
        )
        _last_sms_time = now
        print(f"[SMS] Sent: {message_body[:80]}...")
    except Exception as e:
        error_msg = str(e)
        if "exceeded the 50 daily messages limit" in error_msg:
            AUTO_SUPPRESS_SMS = True
            print("[SMS] TRIAL LIMIT HIT. SMS auto-suppressed for this session.")
        else:
            print(f"[SMS] Failed to send: {error_msg}")


def send_sms_alert(low_fields: list):
    """Send SMS when fields have low moisture."""
    field_list = ', '.join(low_fields)
    send_sms(
        f"[Smart Irrigation Alert] Low moisture detected!\n"
        f"Fields needing water: {field_list}\n"
        f"Please check your irrigation system."
    )


def send_gate_open_sms(gate_id: str, field_name: str):
    """Send SMS when a gate is auto-opened."""
    send_sms(
        f"[Smart Irrigation] Auto-Irrigation Started!\n"
        f"Gate {gate_id} has been OPENED automatically for {field_name}.\n"
        f"Reason: Low soil moisture detected below threshold."
    )

app = Flask(__name__)
app.secret_key = 'smart_irrigation_secret_key'

DATABASE = 'database/irrigation_data.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists('database'):
        os.makedirs('database')
    conn = get_db()
    with open('database/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()

# Initialize Database on Startup
init_db()

# In-memory database with 6 fields and 8 gates
system_state = {
    'moisture': {
        'field_1': 0, 'field_2': 0, 'field_3': 0, 
        'field_4': 0, 'field_5': 0, 'field_6': 0
    },
    'water_flow': 0.0,
    'pump_status': 'OFF',
    'gates': {
        'G1': 'CLOSED', 'G2': 'CLOSED', 'G3': 'CLOSED', 'G4': 'CLOSED',
        'G5': 'CLOSED', 'G6': 'CLOSED', 'G7': 'CLOSED', 'G8': 'CLOSED'
    },
    'alert': None,
    'light_status': 'OFF',
    'last_update': time.time()
}


THRESHOLD_MOISTURE = 30  # % - fields below this get auto-watered

# Map each field to the gate that controls it
# G1 = main valve, G2 = right-side main; field-specific gates are:
FIELD_TO_GATE = {
    'field_1': 'G3',  # Block 1 → Gate G3
    'field_2': 'G4',  # Block 2 → Gate G4
    'field_3': 'G5',  # Block 3 → Gate G5
    'field_4': 'G6',  # Block 4 → Gate G6
    'field_5': 'G7',  # Block 5 → Gate G7
    'field_6': 'G8',  # Block 6 → Gate G8
}


def apply_system_logic(trigger_type, trigger_id, action):
    """
    Enforces hierarchical dependencies between Pump and Gates based on user requirements.
    trigger_type: 'PUMP', 'GATE'
    trigger_id: 'G1'...'G8'
    action: 'ON'/'OFF' or 'OPEN'/'CLOSED'
    """
    gates = system_state['gates']
    
    if trigger_type == 'PUMP':
        system_state['pump_status'] = action
        if action == 'OFF':
            # Stop Pump -> All gates close, Light turns off
            for g_id in gates:
                gates[g_id] = 'CLOSED'
            system_state['light_status'] = 'OFF'
            print("[LOGIC] Master Shutdown: Pump stopped. All gates/lights turned OFF.")
            
    elif trigger_type == 'GATE':
        # G1 Branch: G3, G4, G5
        branch_a = ['G3', 'G4', 'G5']
        # G2 Branch: G6, G7, G8
        branch_b = ['G6', 'G7', 'G8']
        
        if trigger_id in branch_a:
            if action == 'OPEN':
                # Quick-Start: Child open -> Parent G1 and Pump MUST open
                gates[trigger_id] = 'OPEN'
                gates['G1'] = 'OPEN'
                system_state['pump_status'] = 'ON'
                print(f"[LOGIC] Branch A Start: {trigger_id} opened -> G1/Pump started.")
            else:
                # Linkage Kill: Child close -> Parent G1 and Pump MUST close
                gates[trigger_id] = 'CLOSED'
                gates['G1'] = 'CLOSED'
                system_state['pump_status'] = 'OFF'
                for g in branch_a:
                    gates[g] = 'CLOSED'
                print(f"[LOGIC] Branch A Stop: {trigger_id} closed -> G1/Pump shutdown.")
        
        elif trigger_id in branch_b:
            if action == 'OPEN':
                # Quick-Start: Child open -> Parent G2 and Pump MUST open
                gates[trigger_id] = 'OPEN'
                gates['G2'] = 'OPEN'
                system_state['pump_status'] = 'ON'
                print(f"[LOGIC] Branch B Start: {trigger_id} opened -> G2/Pump started.")
            else:
                # Linkage Kill: Child close -> Parent G2 and Pump MUST close
                gates[trigger_id] = 'CLOSED'
                gates['G2'] = 'CLOSED'
                system_state['pump_status'] = 'OFF'
                for g in branch_b:
                    gates[g] = 'CLOSED'
                print(f"[LOGIC] Branch B Stop: {trigger_id} closed -> G2/Pump shutdown.")
        
        elif trigger_id == 'G1':
            gates['G1'] = action
            if action == 'OPEN':
                system_state['pump_status'] = 'ON'
            else:
                for g in branch_a:
                    gates[g] = 'CLOSED'
        elif trigger_id == 'G2':
            gates['G2'] = action
            if action == 'OPEN':
                system_state['pump_status'] = 'ON'
            else:
                for g in branch_b:
                    gates[g] = 'CLOSED'

def auto_control_gates():
    """Automatically open/close gates based on moisture levels."""
    any_opened = False
    moisture_dict = system_state['moisture']
    gates_dict = system_state['gates']
    
    for field, gate_id in FIELD_TO_GATE.items():
        moisture_val = moisture_dict.get(field, 100)
        field_label = f"Block {field.split('_')[1]}"
        if moisture_val < THRESHOLD_MOISTURE:
            # Auto-open: trigger logic via helper
            if gates_dict.get(gate_id) != 'OPEN':
                apply_system_logic('GATE', gate_id, 'OPEN')
                any_opened = True
                print(f"[AUTO] {gate_id} opened for {field_label} (moisture={moisture_val}%)")
                # Send SMS for this specific gate opening
                send_gate_open_sms(gate_id, field_label)
        else:
            # Moisture is OK - close via helper
            if gates_dict.get(gate_id) == 'OPEN':
                apply_system_logic('GATE', gate_id, 'CLOSED')
    return any_opened

@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'rakshitha' and request.form['password'] == 'password':
            session['logged_in'] = True
            session['username'] = request.form['username']  # Store username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    username = session.get('username', 'admin')
    return render_template('dashboard.html', username=username)

@app.route('/api/data', methods=['GET'])
def get_data():
    if 'logged_in' not in session and request.remote_addr != '127.0.0.1': 
        # Allow ESP32 or local access to see relay states
        pass 
    
    # Map system state to the 4 Relays used in user's ESP32 code
    gates = system_state['gates']
    resp = system_state.copy()
    resp['relay1'] = 1 if system_state['pump_status'] == 'ON' else 0
    resp['relay2'] = 1 if gates['G1'] == 'OPEN' else 0
    resp['relay3'] = 1 if gates['G2'] == 'OPEN' else 0
    resp['relay4'] = 1 if gates['G3'] == 'OPEN' else 0
    
    return jsonify(resp)

@app.route('/api/pump', methods=['POST'])
def control_pump():
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    action = data.get('action') # 'ON' or 'OFF'
    if action in ['ON', 'OFF']:
        apply_system_logic('PUMP', None, action)
        return jsonify({'success': True, 'pump_status': system_state['pump_status']})
    return jsonify({'success': False, 'error': 'Invalid action'}), 400

@app.route('/api/light', methods=['POST'])
def control_light():
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    action = data.get('action') # 'ON' or 'OFF'
    if action in ['ON', 'OFF']:
        system_state['light_status'] = action
        return jsonify({'success': True, 'light_status': system_state['light_status']})
    return jsonify({'success': False, 'error': 'Invalid action'}), 400

@app.route('/api/gate', methods=['POST'])
def control_gate():
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    gate_id = data.get('gate_id')
    action = data.get('action') # 'OPEN' or 'CLOSED'
    
    gates_dict = system_state['gates']
    if gate_id in gates_dict and action in ['OPEN', 'CLOSED']:
        apply_system_logic('GATE', gate_id, action)
        return jsonify({'success': True, 'gate_id': gate_id, 'status': gates_dict[gate_id]})
    return jsonify({'success': False, 'error': 'Invalid gate or action'}), 400

@app.route('/api/update', methods=['GET', 'POST'])
def update_data():
    # Fix: User's ESP32 code uses GET to check status, but this route was POST-only.
    if request.method == 'GET':
        return get_data()

    # This route is called by ESP32 via POST JSON
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update state from ESP32
    moisture_data = data.get('moisture', {})
    if isinstance(moisture_data, dict):
        for field, value in moisture_data.items():
            if field in system_state['moisture']:
                try:
                    system_state['moisture'][field] = int(value)
                except (ValueError, TypeError):
                    pass
                
    try:
        system_state['water_flow'] = float(data.get('water_flow', system_state['water_flow']))
    except (ValueError, TypeError):
        pass
    
    # --- Auto-gate control based on moisture levels ---
    auto_control_gates()
    
    # Evaluate Alerts globally based on any field being critically low
    low_fields = []
    moisture_dict = system_state['moisture']
    for k, v in moisture_dict.items():
        if isinstance(v, (int, float)) and v < THRESHOLD_MOISTURE:
            low_fields.append(f"Block {k.split('_')[1]}")

    low_moisture = len(low_fields) > 0

    system_state['alert'] = None
    if low_moisture:
        if system_state['pump_status'] == 'ON' and system_state['water_flow'] == 0:
            system_state['alert'] = 'PUMP_FAILURE'
        else:
            system_state['alert'] = 'LOW_MOISTURE'
            send_sms_alert(low_fields)
    elif system_state['pump_status'] == 'ON' and system_state['water_flow'] == 0:
        system_state['alert'] = 'PUMP_FAILURE'
            
    system_state['last_update'] = time.time()
    
    # Save to SQLite Database asynchronously/periodically (here done synchronous for simplicity)
    try:
        conn = get_db()
        m = system_state['moisture']
        g = system_state['gates']
        conn.execute('''
            INSERT INTO sensor_log (
                moisture_1, moisture_2, moisture_3, moisture_4, moisture_5, moisture_6,
                water_flow, pump_status, gate_1, gate_2, gate_3, gate_4, gate_5, gate_6, gate_7, gate_8
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            m['field_1'], m['field_2'], m['field_3'], m['field_4'], m['field_5'], m['field_6'],
            system_state['water_flow'], system_state['pump_status'],
            g['G1'], g['G2'], g['G3'], g['G4'], g['G5'], g['G6'], g['G7'], g['G8']
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

    # Response tells ESP32 the desired pump status and gates
    return jsonify({
        'success': True, 
        'pump_status': system_state['pump_status'],
        'light_status': system_state['light_status'],
        'gates': system_state['gates']
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db()
        # Get data from the last 7 days, limit to 100 points for chart performance
        cursor = conn.execute('''
            SELECT * FROM sensor_log 
            WHERE timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp ASC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        # Subsample if too many rows (e.g., take every Nth row)
        if len(rows) > 100:
            step = len(rows) // 100
            rows = rows[::step]
            
        history_data = {
            'labels': [row['timestamp'] for row in rows],
            'moisture_avg': [
                sum([row[f'moisture_{i}'] for i in range(1, 7)]) / 6 for row in rows
            ],
            'water_flow': [row['water_flow'] for row in rows]
        }
        return jsonify({'success': True, 'data': history_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
