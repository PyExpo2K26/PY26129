let currentData = null;
let moistureChartInstance = null;
let flowChartInstance = null;

// --- Safety Helpers ---
function safeSetHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}
function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}
function safeSetClass(id, className, add = true) {
    const el = document.getElementById(id);
    if (el) {
        if (add) el.classList.add(className);
        else el.classList.remove(className);
    }
}
function safeSetAttr(id, attr, value) {
    const el = document.getElementById(id);
    if (el) el.setAttribute(attr, value);
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchData();
    fetchHistory();
    // Fetch live data every 3 seconds
    setInterval(fetchData, 3000);
    // Fetch history every 1 minute
    setInterval(fetchHistory, 60000);
});

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        const data = await response.json();
        updateDashboard(data);
        
    } catch (error) {
        console.error('Error fetching live data:', error);
        // Only show connection error if it's a real fetch error, 
        // not a JS crash (though it's hard to distinguish here without more logic)
        showConnectionError();
    }
}

async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                updateCharts(result.data);
            }
        }
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

function updateDashboard(data) {
    if (!data) return;
    currentData = data;
    
    try {
        // --- Update Global Stats ---
        safeSetText('flow-value', `${data.water_flow} L/min`);
        
        if (data.pump_status === 'ON') {
            safeSetHtml('pump-value', '<span class="status-success pulse">ON</span>');
            safeSetClass('pump-icon', 'pulse', true);
            safeSetAttr('svg-pump', 'fill', '#10b981'); // Green pump
        } else {
            safeSetHtml('pump-value', '<span class="status-muted">OFF</span>');
            safeSetClass('pump-icon', 'pulse', false);
            safeSetAttr('svg-pump', 'fill', '#334155'); // Grey pump
        }
        
        // --- Update Light Status ---
        if (data.light_status === 'ON') {
            safeSetHtml('light-value', '<span class="status-success pulse">ON</span>');
        } else {
            safeSetHtml('light-value', '<span class="status-muted">OFF</span>');
        }
    } catch (e) { console.error("Error updating stats:", e); }

    // --- Update Fields (1 to 6) ---
    const FIELD_TO_GATE = {
        'field_1': 'G3', 'field_2': 'G4', 'field_3': 'G5',
        'field_4': 'G6', 'field_5': 'G7', 'field_6': 'G8'
    };
    const THRESHOLD = 30;
    const fieldSuggestions = [];

    for (let i = 1; i <= 6; i++) {
        const fieldKey = `field_${i}`;
        const moistureValue = data.moisture[fieldKey];
        const svgText = document.getElementById(`svg-moisture-${i}`);
        const svgRect = document.getElementById(`rect-field-${i}`);
        
        if (svgText && svgRect) {
            // Show moisture % clearly inside the block
            safeSetText(`svg-moisture-${i}`, `${moistureValue}%`);
            // Color logic
            svgRect.classList.remove('field-low', 'field-good', 'field-dry');
            if (moistureValue < 15) {
                svgRect.classList.add('field-dry');
            } else if (moistureValue < THRESHOLD) {
                svgRect.classList.add('field-low');
            } else {
                svgRect.classList.add('field-good');
            }
        }

        // Build suggestion data
        const gate = FIELD_TO_GATE[fieldKey];
        const gateStatus = data.gates[gate];
        fieldSuggestions.push({
            block: `Block ${i}`,
            gate: gate,
            moisture: moistureValue,
            needsWater: moistureValue < THRESHOLD,
            autoIrrigating: moistureValue < THRESHOLD && gateStatus === 'OPEN'
        });
    }

    updateSuggestions(fieldSuggestions, data.pump_status);

    // --- Update Gates (G1 to G8) ---
    for (let i = 1; i <= 8; i++) {
        const gateKey = `G${i}`;
        const gateStatus = data.gates[gateKey];
        
        // Update Side Panel Buttons
        const btn = document.querySelector(`#ctrl-${gateKey} button`);
        if (btn) {
            btn.textContent = gateStatus;
            btn.className = `toggle-btn ${gateStatus === 'OPEN' ? 'open' : 'closed'}`;
        }
        
        // Update SVG Valves
        safeSetClass(`svg-gate-${i}`, 'gate-open', gateStatus === 'OPEN');
        safeSetClass(`svg-gate-${i}`, 'gate-closed', gateStatus !== 'OPEN');
        const svgGate = document.getElementById(`svg-gate-${i}`);
        if (svgGate) {
             svgGate.setAttribute('class', `svg-gate ${gateStatus === 'OPEN' ? 'gate-open' : 'gate-closed'}`);
        }
    }

    // --- Update Water Flow Animation ---
    const flowLines = document.getElementById('flow-lines');
    if (!flowLines) {
        updateAlertBanner(data.alert);
        document.querySelectorAll('.stat-value').forEach(el => el.style.opacity = '1');
        return;
    }
    
    // Core Pipes
    const flowPump = document.getElementById('flow-pump');
    const flowBotMain = document.getElementById('flow-bottom-main');
    const flowBotV4 = document.getElementById('flow-bottom-v4');
    const flowBotV3 = document.getElementById('flow-bottom-v3');
    const flowBotV2 = document.getElementById('flow-bottom-v2');
    const flowMid = document.getElementById('flow-middle');
    
    // Gate Drop Pipes
    const flowG3 = document.getElementById('flow-G3');
    const flowG4 = document.getElementById('flow-G4');
    const flowG5 = document.getElementById('flow-G5');
    const flowG6 = document.getElementById('flow-G6');
    const flowG7 = document.getElementById('flow-G7');
    const flowG8 = document.getElementById('flow-G8');

    // Reset opacity
    [flowPump, flowBotMain, flowBotV4, flowBotV3, flowBotV2, flowMid, flowG3, flowG4, flowG5, flowG6, flowG7, flowG8].forEach(line => {
        if(line) line.style.opacity = '0';
    });

    if (data.pump_status === 'ON') {
        flowLines.classList.remove('flow-hidden');
        
        // Pump is ON -> Main Horizontal Pipe is active
        if(flowPump) flowPump.style.opacity = '1';

        // G1 controls the rest of the bottom main line
        if (data.gates['G1'] === 'OPEN') {
            if(flowBotMain) flowBotMain.style.opacity = '1';
            
            // G5 draws directly from the bottom main line
            if (data.gates['G5'] === 'OPEN' && flowG5) flowG5.style.opacity = '1';
            if (data.gates['G4'] === 'OPEN' && flowG4) flowG4.style.opacity = '1';
            if (data.gates['G3'] === 'OPEN' && flowG3) flowG3.style.opacity = '1';

            // G2 controls the vertical risers and middle pipeline
            if (data.gates['G2'] === 'OPEN') {
                if(flowBotV4) flowBotV4.style.opacity = '1';
                if(flowBotV3) flowBotV3.style.opacity = '1';
                if(flowBotV2) flowBotV2.style.opacity = '1';
                if(flowMid) flowMid.style.opacity = '1';

                // Top blocks draw from the middle line
                if (data.gates['G6'] === 'OPEN' && flowG6) flowG6.style.opacity = '1';
                if (data.gates['G7'] === 'OPEN' && flowG7) flowG7.style.opacity = '1';
                if (data.gates['G8'] === 'OPEN' && flowG8) flowG8.style.opacity = '1';
            }
        }
    } else {
        flowLines.classList.add('flow-hidden');
    }

    // Update Alert Banner
    updateAlertBanner(data.alert);
    
    // Clear connection error dimming if it was present
    document.querySelectorAll('.stat-value').forEach(el => el.style.opacity = '1');
}


function updateSuggestions(fieldSuggestions, pumpStatus) {
    const list = document.getElementById('suggestions-list');
    if (!list) return;

    safeSetHtml('suggestions-list', fieldSuggestions.map(f => {
        let statusIcon, statusClass, suggestion;

        if (f.moisture >= 60) {
            statusIcon = '✅'; statusClass = 'sug-good';
            suggestion = 'Moisture OK — No action needed';
        } else if (f.moisture >= 30) {
            statusIcon = '🟡'; statusClass = 'sug-warn';
            suggestion = 'Monitor closely';
        } else if (f.autoIrrigating) {
            statusIcon = '💧'; statusClass = 'sug-auto';
            suggestion = `Auto-irrigating via ${f.gate}`;
        } else {
            statusIcon = '🔴'; statusClass = 'sug-dry';
            suggestion = `Needs water! Gate ${f.gate} should open`;
        }

        return `
            <div class="sug-item ${statusClass}">
                <span class="sug-icon">${statusIcon}</span>
                <span class="sug-block">${f.block}</span>
                <span class="sug-moisture">${f.moisture}%</span>
                <div class="sug-bar-wrap"><div class="sug-bar" style="width:${Math.min(f.moisture,100)}%; background:${f.moisture < 30 ? '#ef4444' : f.moisture < 60 ? '#f59e0b' : '#22c55e'}"></div></div>
                <span class="sug-text">${suggestion}</span>
            </div>`;
    }).join(''));
}

function updateAlertBanner(alertType) {
    const banner = document.getElementById('alert-banner');
    if (!banner) return; // Silent fail if banner missing

    if (!alertType) {
        banner.className = 'alert-banner hidden';
        return;
    }
    
    banner.classList.remove('hidden');
    if (alertType === 'PUMP_FAILURE') {
        banner.className = 'alert-banner alert-danger pulse';
        banner.innerHTML = '⚠️ <strong>CRITICAL:</strong> Water flow not detected while pump is running! Check water supply.';
    } else if (alertType === 'LOW_MOISTURE') {
        banner.className = 'alert-banner alert-warning';
        banner.innerHTML = '⚠️ <strong>WARNING:</strong> One or more fields have critically low soil moisture.';
    }
}

function showConnectionError() {
    const banner = document.getElementById('alert-banner');
    banner.className = 'alert-banner alert-danger';
    banner.innerHTML = '🔌 <strong>CONNECTION ERROR:</strong> Cannot reach the server. Trying to reconnect...';
    banner.classList.remove('hidden');
    // Dim values
    document.querySelectorAll('.stat-value').forEach(el => el.style.opacity = '0.5');
}

// --- Control APIs ---

async function controlPump(action) {
    try {
        const response = await fetch('/api/pump', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        if (response.ok) {
            setTimeout(fetchData, 300); // Immediate refresh
        }
    } catch (error) {
        console.error('Error controlling pump:', error);
    }
}

async function controlLight(action) {
    try {
        const response = await fetch('/api/light', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        if (response.ok) {
            setTimeout(fetchData, 300); // Immediate refresh
        }
    } catch (error) {
        console.error('Error controlling light:', error);
    }
}

async function toggleGate(gateId) {
    if (!currentData) return;
    
    // Determine new state (toggle)
    const currentState = currentData.gates[gateId];
    const newState = currentState === 'OPEN' ? 'CLOSED' : 'OPEN';
    
    try {
        const response = await fetch('/api/gate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gate_id: gateId, action: newState })
        });
        
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        if (response.ok) {
            setTimeout(fetchData, 200); // Immediate refresh to show animation changes
        }
    } catch (error) {
        console.error(`Error controlling gate ${gateId}:`, error);
    }
}

// --- Chart.js Setup ---

function formatTimeLabel(isoString) {
    const date = new Date(isoString);
    return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
}

function initCharts() {
    // Common Chart Options
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4 } // Smooth curves
        },
        plugins: {
            legend: {
                labels: { font: { family: "'Outfit', sans-serif" } }
            }
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: { display: false } // Hide x-axis labels to reduce clutter
            },
            y: {
                beginAtZero: true,
            }
        }
    };

    // Moisture Chart
    const ctxMoisture = document.getElementById('moistureChart').getContext('2d');
    moistureChartInstance = new Chart(ctxMoisture, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Soil Moisture (%)',
                data: [],
                borderColor: '#16a34a', // Green
                backgroundColor: 'rgba(22, 163, 74, 0.1)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: { ...chartOptions }
    });

    // Flow Chart
    const ctxFlow = document.getElementById('flowChart').getContext('2d');
    flowChartInstance = new Chart(ctxFlow, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Water Flow Rate (L/min)',
                data: [],
                borderColor: '#0ea5e9', // Blue
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: { ...chartOptions }
    });
}

function updateCharts(historyData) {
    if (!moistureChartInstance || !flowChartInstance || !historyData) return;

    const labels = historyData.labels.map(formatTimeLabel);

    // Update Moisture Chart
    moistureChartInstance.data.labels = labels;
    moistureChartInstance.data.datasets[0].data = historyData.moisture_avg;
    moistureChartInstance.update();

    // Update Flow Chart
    flowChartInstance.data.labels = labels;
    flowChartInstance.data.datasets[0].data = historyData.water_flow;
    flowChartInstance.update();
}
