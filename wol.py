import json
import os
import subprocess
import sys
import logging
import argparse
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import threading
import webbrowser

# Configure argument parser
def parse_arguments():
    parser = argparse.ArgumentParser(description='Wake-on-LAN Web Server')
    parser.add_argument('-p', '--port', type=int, default=5000,
                        help='Port to run the server on (default: 5000)')
    parser.add_argument('-i', '--ip', type=str, default='0.0.0.0',
                        help='IP address to bind the server to (default: 0.0.0.0)')
    parser.add_argument('-d', '--directory', type=str, default=None,
                        help='Directory to look for devices.json and store logs (default: current directory)')
    parser.add_argument('-l', '--logging', action='store_true',
                        help='Enable detailed logging')
    parser.add_argument('--no-browser', action='store_true',
                        help='Do not automatically open browser')
    return parser.parse_args()

# Set up logger
def setup_logging(log_directory, enabled):
    if not enabled:
        return
    
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    log_file = os.path.join(log_directory, f'wol_server_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    logging.info("Logging initialized")

app = Flask(__name__)

# pip install flask wakeonlan pyinstaller
# pyinstaller --onefile wol_server.py

# Global variables
log_enabled = False
working_directory = os.getcwd()

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
    if log_enabled:
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        logging.info(f"Page visit - IP: {client_ip}, User-Agent: {user_agent}")
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/devices.json')
def devices_json():
    # Read devices.json from the configured directory
    json_path = os.path.join(working_directory, 'devices.json')
    try:
        with open(json_path, 'r') as f:
            devices = json.load(f)
        
        if log_enabled:
            logging.info(f"Loaded {len(devices)} devices from {json_path}")
        
        return jsonify(devices)
    except FileNotFoundError:
        if log_enabled:
            logging.warning(f"devices.json not found at {json_path}")
        # Return an empty array if file doesn't exist
        return jsonify([])
    except json.JSONDecodeError:
        if log_enabled:
            logging.error(f"Invalid JSON in devices.json at {json_path}")
        # Return an empty array if JSON is invalid
        return jsonify([])

@app.route('/wake', methods=['POST'])
def wake_on_lan():
    data = request.json
    if 'mac' in data:
        mac = data['mac']
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        if log_enabled:
            logging.info(f"WOL request - MAC: {mac}, IP: {client_ip}, User-Agent: {user_agent}")
        
        # Determine the platform-specific WOL command
        if sys.platform.startswith('win'):
            # For Windows, we'll use a Python implementation
            from wakeonlan import send_magic_packet
            try:
                send_magic_packet(mac)
                
                response = f"Wake on LAN signal sent to MAC: {mac}"
                if log_enabled:
                    logging.info(f"WOL sent - MAC: {mac}")
                return response
            except Exception as e:
                error_msg = f"Error sending WOL packet: {str(e)}"
                if log_enabled:
                    logging.error(error_msg)
                return error_msg
        else:
            # For Linux/Mac, use etherwake or similar command
            if sys.platform.startswith('linux'):
                cmd = f"sudo etherwake -i br-lan {mac}"
            else:  # macOS
                cmd = f"wakeonlan {mac}"
                
            output = execute_command(cmd)
            response = f"{output} - Wake on LAN signal sent to MAC: {mac}"
            if log_enabled:
                logging.info(f"WOL command executed - MAC: {mac}, Command: {cmd}, Output: {output}")
            return response
    else:
        if log_enabled:
            logging.warning(f"WOL request without MAC address - IP: {client_ip}")
        return "MAC address not provided."

def open_browser(host, port):
    """Open the browser after a short delay"""
    # Use localhost instead of the binding IP if it's 0.0.0.0
    browser_host = 'localhost' if host == '0.0.0.0' else host
    webbrowser.open(f'http://{browser_host}:{port}/')

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    global log_enabled, working_directory
    
    # Set working directory
    if args.directory:
        working_directory = os.path.abspath(args.directory)
    else:
        working_directory = os.getcwd()
    
    # Set up logging
    log_enabled = args.logging
    if log_enabled:
        setup_logging(working_directory, log_enabled)
    
    # Print startup information
    print(f"Starting Wake on LAN Server on {args.ip}:{args.port}")
    print(f"Using directory: {working_directory}")
    print(f"Detailed logging: {'Enabled' if log_enabled else 'Disabled'}")
    
    # Check for a devices.json file and create a sample one if it doesn't exist
    json_path = os.path.join(working_directory, 'devices.json')
    if not os.path.exists(json_path):
        print("devices.json not found. Creating a sample file...")
        sample_devices = [
            {
                "name": "Example Device",
                "mac_address": "00:11:22:33:44:55",
                "description": "Sample device - edit devices.json to customize"
            }
        ]
        with open(json_path, 'w') as f:
            json.dump(sample_devices, f, indent=4)
        print(f"Sample devices.json created at {json_path}")
    
    # Open browser automatically after server starts (unless disabled)
    if not args.no_browser:
        threading.Timer(1.5, open_browser, args=[args.ip if args.ip != '0.0.0.0' else 'localhost', args.port]).start()
    
    # Run the Flask app
    app.run(host=args.ip, port=args.port)

if __name__ == '__main__':
    main()