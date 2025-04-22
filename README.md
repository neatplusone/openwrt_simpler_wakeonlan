# Wake-on-LAN Web Server

A simple Go-based web server for sending Wake-on-LAN (WoL) magic packets to devices on your network.

## Features

- Web interface for managing and waking devices
- Support for saving device configurations in JSON
- Cross-platform (Windows, Linux, macOS)
- Easy to build and deploy
- Minimal resource usage
- Docker support for containerized deployment

## Installation

### Prerequisites

- Go 1.16+ installed (for building from source)
- Docker (optional, for containerized deployment)

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/neatplusone/openwrt_simpler_wakeonlan.git
   cd wol-server
   ```

2. Initialize Go module (if needed):
   ```bash
   make init
   ```

3. Build the application:
   ```bash
   make build
   ```

### Using Docker

1. Build the Docker image:
   ```bash
   make docker
   ```

2. Run with Docker Compose:
   ```bash
   make docker-compose
   ```

## Usage

### Command-Line Arguments

| Flag | Shorthand | Description | Default |
|------|-----------|-------------|---------|
| `--port` | `-p` | Port to run the server on | 5000 |
| `--ip` | | IP address to bind the server to | 0.0.0.0 |
| `--directory` | `-d` | Directory for devices.json and logs | Current directory |
| `--logging` | `-l` | Enable logging to file | false |
| `--browser` | | Automatically open browser | false |

### Examples

Run with default settings:
```bash
./wol-server
```

Run on a custom port with file logging:
```bash
./wol-server -p 8080 -l
```

Run with a specific data directory:
```bash
./wol-server -d /path/to/data
```

### Device Configuration

The server looks for a `devices.json` file in the specified directory. If not found, it creates a sample file. The format is:

```json
[
  {
    "name": "Device Name",
    "mac_address": "00:11:22:33:44:55",
    "description": "Optional description",
    "status_ip": "192.168.1.100"
  }
]
```

It's compatible with https://github.com/Florianisme/WakeOnLan | https://apt.izzysoft.de/fdroid/index/apk/de.florianisme.wakeonlan

## Cross-Compilation

Build for Linux:
```bash
make build-linux
```

Build for Windows:
```bash
make build-windows
```

Build for MacOS:
```bash
make build-mac
```

## Docker Deployment

The included Docker setup provides a containerized deployment option.

1. Create a `data` directory in your project:
   ```bash
   mkdir -p data
   ```

2. Create your `devices.json` in the data directory (optional)

3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the web interface at http://localhost:5000

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original concept based on a PHP/Python implementation.

```sh
go build -o wol-server
./wol-server                    # Basic server with console logging
./wol-server -l                 # With file logging
./wol-server -p 8080            # Custom port
./wol-server -browser           # Auto-open browser
```