# Build stage
FROM golang:1.21-alpine AS builder

# Set working directory
WORKDIR /app

# Copy Go module files first to leverage Docker layer caching
COPY go.mod go.sum* ./

# If go.sum doesn't exist yet, this will create it (no error if it exists)
RUN if [ ! -f go.sum ]; then go mod download && touch go.sum; else go mod download; fi

# Copy the source code
COPY . .

# Build the Go app with static linking
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o wol-server .

# Final stage - minimal runtime image
FROM alpine:3.18

LABEL org.opencontainers.image.source="https://github.com/neatplusone/openwrt_simpler_wakeonlan"
LABEL org.opencontainers.image.description="Wake-on-LAN Web Server"
LABEL org.opencontainers.image.licenses="MIT"

# Install necessary utilities for WOL
RUN apk --no-cache add \
    # For network utilities (contains ether-wake)
    net-tools \
    # For network troubleshooting
    iputils \
    # For debugging
    curl

# Set the working directory
WORKDIR /app

# Copy the built binary from the builder stage
COPY --from=builder /app/wol-server .

# Create directory for sample devices.json if needed
RUN mkdir -p /app/data

# Create a minimal sample devices.json file if none exists
RUN echo '[{"name":"Example Device","mac_address":"00:11:22:33:44:55","description":"Sample device - edit to customize"}]' > /app/data/devices.json

# Expose the default port
EXPOSE 5000

# Set the entry point with fallback to Go implementation if command-line tools aren't available
ENTRYPOINT ["/app/wol-server", "-directory", "/app/data"]