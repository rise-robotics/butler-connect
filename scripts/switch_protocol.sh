#!/bin/bash

# Protocol Switcher for Butler Connect
# Helps switch between ROS2 and WebRTC communication protocols

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config/robot_config.yaml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN} Butler Connect - Protocol Switcher        ${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
}

print_current_protocol() {
    if [ -f "$CONFIG_FILE" ]; then
        current=$(grep -o 'protocol: "[^"]*"' "$CONFIG_FILE" | cut -d'"' -f2)
        echo -e "Current protocol: ${YELLOW}$current${NC}"
    else
        echo -e "${RED}Config file not found: $CONFIG_FILE${NC}"
        exit 1
    fi
}

switch_to_ros2() {
    echo -e "\n${GREEN}Switching to ROS2 protocol...${NC}"
    
    # Update configuration
    sed -i 's/protocol: "[^"]*"/protocol: "ros2"/' "$CONFIG_FILE"
    
    echo "✅ Configuration updated to use ROS2"
    echo ""
    echo -e "${YELLOW}ROS2 Protocol Features:${NC}"
    echo "- Real-time topic-based communication"
    echo "- Standard robotics middleware"
    echo "- Requires ROS2 environment setup"
    echo "- Topics: cmd_vel, battery_state, odom, temperature"
    echo ""
    echo -e "${YELLOW}Requirements:${NC}"
    echo "- ROS2 installed and sourced"
    echo "- Robot running ROS2 bridge/driver"
}

switch_to_webrtc() {
    echo -e "\n${GREEN}Switching to WebRTC protocol...${NC}"
    
    # Update configuration  
    sed -i 's/protocol: "[^"]*"/protocol: "webrtc"/' "$CONFIG_FILE"
    
    echo "✅ Configuration updated to use WebRTC"
    echo ""
    echo -e "${YELLOW}WebRTC Protocol Features:${NC}"
    echo "- Real-time peer-to-peer communication"
    echo "- Low latency data streaming"
    echo "- Built-in NAT traversal"
    echo "- Optional video streaming support"
    echo ""
    echo -e "${YELLOW}Requirements:${NC}"
    echo "- Robot with WebRTC support"
    echo "- Network connectivity to robot"
    echo "- aiortc Python package (install with: pip install aiortc av)"
}

switch_to_udp() {
    echo -e "\n${GREEN}Switching to UDP protocol (Mock mode)...${NC}"
    
    # Update configuration
    sed -i 's/protocol: "[^"]*"/protocol: "udp"/' "$CONFIG_FILE"
    
    echo "✅ Configuration updated to use UDP"
    echo ""
    echo -e "${YELLOW}UDP Protocol Features:${NC}"
    echo "- Simple UDP communication"
    echo "- Mock/simulation mode when robot unavailable"
    echo "- Basic connection testing"
    echo ""
    echo -e "${YELLOW}Note:${NC}"
    echo "- This mode provides simulated sensor data"
    echo "- Use for testing without real robot"
}

restart_butler_connect() {
    echo -e "\n${YELLOW}Restarting Butler Connect with new protocol...${NC}"
    
    # Check if PM2 is running Butler Connect
    if pm2 list | grep -q "butler-connect"; then
        echo "🔄 Restarting via PM2..."
        pm2 restart butler-connect
        sleep 2
        pm2 status butler-connect
    else
        echo "⚠️  Butler Connect is not running via PM2"
        echo "   Start it manually with: pm2 start ecosystem.config.js"
    fi
}

show_help() {
    echo "Usage: $0 [PROTOCOL] [OPTIONS]"
    echo ""
    echo "Protocols:"
    echo "  ros2    - Switch to ROS2 communication"
    echo "  webrtc  - Switch to WebRTC communication"  
    echo "  udp     - Switch to UDP/Mock mode"
    echo ""
    echo "Options:"
    echo "  -r, --restart  - Restart Butler Connect after switching"
    echo "  -h, --help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 ros2              # Switch to ROS2"
    echo "  $0 webrtc --restart  # Switch to WebRTC and restart"
    echo "  $0 udp -r            # Switch to UDP and restart"
}

main() {
    print_header
    print_current_protocol
    
    # Parse arguments
    PROTOCOL=""
    RESTART=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            ros2|webrtc|udp)
                PROTOCOL="$1"
                shift
                ;;
            -r|--restart)
                RESTART=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no protocol specified, show interactive menu
    if [ -z "$PROTOCOL" ]; then
        echo ""
        echo "Select protocol:"
        echo "1) ROS2"
        echo "2) WebRTC"
        echo "3) UDP (Mock)"
        echo "4) Exit"
        echo ""
        read -p "Enter choice (1-4): " choice
        
        case $choice in
            1) PROTOCOL="ros2" ;;
            2) PROTOCOL="webrtc" ;;
            3) PROTOCOL="udp" ;;
            4) echo "Exiting..."; exit 0 ;;
            *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
        esac
        
        read -p "Restart Butler Connect after switching? (y/N): " restart_choice
        if [[ $restart_choice =~ ^[Yy]$ ]]; then
            RESTART=true
        fi
    fi
    
    # Switch protocol
    case $PROTOCOL in
        ros2)
            switch_to_ros2
            ;;
        webrtc)
            switch_to_webrtc
            ;;
        udp)
            switch_to_udp
            ;;
        *)
            echo -e "${RED}Invalid protocol: $PROTOCOL${NC}"
            show_help
            exit 1
            ;;
    esac
    
    # Restart if requested
    if [ "$RESTART" = true ]; then
        restart_butler_connect
    fi
    
    echo ""
    echo -e "${GREEN}Protocol switch complete!${NC}"
    echo "New configuration:"
    print_current_protocol
}

# Run main function
main "$@"
