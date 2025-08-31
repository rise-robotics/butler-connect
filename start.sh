#!/bin/bash

# Butler Connect - Unitree Go2 Controller
# Linux/macOS Launcher Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                    🤖 Butler Connect                      ║"
    echo "║               Unitree Go2 Robot Controller                ║"
    echo "║                                                          ║"
    echo "║                   Linux/macOS Launcher                   ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        echo -e "${YELLOW}💡 Please install Python 3.8 or higher${NC}"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e "${GREEN}✅ Python ${python_version} is available${NC}"
}

check_project_dir() {
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt not found${NC}"
        echo -e "${YELLOW}💡 Please run this script from the butler-connect project directory${NC}"
        exit 1
    fi
    echo -e "${GREEN}📁 Project directory confirmed${NC}"
}

setup_venv() {
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✅ Virtual environment found${NC}"
    fi
    
    echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
    source venv/bin/activate
}

install_dependencies() {
    echo -e "${BLUE}🔧 Installing/updating dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
}

check_config() {
    echo -e "${BLUE}🔍 Checking configuration files...${NC}"
    
    configs=("robot_config.yaml" "control_config.yaml" "safety_config.yaml")
    
    for config in "${configs[@]}"; do
        if [ -f "config/${config}" ]; then
            echo -e "${GREEN}✅ ${config}${NC}"
        else
            echo -e "${RED}❌ ${config} missing${NC}"
        fi
    done
}

start_application() {
    # Create logs directory
    mkdir -p logs
    
    echo
    echo -e "${BLUE}🚀 Starting Butler Connect...${NC}"
    echo -e "${GREEN}📱 Web interface: http://localhost:8000${NC}"
    echo -e "${GREEN}📖 API docs: http://localhost:8000/docs${NC}"
    echo
    echo -e "${YELLOW}⚠️  SAFETY REMINDER:${NC}"
    echo -e "${YELLOW}   - Keep emergency stop ready${NC}"
    echo -e "${YELLOW}   - Ensure robot has space to move${NC}"
    echo -e "${YELLOW}   - Check battery level${NC}"
    echo
    echo -e "${RED}🛑 Press Ctrl+C to stop${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo
    
    # Start the application
    python3 src/main.py
}

cleanup() {
    echo
    echo -e "${RED}🛑 Butler Connect stopped${NC}"
    echo -e "${GREEN}✅ Thank you for using Butler Connect!${NC}"
}

# Main execution
main() {
    print_header
    
    check_python
    check_project_dir
    setup_venv
    install_dependencies
    check_config
    
    # Set up signal handling
    trap cleanup EXIT INT TERM
    
    start_application
}

# Run main function
main "$@"
