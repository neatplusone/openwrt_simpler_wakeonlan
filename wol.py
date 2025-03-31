import json
import os
import subprocess
import sys
from flask import Flask, request, jsonify, render_template_string
import threading
import webbrowser

app = Flask(__name__)

# pip install flask wakeonlan pyinstaller
# pyinstaller --onefile wol_server.py

# Replace the PHP executeCommand function with a Python implementation
def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return str(e)

# HTML template (same design as original)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake on LAN</title>
    <style>
        /* (c) neat8 2024 */
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            height: 100vh;
        }

        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            width: 100%;
            max-width: 1200px;
        }

        .device-card {
            background-color: #1e1e1e;
            border: 2px solid #333333;
            border-radius: 8px;
            padding: 20px;
            cursor: pointer;
            transition: background-color 0.3s, border-color 0.3s;
            text-align: center;
        }

        .device-card:hover {
            background-color: #333333;
            border-color: #555555;
        }

        .device-info {
            text-align: center;
        }

        .device-name {
            font-size: 1.5em;
            margin: 0;
            margin-bottom: 10px;
        }

        .device-mac, .device-ip, .device-description {
            font-size: 0.9em;
            margin: 5px 0;
            color: #cccccc;
        }

        h3 {margin:0px;}
        small {margin-top:8px;}

        .manual-wol {
            margin: 20px;
            text-align: center;
        }

        #mac-address-input {
            padding: 10px;
            font-size: 1em;
            width: 250px;
            margin-right: 10px;
            border-radius: 5px;
            border: 1px solid #555;
            background-color: #2c2c2c;
            color: #f0f0f0;
        }

        #wol-button {
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            border-radius: 5px;
            border: 1px solid #555;
            background-color: #404040;
            color: white;
            transition: background-color 0.2s ease;
        }

        #wol-button:hover {
            background-color: #b30000;
        }

        /* Adjustments for mobile */
        @media (max-width: 600px) {
            #mac-address-input {
                width: 80%;
                margin-bottom: 10px;
            }
            #wol-button {
                width: 80%;
            }
        }

        /* blur for privacy security or something...*/
        .blur {
            filter: blur(12px);
            transition: filter 0.3s ease-in-out;
        }
        .blur:hover {
            filter: blur(0px);
        }
    </style>
</head>
<body>
    <h3>Wake On LAN</h3>
    <div id="manual-wol" class="manual-wol">
        <input type="text" id="mac-address-input" placeholder="Enter MAC address">
        <button id="wol-button">Send Wake-on-LAN</button>
    </div>
    <div id="device-container" class="device-grid"><p style="text-align: center;">loading...</p></div>
    <small style="color: #1e1b1b;">&copy; neat8 2024</small>

    <script>
        // Function to create device cards
        function createDeviceCards(devices) {
            const container = document.getElementById('device-container');
            container.innerHTML = ''; // Clear the loading message or any existing content
            devices.forEach(device => {
                const deviceCard = document.createElement('div');
                deviceCard.className = 'device-card';
                deviceCard.onclick = () => wakeOnLan(device.mac_address);

                const deviceInfo = `
                    <div class="device-info">
                        <h2 class="device-name">${device.name}</h2>
                        <p class="device-mac blur">MAC: ${device.mac_address}</p>
                        ${device.status_ip ? `<p class="device-description blur">IP: ${device.status_ip}</p>` : ''}
                        ${device.description ? `<p class="device-description">${device.description}</p>` : ''}
                    </div>
                `;

                deviceCard.innerHTML = deviceInfo;
                container.appendChild(deviceCard);
            });
        }

        // Function to send Wake on LAN request
        function wakeOnLan(macAddress) {
            fetch('/wake', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mac: macAddress })
            })
            .then(response => response.text())
            .then(data => {
                alert(data);
            });
        }
        
        document.getElementById('wol-button').addEventListener('click', () => {
            const macAddress = document.getElementById('mac-address-input').value.trim();
            if (macAddress) {
                wakeOnLan(macAddress);
            } else {
                alert('Please enter a valid MAC address.');
            }
        });
        
        // Fetch the devices.json and create device cards
        document.addEventListener('DOMContentLoaded', () => {
            fetch('/devices.json') 
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                createDeviceCards(data);
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/devices.json')
def devices_json():
    # Read devices.json from the current working directory
    try:
        with open('devices.json', 'r') as f:
            devices = json.load(f)
        return jsonify(devices)
    except FileNotFoundError:
        # Return an empty array if file doesn't exist
        return jsonify([])
    except json.JSONDecodeError:
        # Return an empty array if JSON is invalid
        return jsonify([])

@app.route('/wake', methods=['POST'])
def wake_on_lan():
    data = request.json
    if 'mac' in data:
        mac = data['mac']
        
        # Determine the platform-specific WOL command
        if sys.platform.startswith('win'):
            # For Windows, we'll use a Python implementation
            from wakeonlan import send_magic_packet
            try:
                send_magic_packet(mac)
                return f"Wake on LAN signal sent to MAC: {mac}"
            except Exception as e:
                return f"Error sending WOL packet: {str(e)}"
        else:
            # For Linux/Mac, use etherwake or similar command
            # Adjust the command based on your system's tools
            # This assumes etherwake is installed on Linux systems
            if sys.platform.startswith('linux'):
                cmd = f"sudo etherwake -i br-lan {mac}"
            else:  # macOS
                cmd = f"wakeonlan {mac}"
                
            output = execute_command(cmd)
            return f"{output} - Wake on LAN signal sent to MAC: {mac}"
    else:
        return "MAC address not provided."

def open_browser(port):
    """Open the browser after a short delay"""
    webbrowser.open(f'http://localhost:{port}/')

def main():
    print("Starting Wake on LAN Server...")
    print("Reading devices from devices.json in the current directory")
    
    # Check for a devices.json file and create a sample one if it doesn't exist
    if not os.path.exists('devices.json'):
        print("devices.json not found. Creating a sample file...")
        sample_devices = [
            {
                "name": "Example Device",
                "mac_address": "00:11:22:33:44:55",
                "description": "Sample device - edit devices.json to customize"
            }
        ]
        with open('devices.json', 'w') as f:
            json.dump(sample_devices, f, indent=4)
        print("Sample devices.json created. Please edit it with your actual devices.")
    
    # Choose a port (default: 5000)
    port = 5000
    
    # Open browser automatically after server starts
    threading.Timer(1.5, open_browser, args=[port]).start()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()