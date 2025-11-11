#!/bin/bash

#############################################################
# Server Setup Script for Customs Declaration Platform
#
# This script automates the initial server setup for
# deploying the application on Ubuntu.
#
# Usage:
#   wget https://raw.githubusercontent.com/your-repo/main/scripts/server-setup.sh
#   chmod +x server-setup.sh
#   ./server-setup.sh
#
# Or run directly:
#   bash <(curl -fsSL https://raw.githubusercontent.com/your-repo/main/scripts/server-setup.sh)
#
#############################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_DIR="$HOME/logai-production"
NGINX_AVAILABLE="/etc/nginx/sites-available/siufu.tinsu.ai"
NGINX_ENABLED="/etc/nginx/sites-enabled/siufu.tinsu.ai"
SSL_DIR="/etc/nginx/ssl"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Customs Declaration Platform - Server Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Function to print colored status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running on Ubuntu
check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" != "ubuntu" ]; then
            print_error "This script is designed for Ubuntu. Detected: $ID"
            exit 1
        fi
    else
        print_error "Cannot detect OS. Please run on Ubuntu."
        exit 1
    fi
    print_status "Running on Ubuntu $VERSION_ID"
}

# Update system packages
update_system() {
    print_info "Updating system packages..."
    sudo apt-get update -qq
    sudo apt-get upgrade -y -qq
    print_status "System packages updated"
}

# Install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker is already installed: $(docker --version)"
    else
        print_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sudo sh /tmp/get-docker.sh
        rm /tmp/get-docker.sh

        # Add current user to docker group
        sudo usermod -aG docker $USER
        print_status "Docker installed successfully"
        print_warning "You need to log out and log back in for Docker group changes to take effect"
    fi
}

# Install Docker Compose
check_docker_compose() {
    if docker compose version &> /dev/null; then
        print_status "Docker Compose is available: $(docker compose version)"
    else
        print_warning "Docker Compose plugin not found. Installing..."
        sudo apt-get install -y docker-compose-plugin
        print_status "Docker Compose installed"
    fi
}

# Install Nginx
install_nginx() {
    if command -v nginx &> /dev/null; then
        print_status "Nginx is already installed: $(nginx -v 2>&1 | grep -o 'nginx/[^ ]*')"
    else
        print_info "Installing Nginx..."
        sudo apt-get install -y nginx
        sudo systemctl enable nginx
        sudo systemctl start nginx
        print_status "Nginx installed and started"
    fi
}

# Create deployment directory structure
create_directories() {
    print_info "Creating deployment directory structure..."
    mkdir -p "$DEPLOYMENT_DIR/secrets"
    mkdir -p "$DEPLOYMENT_DIR/backups"
    chmod 700 "$DEPLOYMENT_DIR/secrets"
    print_status "Created: $DEPLOYMENT_DIR"
}

# Configure firewall
configure_firewall() {
    if command -v ufw &> /dev/null; then
        print_info "Configuring UFW firewall..."
        sudo ufw allow 22/tcp comment 'SSH'
        sudo ufw allow 80/tcp comment 'HTTP'
        sudo ufw allow 443/tcp comment 'HTTPS'

        # Enable UFW if not already enabled
        if ! sudo ufw status | grep -q "Status: active"; then
            print_warning "UFW will be enabled. Make sure SSH (port 22) is allowed!"
            read -p "Enable UFW firewall? (yes/no): " enable_ufw
            if [ "$enable_ufw" = "yes" ]; then
                echo "y" | sudo ufw enable
                print_status "UFW firewall enabled"
            else
                print_warning "UFW firewall not enabled"
            fi
        else
            print_status "UFW firewall already configured"
        fi
    else
        print_warning "UFW not installed. Skipping firewall configuration."
    fi
}

# Install additional utilities
install_utilities() {
    print_info "Installing additional utilities..."
    sudo apt-get install -y curl wget git rsync
    print_status "Utilities installed"
}

# Create SSL directory
create_ssl_directory() {
    print_info "Creating SSL directory..."
    sudo mkdir -p "$SSL_DIR"
    sudo chmod 755 "$SSL_DIR"
    print_status "SSL directory created: $SSL_DIR"
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}Server Setup Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo "1. Log out and log back in to apply Docker group changes:"
    echo "   exit"
    echo ""
    echo "2. Set up Cloudflare SSL certificates:"
    echo "   sudo nano $SSL_DIR/siufu.tinsu.ai.pem   # Paste certificate"
    echo "   sudo nano $SSL_DIR/siufu.tinsu.ai.key   # Paste private key"
    echo "   sudo chmod 600 $SSL_DIR/siufu.tinsu.ai.key"
    echo ""
    echo "3. Create Nginx configuration:"
    echo "   sudo nano $NGINX_AVAILABLE"
    echo "   # Copy configuration from docs/DEPLOYMENT.md"
    echo ""
    echo "4. Enable Nginx site:"
    echo "   sudo ln -s $NGINX_AVAILABLE $NGINX_ENABLED"
    echo "   sudo nginx -t"
    echo "   sudo systemctl reload nginx"
    echo ""
    echo "5. Configure GitHub Secrets (see docs/DEPLOYMENT.md)"
    echo ""
    echo "6. Generate SSH key for GitHub Actions:"
    echo "   ssh-keygen -t ed25519 -C 'github-deploy' -f ~/.ssh/github_deploy"
    echo "   cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys"
    echo "   cat ~/.ssh/github_deploy  # Copy to GitHub Secret: SSH_PRIVATE_KEY"
    echo ""
    echo "7. Deploy via GitHub Actions or manually"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "   Full Guide: docs/DEPLOYMENT.md"
    echo "   Quick Start: docs/DEPLOYMENT_QUICKSTART.md"
    echo ""
    echo -e "${GREEN}Deployment directory: $DEPLOYMENT_DIR${NC}"
    echo ""
}

# Main execution
main() {
    check_os
    update_system
    install_docker
    check_docker_compose
    install_nginx
    install_utilities
    create_directories
    create_ssl_directory
    configure_firewall
    print_next_steps
}

# Run main function
main
