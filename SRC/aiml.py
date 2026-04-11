import random
import time

print("\nSMART IRRIGATION SYSTEM\n")

# -----------------------------
# GATE LIST
# -----------------------------

gates = ["G1","G2","G3","G4","G5","G6","G7","G8"]

# Gate states
gate_state = {g: False for g in gates}

# Pump state
pump_state = False

# -----------------------------
# GATE DEPENDENCIES
# -----------------------------

dependencies = {
    "G3":"G1",
    "G4":"G1",
    "G5":"G1",
    "G6":"G1",
    "G7":"G2",
    "G8":"G2"
}

# -----------------------------
# DISTANCE FROM PUMP (meters)
# -----------------------------

distance = {
    "G1":10,
    "G2":10,
    "G3":20,
    "G4":25,
    "G5":30,
    "G6":35,
    "G7":40,
    "G8":45
}

# -----------------------------
# SOIL MOISTURE INPUT
# -----------------------------

soil_moisture = {}

print("Enter soil moisture for gates (0-100)\n")

for g in gates:

    if g in ["G1","G2"]:
        soil_moisture[g] = 100
    else:
        m = float(input(f"{g} moisture: "))
        soil_moisture[g] = m

# -----------------------------
# WATER FLOW CALCULATION
# -----------------------------

def calculate_flow(gate):

    d = distance[gate]

    flow = max(2, 10 - (d*0.1))

    return round(flow,2)

# -----------------------------
# CHECK WATER NEED
# -----------------------------

def needs_water(m):

    return m < 50

# -----------------------------
# OPEN GATE
# -----------------------------

def open_gate(gate):

    global pump_state

    if gate in dependencies:

        main_gate = dependencies[gate]

        if not gate_state[main_gate]:

            gate_state[main_gate] = True
            print(main_gate,"opened (main pipeline)")

    if not gate_state[gate]:

        gate_state[gate] = True
        print(gate,"opened (field gate)")

    pump_state = True

# -----------------------------
# CLOSE GATE
# -----------------------------

def close_gate(gate):

    gate_state[gate] = False
    print(gate,"closed")

# -----------------------------
# IRRIGATION CONTROL
# -----------------------------

def irrigation():

    print("\nChecking irrigation needs...\n")

    for gate in gates:

        if gate in ["G1","G2"]:
            continue

        moisture = soil_moisture[gate]

        if needs_water(moisture):

            print("Water required at",gate)

            open_gate(gate)

# -----------------------------
# DASHBOARD
# -----------------------------

def dashboard():

    print("\n==========================")
    print("IRRIGATION DASHBOARD")
    print("==========================")

    pump_status = "ON" if pump_state else "OFF"

    print("\nPump Status:",pump_status)

    total_flow = 0

    for g in gates:

        status = "OPEN" if gate_state[g] else "CLOSED"

        print("\nGate:",g)
        print("Status:",status)

        if g not in ["G1","G2"] and gate_state[g]:

            flow = calculate_flow(g)

            print("Water Flow:",flow)
            print("Distance:",distance[g],"m")

            total_flow += flow

    print("\nTotal Water Flow:",round(total_flow,2))

    print("==========================")

# -----------------------------
# SOIL MOISTURE UPDATE
# -----------------------------

def update_moisture():

    for g in gates:

        if g in ["G1","G2"]:
            continue

        soil_moisture[g] += random.uniform(-3,2)

        soil_moisture[g] = max(0,min(100,soil_moisture[g]))

# -----------------------------
# PIPELINE MAP
# -----------------------------

def pipeline_map():

    print("\nPIPELINE LAYOUT\n")

    print("Well → Pump")
    print("      │")
    print("      ├── G1 → G3, G4, G5, G6")
    print("      │")
    print("      └── G2 → G7, G8")

# -----------------------------
# SYSTEM START
# -----------------------------

pipeline_map()

print("\nSystem Started...\n")

while True:

    irrigation()

    dashboard()

    update_moisture()

    time.sleep(5)