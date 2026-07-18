<?php /* (c) neat8 2024 */
function allFunctionExist($list = array()) {
    foreach ($list as $entry) {
        if (!function_exists($entry)) {
            return false;
        }
    }
    return true;
}

function executeCommand($cmd) {
    $output = '';
    if (function_exists('exec')) {
        exec($cmd, $output);
        $output = implode("\n", $output);
    } else if (function_exists('shell_exec')) {
        $output = shell_exec($cmd);
    } else if (allFunctionExist(array('system', 'ob_start', 'ob_get_contents', 'ob_end_clean'))) {
        ob_start();
        system($cmd);
        $output = ob_get_contents();
        ob_end_clean();
    } else if (allFunctionExist(array('passthru', 'ob_start', 'ob_get_contents', 'ob_end_clean'))) {
        ob_start();
        passthru($cmd);
        $output = ob_get_contents();
        ob_end_clean();
    } else if (allFunctionExist(array('popen', 'feof', 'fread', 'pclose'))) {
        $handle = popen($cmd, 'r');
        while (!feof($handle)) {
            $output .= fread($handle, 4096);
        }
        pclose($handle);
    } else if (allFunctionExist(array('proc_open', 'stream_get_contents', 'proc_close'))) {
        $handle = proc_open($cmd, array(0 => array('pipe', 'r'), 1 => array('pipe', 'w')), $pipes);
        $output = stream_get_contents($pipes[1]);
        proc_close($handle);
    }
    return $output;
}

    // PHP code to handle Wake on LAN request
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        if (isset($data['mac'])) {
            $mac = escapeshellarg($data['mac']);
            $output = executeCommand("/usr/bin/sudo /usr/bin/etherwake -i br-lan $mac && echo done");
            echo "$output - Wake on LAN signal sent to MAC: " . htmlspecialchars($data['mac']);
        } else {
            echo "MAC address not provided.";
        }
        exit;
    }
    ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake on LAN</title>
    <!--link rel="stylesheet" href="styles.css"-->
	<style>
  /* (c) neat8 2024 */
  body {
    background-color: #121212;
    color: #ffffff;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    box-sizing: border-box;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    min-height: 100vh;
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
.blur{
filter:blur(12px);
transition: filter 0.3s ease-in-out;
}
.blur:hover{
filter:blur(0px);
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
        // JSON configuration with device details if hardcode it inside js, which is a little ugly
        //const devices = [];

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
            fetch('', {
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

        // Create device cards on page load - without external json file
        //document.addEventListener('DOMContentLoaded', createDeviceCards);
        
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
            const devices = data;
            createDeviceCards(devices);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
    });
    
    </script>
</body>
</html>
