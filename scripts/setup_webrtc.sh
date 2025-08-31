#!/bin/bash

# WebRTC Setup Script for Butler Connect
# Installs dependencies and configures WebRTC support

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Butler Connect - WebRTC Setup             ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

check_python_env() {
    echo -e "${YELLOW}Checking Python environment...${NC}"
    
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo -e "${RED}❌ Virtual environment not active${NC}"
        echo "Please activate your virtual environment first:"
        echo "  source venv/bin/activate"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
}

install_webrtc_deps() {
    echo -e "\n${YELLOW}Installing WebRTC dependencies...${NC}"
    
    # Check if already installed
    if pip list | grep -q "aiortc"; then
        echo -e "${GREEN}✅ aiortc already installed${NC}"
    else
        echo "📦 Installing aiortc..."
        pip install aiortc>=1.6.0
    fi
    
    if pip list | grep -q "av"; then
        echo -e "${GREEN}✅ av already installed${NC}"
    else
        echo "📦 Installing av (audio/video processing)..."
        pip install av>=10.0.0
    fi
    
    echo -e "${GREEN}✅ WebRTC dependencies installed${NC}"
}

verify_installation() {
    echo -e "\n${YELLOW}Verifying WebRTC installation...${NC}"
    
    python3 -c "
import sys
try:
    import aiortc
    print('✅ aiortc import successful')
    print(f'   Version: {aiortc.__version__}')
except ImportError as e:
    print('❌ aiortc import failed:', e)
    sys.exit(1)

try:
    import av
    print('✅ av import successful')
    print(f'   Version: {av.__version__}')
except ImportError as e:
    print('❌ av import failed:', e)
    sys.exit(1)
    
print('🎉 All WebRTC dependencies verified!')
"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ WebRTC installation verified${NC}"
    else
        echo -e "${RED}❌ WebRTC installation verification failed${NC}"
        exit 1
    fi
}

test_webrtc_client() {
    echo -e "\n${YELLOW}Testing WebRTC client...${NC}"
    
    # Test import of our WebRTC client
    cd "$PROJECT_ROOT"
    
    python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    from core.webrtc_client import WebRTCClient
    print('✅ WebRTCClient import successful')
    
    # Test client creation (without connecting)
    config = {
        'webrtc': {
            'robot_ip': 'test.local',
            'signaling_port': 8765,
            'video_enabled': False,
            'data_channel_enabled': True
        }
    }
    client = WebRTCClient(config)
    print('✅ WebRTCClient instantiation successful')
    print('🎉 WebRTC client ready for use!')
    
except Exception as e:
    print('❌ WebRTC client test failed:', e)
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ WebRTC client test passed${NC}"
    else
        echo -e "${RED}❌ WebRTC client test failed${NC}"
        exit 1
    fi
}

show_next_steps() {
    echo -e "\n${GREEN}🎉 WebRTC setup complete!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Test WebRTC connection:"
    echo "   ./scripts/test_webrtc.py"
    echo ""
    echo "2. Switch to WebRTC protocol:"
    echo "   ./scripts/switch_protocol.sh webrtc"
    echo ""
    echo "3. Start Butler Connect with WebRTC:"
    echo "   pm2 restart butler-connect"
    echo ""
    echo -e "${YELLOW}WebRTC Features:${NC}"
    echo "• Real-time peer-to-peer communication"
    echo "• Low latency data streaming"
    echo "• Built-in NAT traversal"
    echo "• Optional video streaming support"
    echo ""
    echo -e "${YELLOW}Requirements:${NC}"
    echo "• Robot must support WebRTC signaling"
    echo "• Network connectivity to robot"
    echo "• WebRTC signaling server on robot"
}

main() {
    print_header
    
    check_python_env
    install_webrtc_deps
    verify_installation
    test_webrtc_client
    show_next_steps
}

# Handle arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo ""
        echo "This script installs and configures WebRTC support for Butler Connect."
        exit 0
        ;;
    *)
        main
        ;;
esac
