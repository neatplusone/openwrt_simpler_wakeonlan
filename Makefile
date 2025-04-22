# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
BINARY_NAME=wol-server
BINARY_UNIX=$(BINARY_NAME)_unix
BUILD_DIR=builds

# Build targets
.PHONY: all test clean run build-all init help

all: test build

build:
	$(GOBUILD) -o $(BINARY_NAME) -v

test: 
	$(GOTEST) -v ./...

clean: 
	$(GOCLEAN)
	rm -f $(BINARY_NAME)
	rm -rf $(BUILD_DIR)

run:
	$(GOBUILD) -o $(BINARY_NAME) -v
	./$(BINARY_NAME)

# Build for all platforms
build-all: clean prepare-build-dir build-windows-amd64 build-windows-386 build-linux-amd64 build-linux-386 build-linux-arm64 build-linux-armv7 build-linux-armv6 build-mac-amd64 build-mac-arm64 create-buildout

prepare-build-dir:
	mkdir -p $(BUILD_DIR)

build-windows-amd64:
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_windows_amd64.exe -v

build-windows-386:
	CGO_ENABLED=0 GOOS=windows GOARCH=386 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_windows_386.exe -v

build-linux-amd64:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_linux_amd64 -v

build-linux-386:
	CGO_ENABLED=0 GOOS=linux GOARCH=386 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_linux_386 -v

build-linux-arm64:
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_linux_arm64 -v

build-linux-armv7:
	CGO_ENABLED=0 GOOS=linux GOARCH=arm GOARM=7 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_linux_armv7 -v

build-linux-armv6:
	CGO_ENABLED=0 GOOS=linux GOARCH=arm GOARM=6 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_linux_armv6 -v

build-mac-amd64:
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_darwin_amd64 -v

build-mac-arm64:
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 $(GOBUILD) -o $(BUILD_DIR)/$(BINARY_NAME)_darwin_arm64 -v

create-buildout:
	echo "Wake-on-LAN Web Server - Binary Releases" > $(BUILD_DIR)/buildout
	echo "" >> $(BUILD_DIR)/buildout
	echo "## Binaries" >> $(BUILD_DIR)/buildout
	echo "- Windows (x64): $(BINARY_NAME)_windows_amd64.exe" >> $(BUILD_DIR)/buildout
	echo "- Windows (x86): $(BINARY_NAME)_windows_386.exe" >> $(BUILD_DIR)/buildout
	echo "- Linux (x64): $(BINARY_NAME)_linux_amd64" >> $(BUILD_DIR)/buildout
	echo "- Linux (x86): $(BINARY_NAME)_linux_386" >> $(BUILD_DIR)/buildout
	echo "- Linux (ARM64): $(BINARY_NAME)_linux_arm64" >> $(BUILD_DIR)/buildout
	echo "- Linux (ARMv7): $(BINARY_NAME)_linux_armv7" >> $(BUILD_DIR)/buildout
	echo "- Linux (ARMv6): $(BINARY_NAME)_linux_armv6" >> $(BUILD_DIR)/buildout
	echo "- macOS (x64): $(BINARY_NAME)_darwin_amd64" >> $(BUILD_DIR)/buildout
	echo "- macOS (ARM/M1): $(BINARY_NAME)_darwin_arm64" >> $(BUILD_DIR)/buildout
	echo "" >> $(BUILD_DIR)/buildout
	echo "## Docker Images" >> $(BUILD_DIR)/buildout
	echo "Docker images are available at ghcr.io/[your-username]/$(BINARY_NAME)" >> $(BUILD_DIR)/buildout

# Initialize Go module if needed
init:
	$(GOCMD) mod init github.com/neatplusone/$(BINARY_NAME)
	$(GOCMD) mod tidy

# Help
help:
	@echo "Make targets:"
	@echo "  build          - Build for the current platform"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean build files"
	@echo "  run            - Build and run locally"
	@echo "  build-all      - Build for all platforms"
	@echo "  init           - Initialize Go module"