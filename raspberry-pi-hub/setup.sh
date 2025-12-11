#!/bin/bash
#===============================================================================
# Tickertronix Hub - Raspberry Pi Setup Script
#===============================================================================
# This script sets up a fresh Raspberry Pi OS Lite (Bookworm) installation
# to run as a Tickertronix Hub.
#
# Tested on: Raspberry Pi Zero 2 W
# Requires: Raspberry Pi OS Lite (Bookworm, 64-bit recommended)
#
# Usage:
#   ./setup.sh
#
#
#===============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/tickertronix-hub"
SERVICE_USER="tickertronix"
HOSTNAME_NEW="tickertronixhub"
REPO_URL="https://github.com/Tickertronix/Tickertronix-Open.git"

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║              TICKERTRONIX HUB - SETUP SCRIPT                     ║"
    echo "║                                                                  ║"
    echo "║         Transform your Raspberry Pi into a financial             ║"
    echo "║              data hub for your local network                     ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  STEP: $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_raspberry_pi() {
    if [ ! -f /proc/device-tree/model ]; then
        log_warn "Could not detect Raspberry Pi model"
        return
    fi
    
    PI_MODEL=$(cat /proc/device-tree/model)
    log_info "Detected: $PI_MODEL"
}

check_os() {
    if [ ! -f /etc/os-release ]; then
        log_error "Could not detect OS"
        exit 1
    fi
    
    . /etc/os-release
    log_info "OS: $PRETTY_NAME"
    
    if [[ "$VERSION_CODENAME" != "bookworm" ]]; then
        log_warn "This script is tested on Raspberry Pi OS Bookworm"
        log_warn "You are running: $VERSION_CODENAME"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

#-------------------------------------------------------------------------------
# Installation steps
#-------------------------------------------------------------------------------

install_system_packages() {
    log_step "Installing system packages"
    
    apt-get update
    apt-get upgrade -y
    
    # Core packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        avahi-daemon \
        sqlite3
    
    # Optional: for GUI mode (not needed for headless)
    # apt-get install -y python3-tk
    
    log_info "System packages installed"
}

setup_hostname() {
    log_step "Setting up hostname"
    
    CURRENT_HOSTNAME=$(hostname)
    
    if [ "$CURRENT_HOSTNAME" = "$HOSTNAME_NEW" ]; then
        log_info "Hostname already set to $HOSTNAME_NEW"
        return
    fi
    
    read -p "Change hostname from '$CURRENT_HOSTNAME' to '$HOSTNAME_NEW'? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Update hostname
        echo "$HOSTNAME_NEW" > /etc/hostname
        
        # Update /etc/hosts
        sed -i "s/127.0.1.1.*$CURRENT_HOSTNAME/127.0.1.1\t$HOSTNAME_NEW/g" /etc/hosts
        
        # Apply immediately
        hostnamectl set-hostname "$HOSTNAME_NEW"
        
        log_info "Hostname changed to $HOSTNAME_NEW"
        log_info "The hub will be accessible at: ${HOSTNAME_NEW}.local"
    else
        log_info "Keeping current hostname: $CURRENT_HOSTNAME"
    fi
}

setup_avahi() {
    log_step "Configuring mDNS (Avahi)"
    
    # Enable and start avahi-daemon for .local hostname resolution
    systemctl enable avahi-daemon
    systemctl start avahi-daemon
    
    log_info "Avahi configured - device will be discoverable as $(hostname).local"
}

create_service_user() {
    log_step "Creating service user"
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "User $SERVICE_USER already exists"
    else
        useradd --system --no-create-home --shell /bin/false "$SERVICE_USER"
        log_info "Created system user: $SERVICE_USER"
    fi
}

clone_or_update_repo() {
    log_step "Setting up application files"
    
    # Check if we're running from the repo directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ -f "$SCRIPT_DIR/main_headless.py" ]; then
        log_info "Running from source directory"
        
        # Copy to install directory
        if [ -d "$INSTALL_DIR" ]; then
            log_info "Updating existing installation..."
            rm -rf "$INSTALL_DIR"
        fi
        
        mkdir -p "$INSTALL_DIR"
        cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
        
    elif [ -d "$INSTALL_DIR" ]; then
        log_info "Updating existing installation..."
        cd "$INSTALL_DIR"
        git pull || log_warn "Git pull failed - continuing with existing files"
    else
        log_info "Cloning repository..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
    
    log_info "Application files ready at $INSTALL_DIR"
}

setup_python_environment() {
    log_step "Setting up Python environment"
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    if [ -d "venv" ]; then
        log_info "Virtual environment exists, updating..."
    else
        python3 -m venv venv
        log_info "Created Python virtual environment"
    fi
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    
    log_info "Python dependencies installed"
}

setup_directories() {
    log_step "Setting up data directories"
    
    # Create data and log directories
    mkdir -p "$INSTALL_DIR/data"
    mkdir -p "$INSTALL_DIR/logs"
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/data"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/logs"
    
    log_info "Data directories configured"
}

create_systemd_service() {
    log_step "Creating systemd service"
    
    cat > /etc/systemd/system/tickertronix-hub.service << 'EOF'
[Unit]
Description=Tickertronix Hub - Financial Data Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tickertronix
Group=tickertronix
WorkingDirectory=/opt/tickertronix-hub
ExecStart=/opt/tickertronix-hub/venv/bin/python3 main_web.py
Restart=always
RestartSec=10

# Environment
Environment=PYTHONUNBUFFERED=1

# Logging
StandardOutput=append:/opt/tickertronix-hub/logs/service.log
StandardError=append:/opt/tickertronix-hub/logs/service.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/tickertronix-hub/data /opt/tickertronix-hub/logs

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service to start on boot
    systemctl enable tickertronix-hub
    
    # Start the service now
    systemctl start tickertronix-hub
    
    log_info "Systemd service created and started: tickertronix-hub.service"
}

create_helper_scripts() {
    log_step "Creating helper scripts"
    
    # Create a wrapper script in /usr/local/bin
    cat > /usr/local/bin/tickertronix << 'EOF'
#!/bin/bash
# Tickertronix Hub CLI helper

INSTALL_DIR="/opt/tickertronix-hub"

case "$1" in
    start)
        sudo systemctl start tickertronix-hub
        echo "Tickertronix Hub started"
        ;;
    stop)
        sudo systemctl stop tickertronix-hub
        echo "Tickertronix Hub stopped"
        ;;
    restart)
        sudo systemctl restart tickertronix-hub
        echo "Tickertronix Hub restarted"
        ;;
    status)
        systemctl status tickertronix-hub
        ;;
    logs)
        tail -f "$INSTALL_DIR/logs/app.log"
        ;;
    setup-credentials)
        cd "$INSTALL_DIR"
        sudo -u tickertronix ./venv/bin/python3 credentials_setup.py
        ;;
    *)
        echo "Tickertronix Hub - Management Commands"
        echo ""
        echo "Usage: tickertronix <command>"
        echo ""
        echo "Commands:"
        echo "  start              Start the hub service"
        echo "  stop               Stop the hub service"
        echo "  restart            Restart the hub service"
        echo "  status             Show service status"
        echo "  logs               Follow the application logs"
        echo "  setup-credentials  Configure Alpaca API credentials"
        echo ""
        echo "Web UI (when running):"
        echo "  http://$(hostname).local:8080"
        echo ""
        echo "REST API Endpoints:"
        echo "  http://$(hostname).local:5001/health"
        echo "  http://$(hostname).local:5001/prices"
        echo "  http://$(hostname).local:5001/status"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/tickertronix
    
    log_info "Helper script installed: tickertronix"
}

set_permissions() {
    log_step "Setting file permissions"
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/main_web.py"
    chmod +x "$INSTALL_DIR/main_headless.py"
    chmod +x "$INSTALL_DIR/main.py"
    chmod +x "$INSTALL_DIR/credentials_setup.py"
    chmod +x "$INSTALL_DIR/start.sh"
    
    log_info "Permissions configured"
}

print_completion_message() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║                    SETUP COMPLETE!                               ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${GREEN}The hub is now running and will start automatically on boot.${NC}"
    echo ""
    echo -e "${YELLOW}ACCESS YOUR HUB:${NC}"
    echo ""
    echo -e "  Web UI:   ${BLUE}http://$(hostname).local:8080${NC}"
    echo -e "  REST API: ${BLUE}http://$(hostname).local:5001${NC}"
    echo ""
    echo -e "${YELLOW}NEXT STEP:${NC}"
    echo ""
    echo "  Configure your Alpaca API credentials via the Web UI,"
    echo "  or from the command line:"
    echo -e "   ${BLUE}tickertronix setup-credentials${NC}"
    echo ""
    echo -e "${YELLOW}USEFUL COMMANDS:${NC}"
    echo "  tickertronix status    - Check if service is running"
    echo "  tickertronix logs      - View application logs"
    echo "  tickertronix restart   - Restart the service"
    echo ""
    echo -e "${YELLOW}DOCUMENTATION:${NC}"
    echo "  $INSTALL_DIR/README.md"
    echo ""
    
    # Check if reboot is needed for hostname change
    if [ "$(hostname)" != "$HOSTNAME_NEW" ]; then
        echo -e "${YELLOW}NOTE:${NC} A reboot is recommended to apply hostname changes."
        echo "      Run: sudo reboot"
        echo ""
    fi
}

#-------------------------------------------------------------------------------
# Main execution
#-------------------------------------------------------------------------------

main() {
    print_banner
    
    check_root
    check_raspberry_pi
    check_os
    
    log_info "Starting Tickertronix Hub installation..."
    
    install_system_packages
    setup_hostname
    setup_avahi
    create_service_user
    clone_or_update_repo
    setup_python_environment
    setup_directories
    set_permissions
    create_systemd_service
    create_helper_scripts
    
    print_completion_message
}

# Run main function
main "$@"
