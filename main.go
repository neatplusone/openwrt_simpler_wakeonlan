package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"html/template"
	"io"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"
)

// Device represents a network device that can be woken up
type Device struct {
	Name        string `json:"name"`
	MacAddress  string `json:"mac_address"`
	StatusIP    string `json:"status_ip,omitempty"`
	Description string `json:"description,omitempty"`
}

// Configuration for the server
type Config struct {
	Port        int
	IP          string
	Directory   string
	LogToFile   bool
	OpenBrowser bool
}

// HTML template - same design as original
const htmlTemplate = `
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

                const deviceInfo = ` +
	"`" + `
                    <div class="device-info">
                        <h2 class="device-name">${device.name}</h2>
                        <p class="device-mac blur">MAC: ${device.mac_address}</p>
                        ${device.status_ip ? ` + "`" + `<p class="device-description blur">IP: ${device.status_ip}</p>` + "`" + ` : ''}
                        ${device.description ? ` + "`" + `<p class="device-description">${device.description}</p>` + "`" + ` : ''}
                    </div>
                ` + "`" + `;

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
`

// Wake on LAN function sends a magic packet to the specified MAC address
func sendWakeOnLAN(macAddr string) error {
	// Parse the MAC address
	mac, err := net.ParseMAC(macAddr)
	if err != nil {
		return fmt.Errorf("invalid MAC address: %v", err)
	}

	// Create magic packet
	// Magic packet is 6 bytes of 0xFF followed by the mac address repeated 16 times
	packet := make([]byte, 102)
	for i := 0; i < 6; i++ {
		packet[i] = 0xFF
	}

	// Add 16 repetitions of the MAC address
	for i := 0; i < 16; i++ {
		copy(packet[6+i*6:], mac)
	}

	// Set up a UDP address for broadcast
	udpAddr, err := net.ResolveUDPAddr("udp", "255.255.255.255:9")
	if err != nil {
		return fmt.Errorf("failed to resolve UDP address: %v", err)
	}

	// Create a UDP connection
	conn, err := net.DialUDP("udp", nil, udpAddr)
	if err != nil {
		return fmt.Errorf("failed to establish UDP connection: %v", err)
	}
	defer conn.Close()

	// Send the packet
	_, err = conn.Write(packet)
	if err != nil {
		return fmt.Errorf("failed to send packet: %v", err)
	}

	return nil
}

// Execute a command and return its output
func executeCommand(cmd string) (string, error) {
	var command *exec.Cmd
	if runtime.GOOS == "windows" {
		command = exec.Command("cmd", "/C", cmd)
	} else {
		command = exec.Command("sh", "-c", cmd)
	}

	output, err := command.CombinedOutput()
	return string(output), err
}

// Handler for the main page
func indexHandler(config Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Page visit - IP: %s, User-Agent: %s", r.RemoteAddr, r.Header.Get("User-Agent"))

		// Check if wol_index.html exists in the current directory
		htmlFilePath := filepath.Join(config.Directory, "wol_index.html")
		if _, err := os.Stat(htmlFilePath); err == nil {
			// File exists, serve it
			log.Printf("Serving external HTML file: %s", htmlFilePath)
			http.ServeFile(w, r, htmlFilePath)
			return
		}

		// External file doesn't exist, use the embedded template
		log.Printf("External HTML file not found, using embedded template")
		tmpl, err := template.New("index").Parse(htmlTemplate)
		if err != nil {
			http.Error(w, fmt.Sprintf("Error parsing template: %v", err), http.StatusInternalServerError)
			return
		}

		err = tmpl.Execute(w, nil)
		if err != nil {
			http.Error(w, fmt.Sprintf("Error executing template: %v", err), http.StatusInternalServerError)
		}
	}
}

// Handler for the devices.json endpoint
func devicesJSONHandler(config Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		jsonPath := filepath.Join(config.Directory, "devices.json")
		data, err := ioutil.ReadFile(jsonPath)
		if err != nil {
			log.Printf("Error reading devices.json: %v", err)
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte("[]"))
			return
		}

		log.Printf("Serving devices.json - Client IP: %s", r.RemoteAddr)
		w.Header().Set("Content-Type", "application/json")
		w.Write(data)
	}
}

// Handler for the wake endpoint
func wakeHandler(config Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		// Parse JSON request
		var requestData struct {
			MAC string `json:"mac"`
		}

		err := json.NewDecoder(r.Body).Decode(&requestData)
		if err != nil {
			http.Error(w, fmt.Sprintf("Error parsing request: %v", err), http.StatusBadRequest)
			return
		}

		if requestData.MAC == "" {
			http.Error(w, "MAC address not provided", http.StatusBadRequest)
			return
		}

		clientIP := r.RemoteAddr
		userAgent := r.Header.Get("User-Agent")

		log.Printf("WOL request - MAC: %s, IP: %s, User-Agent: %s", requestData.MAC, clientIP, userAgent)

		// Different approaches based on platform
		var result string
		var cmdErr error

		if runtime.GOOS == "windows" {
			// Use the Go implementation for Windows
			err := sendWakeOnLAN(requestData.MAC)
			if err != nil {
				errorMsg := fmt.Sprintf("Error sending WOL packet: %v", err)
				log.Printf("WOL error: %s", errorMsg)
				http.Error(w, errorMsg, http.StatusInternalServerError)
				return
			}
			result = "Wake on LAN signal sent successfully"
		} else if runtime.GOOS == "linux" {
			// For Linux, use etherwake or similar command
			cmd := fmt.Sprintf("sudo etherwake -i br-lan %s", requestData.MAC)
			output, err := executeCommand(cmd)
			cmdErr = err
			result = fmt.Sprintf("%s - Wake on LAN signal sent to MAC: %s", output, requestData.MAC)
		} else {
			// For macOS and others, use wakeonlan
			cmd := fmt.Sprintf("wakeonlan %s", requestData.MAC)
			output, err := executeCommand(cmd)
			cmdErr = err
			result = fmt.Sprintf("%s - Wake on LAN signal sent to MAC: %s", output, requestData.MAC)
		}

		if cmdErr != nil {
			log.Printf("Command execution error: %v", cmdErr)
		}

		log.Printf("WOL sent - MAC: %s", requestData.MAC)
		fmt.Fprint(w, result)
	}
}

// Create sample devices.json if it doesn't exist
func createSampleDevicesJSON(jsonPath string) {
	if _, err := os.Stat(jsonPath); os.IsNotExist(err) {
		fmt.Println("devices.json not found. Creating a sample file...")
		sampleDevices := []Device{
			{
				Name:        "Example Device",
				MacAddress:  "00:11:22:33:44:55",
				Description: "Sample device - edit devices.json to customize",
			},
		}

		jsonData, err := json.MarshalIndent(sampleDevices, "", "    ")
		if err != nil {
			log.Printf("Error creating sample devices.json: %v", err)
			return
		}

		err = ioutil.WriteFile(jsonPath, jsonData, 0644)
		if err != nil {
			log.Printf("Error writing sample devices.json: %v", err)
			return
		}

		fmt.Printf("Sample devices.json created at %s\n", jsonPath)
	}
}

// Open browser function
func openBrowserURL(url string) error {
	var cmd string
	var args []string

	switch runtime.GOOS {
	case "windows":
		cmd = "cmd"
		args = []string{"/c", "start", url}
	case "darwin":
		cmd = "open"
		args = []string{url}
	default: // "linux", "freebsd", etc.
		cmd = "xdg-open"
		args = []string{url}
	}

	return exec.Command(cmd, args...).Start()
}

func main() {
	// Parse command line flags (equivalent to argparse in Python)
	port := flag.Int("port", 8000, "Port to run the server on")
	shortPort := flag.Int("p", 8000, "Port to run the server on (shorthand)")
	ip := flag.String("ip", "0.0.0.0", "IP address to bind the server to")
	directory := flag.String("directory", "", "Directory to look for devices.json and store logs")
	shortDirectory := flag.String("d", "", "Directory to look for devices.json and store logs (shorthand)")
	logToFile := flag.Bool("logging", false, "Enable logging to file")
	shortLogToFile := flag.Bool("l", false, "Enable logging to file (shorthand)")
	openBrowser := flag.Bool("browser", false, "Automatically open browser")
	flag.Parse()

	// Handle shorthand flags (use the non-shorthand value if it was set explicitly)
	finalPort := *port
	if flag.CommandLine.Lookup("port").Value.String() == "8000" && *shortPort != 8000 {
		finalPort = *shortPort
	}

	finalDirectory := *directory
	if *directory == "" && *shortDirectory != "" {
		finalDirectory = *shortDirectory
	}

	finalLogToFile := *logToFile
	if !*logToFile && *shortLogToFile {
		finalLogToFile = *shortLogToFile
	}

	// Setup configuration
	config := Config{
		Port:        finalPort,
		IP:          *ip,
		LogToFile:   finalLogToFile,
		OpenBrowser: *openBrowser,
	}

	// Set working directory
	if finalDirectory != "" {
		config.Directory = finalDirectory
	} else {
		currentDir, err := os.Getwd()
		if err != nil {
			log.Fatalf("Error getting current directory: %v", err)
		}
		config.Directory = currentDir
	}

	// Set working directory
	if *directory != "" {
		config.Directory = *directory
	} else {
		currentDir, err := os.Getwd()
		if err != nil {
			log.Fatalf("Error getting current directory: %v", err)
		}
		config.Directory = currentDir
	}

	// Setup logging - always enabled for console
	log.SetFlags(log.Ldate | log.Ltime)

	// If LogToFile is enabled, set up file logging
	if config.LogToFile {
		logDir := config.Directory
		if _, err := os.Stat(logDir); os.IsNotExist(err) {
			os.MkdirAll(logDir, 0755)
		}

		logFileName := fmt.Sprintf("wol_server_%s.log", time.Now().Format("20060102"))
		logFilePath := filepath.Join(logDir, logFileName)

		logFile, err := os.OpenFile(logFilePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			log.Fatalf("Error opening log file: %v", err)
		}
		defer logFile.Close()

		// Create a multi-writer to log to both console and file
		multiWriter := io.MultiWriter(os.Stdout, logFile)
		log.SetOutput(multiWriter)
		log.Println("Logging initialized (console and file)")
	} else {
		// Log to console only
		log.SetOutput(os.Stdout)
		log.Println("Logging initialized (console only)")
	}

	// Print startup information
	log.Printf("Starting Wake on LAN Server on %s:%d", config.IP, config.Port)
	log.Printf("Using directory: %s", config.Directory)
	log.Printf("Logging to file: %v", config.LogToFile)
	log.Printf("Auto-open browser: %v", config.OpenBrowser)

	// Check for devices.json and create if it doesn't exist
	jsonPath := filepath.Join(config.Directory, "devices.json")
	createSampleDevicesJSON(jsonPath)

	// Set up HTTP handlers
	http.HandleFunc("/", indexHandler(config))
	http.HandleFunc("/devices.json", devicesJSONHandler(config))
	http.HandleFunc("/wake", wakeHandler(config))

	// Open browser automatically after server starts (if enabled)
	if config.OpenBrowser {
		browserHost := "localhost"
		if config.IP != "0.0.0.0" && config.IP != "::" {
			browserHost = config.IP
		}
		url := fmt.Sprintf("http://%s:%d/", browserHost, config.Port)

		go func() {
			time.Sleep(1500 * time.Millisecond)
			log.Printf("Opening browser at %s", url)
			err := openBrowserURL(url)
			if err != nil {
				log.Printf("Error opening browser: %v", err)
			}
		}()
	}

	// Start the server
	listenAddr := fmt.Sprintf("%s:%d", config.IP, config.Port)
	log.Printf("Server started at http://%s/", listenAddr)
	log.Fatal(http.ListenAndServe(listenAddr, nil))
}
