#!/bin/bash
#
# Prusa Camera Timelapse Installation Script
#
# Automates the installation and configuration of the Prusa camera
# timelapse system on Raspberry Pi Zero 2W.
#
# Usage: sudo ./install.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

print_header "Prusa Camera Timelapse Installation"
echo "Installing for user: $ACTUAL_USER"
echo "Home directory: $ACTUAL_HOME"
echo ""

# Confirm installation
read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Installation cancelled"
    exit 0
fi

# Update system
print_header "Updating System Packages"
apt update
apt upgrade -y
print_success "System packages updated"

# Install dependencies
print_header "Installing System Dependencies"
PACKAGES=(
    "python3"
    "python3-pip"
    "python3-venv"
    "libcamera-apps"
    "libcamera-dev"
    "ffmpeg"
    "git"
    "smbclient"
    "cifs-utils"
    "nfs-common"
    "yq"
)

for package in "${PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $package "; then
        print_success "$package already installed"
    else
        apt install -y "$package"
        print_success "$package installed"
    fi
done

# Enable camera interface
print_header "Configuring Camera Interface"
if ! grep -q "^camera_auto_detect=1" /boot/config.txt; then
    echo "camera_auto_detect=1" >> /boot/config.txt
    print_success "Camera auto-detect enabled"
else
    print_success "Camera already enabled"
fi

# Create directory structure
print_header "Creating Directory Structure"
INSTALL_DIR="$ACTUAL_HOME/prusa-camera"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/captures"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR"
print_success "Directories created: $INSTALL_DIR"

# Copy files
print_header "Installing Application Files"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy Python service
if [ -f "$SCRIPT_DIR/camera_service.py" ]; then
    cp "$SCRIPT_DIR/camera_service.py" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/camera_service.py"
    chown "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR/camera_service.py"
    print_success "camera_service.py installed"
else
    print_error "camera_service.py not found in $SCRIPT_DIR"
    exit 1
fi

# Copy compilation script
if [ -f "$SCRIPT_DIR/compile_video.sh" ]; then
    cp "$SCRIPT_DIR/compile_video.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/compile_video.sh"
    chown "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR/compile_video.sh"
    print_success "compile_video.sh installed"
else
    print_error "compile_video.sh not found in $SCRIPT_DIR"
    exit 1
fi

# Copy or create config
if [ -f "$SCRIPT_DIR/config.yaml" ]; then
    if [ -f "$INSTALL_DIR/config.yaml" ]; then
        print_warning "config.yaml already exists, creating backup"
        cp "$INSTALL_DIR/config.yaml" "$INSTALL_DIR/config.yaml.backup"
    fi
    cp "$SCRIPT_DIR/config.yaml" "$INSTALL_DIR/"
    chown "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR/config.yaml"
    print_success "config.yaml installed"
else
    print_error "config.yaml not found in $SCRIPT_DIR"
    exit 1
fi

# Install Python dependencies
print_header "Installing Python Dependencies"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    sudo -u "$ACTUAL_USER" pip3 install --user -r "$SCRIPT_DIR/requirements.txt"
    print_success "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping Python dependencies"
fi

# Install systemd service
print_header "Installing Systemd Service"
if [ -f "$SCRIPT_DIR/camera.service" ]; then
    # Update paths in service file
    sed "s|/home/pi|$ACTUAL_HOME|g" "$SCRIPT_DIR/camera.service" > /etc/systemd/system/prusa-camera.service
    sed -i "s|User=pi|User=$ACTUAL_USER|g" /etc/systemd/system/prusa-camera.service
    sed -i "s|Group=pi|Group=$ACTUAL_USER|g" /etc/systemd/system/prusa-camera.service
    
    systemctl daemon-reload
    print_success "Systemd service installed"
else
    print_error "camera.service not found in $SCRIPT_DIR"
    exit 1
fi

# Test camera
print_header "Testing Camera"
print_warning "Testing camera capture (this may take a few seconds)..."
if sudo -u "$ACTUAL_USER" libcamera-still -o /tmp/test_capture.jpg -t 1 -n 2>&1; then
    print_success "Camera test successful"
    rm -f /tmp/test_capture.jpg
else
    print_error "Camera test failed - please check camera connection"
    print_warning "You may need to reboot for camera changes to take effect"
fi

# Configure GPIO permissions
print_header "Configuring GPIO Permissions"
if ! groups "$ACTUAL_USER" | grep -q "gpio"; then
    usermod -a -G gpio "$ACTUAL_USER"
    print_success "User added to gpio group"
else
    print_success "User already in gpio group"
fi

# Setup logrotate
print_header "Configuring Log Rotation"
cat > /etc/logrotate.d/prusa-camera <<EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $ACTUAL_USER $ACTUAL_USER
}
EOF
print_success "Log rotation configured"

# Print configuration instructions
print_header "Installation Complete!"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Edit the configuration file:"
echo -e "   ${YELLOW}nano $INSTALL_DIR/config.yaml${NC}"
echo ""
echo "2. Configure your Prusa Connect token:"
echo "   - Visit https://connect.prusa3d.com/"
echo "   - Go to Cameras section"
echo "   - Add new 'other camera' and copy the token"
echo "   - Update the token in config.yaml"
echo ""
echo "3. (Optional) Configure NAS upload settings in config.yaml"
echo ""
echo "4. Enable and start the service:"
echo -e "   ${YELLOW}sudo systemctl enable prusa-camera${NC}"
echo -e "   ${YELLOW}sudo systemctl start prusa-camera${NC}"
echo ""
echo "5. Check service status:"
echo -e "   ${YELLOW}sudo systemctl status prusa-camera${NC}"
echo ""
echo "6. View logs:"
echo -e "   ${YELLOW}tail -f $INSTALL_DIR/logs/camera.log${NC}"
echo ""
echo "7. Configure PrusaSlicer G-code (see README.md for details)"
echo ""

if ! groups "$ACTUAL_USER" | grep -q "gpio" && [ -z "$SUDO_USER" ]; then
    print_warning "You may need to log out and back in for GPIO permissions to take effect"
fi

if ! grep -q "^camera_auto_detect=1" /boot/config.txt; then
    print_warning "A reboot is recommended to enable camera interface"
    read -p "Reboot now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Rebooting in 5 seconds..."
        sleep 5
        reboot
    fi
fi

print_success "Installation script completed!"

