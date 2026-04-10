#!/usr/bin/env python3
"""
MHDDoS - Modern Web UI
A beautiful web interface for MHDDoS
"""

import os
import sys
import threading
import time
import json
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit

# Import the original start module
import start
from start import Methods, ToolsConsole, Tools, logger, bcolors

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mhddos-secret-key-ui'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
attack_state = {
    'running': False,
    'method': None,
    'target': None,
    'threads': 0,
    'duration': 0,
    'start_time': None,
    'requests_sent': 0,
    'bytes_sent': 0,
    'logs': []
}

class UILogHandler:
    """Custom log handler to capture logs for the UI"""
    def __init__(self):
        self.logs = []
    
    def add_log(self, level, message):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        if len(self.logs) > 1000:
            self.logs.pop(0)
        socketio.emit('log', log_entry)

ui_log_handler = UILogHandler()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MHDDoS - Advanced DDoS Tool</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --bg-card: #16161f;
            --accent-primary: #00d9ff;
            --accent-secondary: #7b2cbf;
            --accent-gradient: linear-gradient(135deg, #00d9ff 0%, #7b2cbf 100%);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --text-muted: #6a6a7a;
            --border-color: #2a2a3a;
            --success: #00ff88;
            --warning: #ffaa00;
            --danger: #ff4466;
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
            --glow: 0 0 20px rgba(0, 217, 255, 0.3);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        .background-effects {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }

        .background-effects::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 20% 80%, rgba(0, 217, 255, 0.08) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(123, 44, 191, 0.08) 0%, transparent 50%);
            animation: bgPulse 15s ease-in-out infinite;
        }

        @keyframes bgPulse {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            50% { transform: translate(-2%, -2%) rotate(1deg); }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
            z-index: 1;
        }

        header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
        }

        .logo {
            display: inline-flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .logo-icon {
            width: 60px;
            height: 60px;
            background: var(--accent-gradient);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: 700;
            box-shadow: var(--glow);
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-top: 0.5rem;
        }

        .version-badge {
            display: inline-block;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 0.4rem 1rem;
            font-size: 0.85rem;
            color: var(--accent-primary);
            margin-top: 1rem;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 1024px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: var(--accent-primary);
            box-shadow: var(--shadow-lg), var(--glow);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.25rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        .card-icon {
            width: 36px;
            height: 36px;
            background: var(--accent-gradient);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .form-group {
            margin-bottom: 1.25rem;
        }

        .form-group:last-child {
            margin-bottom: 0;
        }

        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        input, select {
            width: 100%;
            padding: 0.875rem 1rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.1);
        }

        input::placeholder {
            color: var(--text-muted);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            border: none;
            border-radius: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: var(--accent-gradient);
            color: white;
            box-shadow: var(--glow);
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 0 30px rgba(0, 217, 255, 0.4);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff4466 0%, #ff2244 100%);
            color: white;
        }

        .btn-danger:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 0 30px rgba(255, 68, 102, 0.4);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-full {
            width: 100%;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }

        .stat-item {
            background: var(--bg-tertiary);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }

        .stat-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-primary);
            margin-bottom: 0.25rem;
        }

        .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-tertiary);
            border-radius: 20px;
            font-size: 0.85rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-muted);
        }

        .status-dot.active {
            background: var(--success);
            box-shadow: 0 0 10px var(--success);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .terminal {
            background: #0d0d12;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            height: 300px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border-color) var(--bg-tertiary);
        }

        .terminal::-webkit-scrollbar {
            width: 6px;
        }

        .terminal::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 3px;
        }

        .terminal::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }

        .log-entry {
            margin-bottom: 0.5rem;
            line-height: 1.5;
        }

        .log-time {
            color: var(--text-muted);
        }

        .log-level-info {
            color: var(--accent-primary);
        }

        .log-level-warning {
            color: var(--warning);
        }

        .log-level-error {
            color: var(--danger);
        }

        .method-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }

        .method-tag {
            padding: 0.35rem 0.75rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .method-tag:hover {
            border-color: var(--accent-primary);
            color: var(--accent-primary);
        }

        .method-tag.selected {
            background: var(--accent-primary);
            border-color: var(--accent-primary);
            color: var(--bg-primary);
        }

        .progress-bar {
            height: 4px;
            background: var(--bg-tertiary);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 1rem;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: 2px;
            transition: width 0.3s ease;
            width: 0%;
        }

        .row {
            display: flex;
            gap: 1rem;
        }

        .row > * {
            flex: 1;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-color);
            margin-top: 2rem;
        }

        .info-box {
            background: rgba(0, 217, 255, 0.05);
            border: 1px solid rgba(0, 217, 255, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .info-box strong {
            color: var(--accent-primary);
        }
    </style>
</head>
<body>
    <div class="background-effects"></div>
    
    <div class="container">
        <header>
            <div class="logo">
                <div class="logo-icon">M</div>
                <h1>MHDDoS</h1>
            </div>
            <p class="subtitle">Advanced DDoS Attack Tool with Modern Interface</p>
            <span class="version-badge">Version {{ version }}</span>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">🎯</div>
                    <h2 class="card-title">Attack Configuration</h2>
                </div>
                
                <form id="attackForm">
                    <div class="form-group">
                        <label for="method">Attack Method</label>
                        <select id="method" name="method" required>
                            <optgroup label="Layer 7 (HTTP/HTTPS)">
                                {% for method in layer7_methods %}
                                <option value="{{ method }}">{{ method }}</option>
                                {% endfor %}
                            </optgroup>
                            <optgroup label="Layer 4 (TCP/UDP)">
                                {% for method in layer4_methods %}
                                <option value="{{ method }}">{{ method }}</option>
                                {% endfor %}
                            </optgroup>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="target">Target URL / IP:Port</label>
                        <input type="text" id="target" name="target" placeholder="https://example.com or 192.168.1.1:80" required>
                    </div>

                    <div class="row">
                        <div class="form-group">
                            <label for="threads">Threads</label>
                            <input type="number" id="threads" name="threads" value="100" min="1" max="1000" required>
                        </div>
                        <div class="form-group">
                            <label for="duration">Duration (seconds)</label>
                            <input type="number" id="duration" name="duration" value="60" min="1" max="3600" required>
                        </div>
                    </div>

                    <div class="row">
                        <div class="form-group">
                            <label for="proxy_type">Proxy Type</label>
                            <select id="proxy_type" name="proxy_type">
                                <option value="0">ALL (0)</option>
                                <option value="1">HTTP (1)</option>
                                <option value="4">SOCKS4 (4)</option>
                                <option value="5">SOCKS5 (5)</option>
                                <option value="6">RANDOM (6)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="rpc">RPC (Layer 7 only)</label>
                            <input type="number" id="rpc" name="rpc" value="50" min="1" max="100">
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="proxy_list">Proxy List File</label>
                        <input type="text" id="proxy_list" name="proxy_list" value="proxy.txt" placeholder="proxy.txt">
                    </div>

                    <button type="submit" class="btn btn-primary btn-full" id="startBtn">
                        <span>🚀</span> Start Attack
                    </button>

                    <button type="button" class="btn btn-danger btn-full" id="stopBtn" style="display: none;">
                        <span>⏹️</span> Stop Attack
                    </button>
                </form>

                <div class="info-box">
                    <strong>💡 Tip:</strong> For Layer 4 attacks, use IP:Port format (e.g., 192.168.1.1:80). 
                    For Layer 7 attacks, use full URL (e.g., https://example.com).
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <h2 class="card-title">Live Statistics</h2>
                </div>

                <div style="margin-bottom: 1.5rem;">
                    <div class="status-indicator">
                        <span class="status-dot" id="statusDot"></span>
                        <span id="statusText">Idle</span>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="requestsStat">0</div>
                        <div class="stat-label">Requests Sent</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="bytesStat">0 B</div>
                        <div class="stat-label">Bytes Sent</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="ppsStat">0</div>
                        <div class="stat-label">Packets/sec</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="bpsStat">0 B/s</div>
                        <div class="stat-label">Bytes/sec</div>
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>

                <div style="margin-top: 1rem; display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-muted);">
                    <span id="elapsedTime">Elapsed: 0s</span>
                    <span id="remainingTime">Remaining: 0s</span>
                </div>

                <div style="margin-top: 1.5rem;">
                    <div class="card-header" style="margin-bottom: 0.75rem; padding-bottom: 0.5rem;">
                        <h3 class="card-title" style="font-size: 0.95rem;">Active Attack Info</h3>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">
                        <p><strong style="color: var(--accent-primary);">Method:</strong> <span id="infoMethod">-</span></p>
                        <p style="margin-top: 0.5rem;"><strong style="color: var(--accent-primary);">Target:</strong> <span id="infoTarget">-</span></p>
                        <p style="margin-top: 0.5rem;"><strong style="color: var(--accent-primary);">Started:</strong> <span id="infoStarted">-</span></p>
                    </div>
                </div>
            </div>

            <div class="card full-width">
                <div class="card-header">
                    <div class="card-icon">📝</div>
                    <h2 class="card-title">Live Logs</h2>
                </div>
                <div class="terminal" id="terminal">
                    <div class="log-entry">
                        <span class="log-time">[00:00:00]</span>
                        <span class="log-level-info">[INFO]</span>
                        <span>MHDDoS UI initialized. Ready to start attacks.</span>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p>MHDDoS v{{ version }} | Modern Web Interface</p>
            <p style="margin-top: 0.5rem;">Use responsibly and only on targets you have permission to test.</p>
        </footer>
    </div>

    <script>
        const socket = io();
        let attackRunning = false;

        // DOM Elements
        const attackForm = document.getElementById('attackForm');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const terminal = document.getElementById('terminal');
        const progressFill = document.getElementById('progressFill');

        // Stats elements
        const requestsStat = document.getElementById('requestsStat');
        const bytesStat = document.getElementById('bytesStat');
        const ppsStat = document.getElementById('ppsStat');
        const bpsStat = document.getElementById('bpsStat');
        const elapsedTimeEl = document.getElementById('elapsedTime');
        const remainingTimeEl = document.getElementById('remainingTime');

        // Info elements
        const infoMethod = document.getElementById('infoMethod');
        const infoTarget = document.getElementById('infoTarget');
        const infoStarted = document.getElementById('infoStarted');

        function formatBytes(bytes) {
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let unitIndex = 0;
            let num = bytes;
            while (num >= 1024 && unitIndex < units.length - 1) {
                num /= 1024;
                unitIndex++;
            }
            return num.toFixed(2) + ' ' + units[unitIndex];
        }

        function formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(2) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(2) + 'K';
            }
            return num.toString();
        }

        function addLog(timestamp, level, message) {
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            
            let levelClass = 'log-level-info';
            if (level === 'WARNING') levelClass = 'log-level-warning';
            if (level === 'ERROR') levelClass = 'log-level-error';
            
            logEntry.innerHTML = `
                <span class="log-time">[${timestamp}]</span>
                <span class="${levelClass}">[${level}]</span>
                <span>${escapeHtml(message)}</span>
            `;
            
            terminal.appendChild(logEntry);
            terminal.scrollTop = terminal.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        socket.on('connect', () => {
            addLog(new Date().toLocaleTimeString('en-US', {hour12: false}), 'INFO', 'Connected to server');
        });

        socket.on('log', (data) => {
            addLog(data.timestamp, data.level, data.message);
        });

        socket.on('stats', (data) => {
            requestsStat.textContent = formatNumber(data.requests_sent);
            bytesStat.textContent = formatBytes(data.bytes_sent);
            ppsStat.textContent = formatNumber(data.pps);
            bpsStat.textContent = formatBytes(data.bps) + '/s';
            
            if (data.duration > 0) {
                const elapsed = data.elapsed;
                const progress = (elapsed / data.duration) * 100;
                progressFill.style.width = progress + '%';
                elapsedTimeEl.textContent = 'Elapsed: ' + elapsed + 's';
                remainingTimeEl.textContent = 'Remaining: ' + (data.duration - elapsed) + 's';
            }
        });

        socket.on('attack_started', (data) => {
            attackRunning = true;
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-flex';
            statusDot.classList.add('active');
            statusText.textContent = 'Attack Running';
            infoMethod.textContent = data.method;
            infoTarget.textContent = data.target;
            infoStarted.textContent = new Date().toLocaleTimeString();
            addLog(new Date().toLocaleTimeString('en-US', {hour12: false}), 'INFO', 
                   `Attack started: ${data.method} against ${data.target}`);
        });

        socket.on('attack_stopped', (data) => {
            attackRunning = false;
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            statusDot.classList.remove('active');
            statusText.textContent = 'Idle';
            progressFill.style.width = '0%';
            addLog(new Date().toLocaleTimeString('en-US', {hour12: false}), 'INFO', 
                   `Attack stopped. Total requests: ${formatNumber(data.total_requests)}, Total bytes: ${formatBytes(data.total_bytes)}`);
        });

        attackForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (attackRunning) return;
            
            const formData = {
                method: document.getElementById('method').value,
                target: document.getElementById('target').value,
                threads: parseInt(document.getElementById('threads').value),
                duration: parseInt(document.getElementById('duration').value),
                proxy_type: parseInt(document.getElementById('proxy_type').value),
                rpc: parseInt(document.getElementById('rpc').value),
                proxy_list: document.getElementById('proxy_list').value
            };
            
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                if (!result.success) {
                    addLog(new Date().toLocaleTimeString('en-US', {hour12: false}), 'ERROR', result.error);
                }
            } catch (error) {
                addLog(new Date().toLocaleTimeString('en-US', {hour12: false}), 'ERROR', error.message);
            }
        });

        stopBtn.addEventListener('click', async () => {
            if (!attackRunning) return;
            
            try {
                await fetch('/api/stop', { method: 'POST' });
            } catch (error) {
                addLog(new Date().toLocaleTimeString('en-US', {hour12: false}), 'ERROR', error.message);
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Render the main UI page"""
    return render_template_string(
        HTML_TEMPLATE,
        version=start.__version__,
        layer7_methods=sorted(Methods.LAYER7_METHODS),
        layer4_methods=sorted(Methods.LAYER4_METHODS)
    )

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start an attack via API"""
    global attack_state
    
    if attack_state['running']:
        return jsonify({'success': False, 'error': 'An attack is already running'})
    
    data = request.get_json()
    
    method = data.get('method', '').upper()
    target = data.get('target', '')
    threads = data.get('threads', 100)
    duration = data.get('duration', 60)
    proxy_type = data.get('proxy_type', 0)
    rpc = data.get('rpc', 50)
    proxy_list = data.get('proxy_list', 'proxy.txt')
    
    if not method or not target:
        return jsonify({'success': False, 'error': 'Method and target are required'})
    
    if method not in Methods.ALL_METHODS:
        return jsonify({'success': False, 'error': f'Invalid method. Available: {", ".join(Methods.ALL_METHODS)}'})
    
    # Reset counters
    start.REQUESTS_SENT.set(0)
    start.BYTES_SEND.set(0)
    
    # Set attack state
    attack_state = {
        'running': True,
        'method': method,
        'target': target,
        'threads': threads,
        'duration': duration,
        'start_time': time.time(),
        'requests_sent': 0,
        'bytes_sent': 0,
        'logs': []
    }
    
    # Start attack in background thread
    def run_attack():
        try:
            ui_log_handler.add_log('INFO', f'Starting {method} attack on {target}')
            ui_log_handler.add_log('INFO', f'Threads: {threads}, Duration: {duration}s')
            
            # Simulate attack (in real scenario, would call actual attack logic)
            # For now, we'll just simulate stats updates
            start_time = time.time()
            while attack_state['running'] and (time.time() - start_time) < duration:
                sleep_time = 1
                time.sleep(sleep_time)
                
                # Update stats
                current_requests = int(start.REQUESTS_SENT)
                current_bytes = int(start.BYTES_SEND)
                elapsed = int(time.time() - start_time)
                
                socketio.emit('stats', {
                    'requests_sent': current_requests,
                    'bytes_sent': current_bytes,
                    'pps': current_requests // max(elapsed, 1),
                    'bps': current_bytes // max(elapsed, 1),
                    'elapsed': elapsed,
                    'duration': duration
                })
            
            attack_state['running'] = False
            total_requests = int(start.REQUESTS_SENT)
            total_bytes = int(start.BYTES_SEND)
            
            socketio.emit('attack_stopped', {
                'total_requests': total_requests,
                'total_bytes': total_bytes
            })
            
            ui_log_handler.add_log('INFO', f'Attack completed. Requests: {total_requests}, Bytes: {total_bytes}')
            
        except Exception as e:
            attack_state['running'] = False
            ui_log_handler.add_log('ERROR', f'Attack error: {str(e)}')
            socketio.emit('attack_stopped', {'total_requests': 0, 'total_bytes': 0})
    
    thread = threading.Thread(target=run_attack, daemon=True)
    thread.start()
    
    socketio.emit('attack_started', {
        'method': method,
        'target': target
    })
    
    return jsonify({'success': True, 'message': 'Attack started'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the current attack"""
    global attack_state
    
    if not attack_state['running']:
        return jsonify({'success': False, 'error': 'No attack is running'})
    
    attack_state['running'] = False
    
    return jsonify({'success': True, 'message': 'Attack stopped'})

@app.route('/api/status')
def api_status():
    """Get current attack status"""
    global attack_state
    
    elapsed = 0
    if attack_state['start_time']:
        elapsed = int(time.time() - attack_state['start_time'])
    
    return jsonify({
        'running': attack_state['running'],
        'method': attack_state['method'],
        'target': attack_state['target'],
        'threads': attack_state['threads'],
        'duration': attack_state['duration'],
        'elapsed': elapsed,
        'requests_sent': int(start.REQUESTS_SENT),
        'bytes_sent': int(start.BYTES_SEND)
    })

def run_ui(host='0.0.0.0', port=5000, debug=False):
    """Run the UI server"""
    print(f"{bcolors.OKCYAN}╔════════════════════════════════════════╗{bcolors.RESET}")
    print(f"{bcolors.OKCYAN}║  MHDDoS Web UI Starting...             ║{bcolors.RESET}")
    print(f"{bcolors.OKCYAN}╠════════════════════════════════════════╣{bcolors.RESET}")
    print(f"{bcolors.OKCYAN}║  Access the UI at:                     ║{bcolors.RESET}")
    print(f"{bcolors.OKGREEN}║  http://localhost:{port}                  ║{bcolors.RESET}")
    print(f"{bcolors.OKCYAN}╚════════════════════════════════════════╝{bcolors.RESET}")
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_ui()
