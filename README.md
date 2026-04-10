<h1 align="center">KTStress</h1>
<em><h5 align="center">MHDDoS but with active support and updates!</h5></em>

<p align="center">Please Don't Attack websites without the owner's consent.</p>

## 🚀 Quick Start

### CLI Mode (Original)
```bash
python3 start.py <method> <url> <socks_type> <threads> <proxylist> <rpc> <duration>
```

### Web UI Mode (NEW!)
```bash
# Install dependencies
pip install -r requirements.txt

# Start the web UI
python3 ui.py

# Access the UI at http://localhost:5000
```

## 🎨 Web UI Features

- **Modern Dark Theme** - Beautiful gradient-based design with smooth animations
- **Real-time Statistics** - Live updates of requests, bytes sent, PPS, and BPS
- **Attack Configuration** - Easy-to-use form for configuring all attack parameters
- **Live Logs** - Real-time terminal output in the browser
- **Progress Tracking** - Visual progress bar showing attack duration
- **Method Selection** - Dropdown with all Layer 4 and Layer 7 methods
- **Responsive Design** - Works on desktop and mobile devices

## 📸 UI Preview

The web interface provides:
- Attack configuration panel with method selection, target input, threads, duration, proxy settings
- Live statistics dashboard showing requests sent, bytes sent, packets/sec, bytes/sec
- Real-time log terminal with color-coded log levels
- Start/Stop attack controls with visual status indicator

## 🛠️ Requirements

All dependencies are listed in `requirements.txt`:
- flask>=2.3.0 (Web framework)
- flask-socketio>=5.3.0 (Real-time communication)
- All original MHDDoS dependencies

Install with: `pip install -r requirements.txt`

## ⚙️ Usage Examples

### CLI Mode
```bash
# Layer 7 Attack
python3 start.py GET https://example.com 0 100 proxy.txt 50 60

# Layer 4 Attack  
python3 start.py TCP 192.168.1.1:80 100 60
```

### Web UI Mode
```bash
python3 ui.py
# Then open http://localhost:5000 in your browser
```

## 📋 Available Methods

### Layer 7 (HTTP/HTTPS)
GET, POST, CFB, BYPASS, OVH, STRESS, DYN, SLOW, HEAD, NULL, COOKIE, PPS, EVEN, GSB, DGB, AVB, CFBUAM, APACHE, XMLRPC, BOT, BOMB, DOWNLOADER, KILLER, TOR, RHEX, STOMP

### Layer 4 (TCP/UDP)
TCP, UDP, SYN, VSE, MINECRAFT, MCBOT, CONNECTION, CPS, FIVEM, FIVEM-TOKEN, TS3, MCPE, ICMP, OVH-UDP, MEM, NTP, DNS, ARD, CLDAP, CHAR, RDP

## ⚠️ Disclaimer

This tool is for educational and testing purposes only. Only use on targets you have explicit permission to test. The authors are not responsible for any misuse or damage caused by this tool.
