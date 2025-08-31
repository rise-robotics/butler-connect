# 🤖 Butler Connect

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Professional Control System for Unitree Go2 Quadruped Robot**

Butler Connect is a comprehensive, safety-first control system designed for the Unitree Go2 quadruped robot. It provides an intuitive web interface, robust safety monitoring, and professional-grade motion control capabilities.

## ✨ Features

- **🌐 Web-Based Control Interface** - Modern, responsive UI with real-time robot control
- **🛡️ Safety-First Design** - Multiple emergency stop mechanisms and boundary monitoring  
- **🎮 Advanced Motion Control** - Velocity control, gait management, and trajectory planning
- **📊 Real-Time Monitoring** - Live status updates, data logging, and performance analysis
- **🔌 RESTful API** - Complete API for programmatic control and integration
- **⚡ WebSocket Support** - Real-time updates and live data streaming
- **📱 Cross-Platform** - Works on Windows, Linux, and macOS
- **🔧 Configurable** - Extensive configuration options for customization

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Unitree Go2 robot connected to network
- Network connectivity to robot's IP address

### Installation & Startup

#### Option 1: Quick Start Scripts (Recommended)
```bash
# Windows
start.bat

# Linux/macOS
./start.sh

# Cross-platform Python script
python quick_start.py
```

#### Option 2: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure robot settings (edit config/robot_config.yaml)
# Set your robot's IP address

# 3. Start the application
python src/main.py
```

### 🌐 Access the Interface
- **Web Control Panel**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs  
- **WebSocket Endpoint**: ws://localhost:8000/ws

## 📁 Project Structure

```
butler-connect/
├── 📋 README.md                      # Project documentation
├── 📦 requirements.txt               # Python dependencies
├── 🚀 quick_start.py                 # Cross-platform setup script
├── 🪟 start.bat                      # Windows launcher
├── 🐧 start.sh                       # Linux/macOS launcher
├── 
├── config/                           # Configuration files
│   ├── 🤖 robot_config.yaml         # Robot connection settings
│   ├── 🎮 control_config.yaml       # Motion control parameters
│   └── 🛡️ safety_config.yaml        # Safety boundaries and alerts
├── 
├── src/                              # Source code
│   ├── 🎯 main.py                    # Application entry point
│   ├── 
│   ├── core/                         # Core robot functionality
│   │   └── 🧠 robot_manager.py       # Robot communication & state
│   ├── 
│   ├── control/                      # Motion control systems
│   │   └── 🎮 motion_controller.py   # High-level movement control
│   ├── 
│   ├── safety/                       # Safety monitoring
│   │   └── 🛡️ safety_monitor.py      # Safety checks & emergency stop
│   ├── 
│   ├── monitoring/                   # State monitoring
│   │   └── 📊 state_monitor.py       # Data logging & analysis
│   ├── 
│   ├── web/                          # Web interface
│   │   ├── 🌐 api_server.py          # FastAPI server & routes
│   │   └── templates/
│   │       └── 🎨 index.html         # Web control interface
│   └── 
│   └── utils/                        # Utility modules
│       ├── ⚙️ config_loader.py       # Configuration management
│       └── 📝 logger.py              # Logging system
└── 
└── logs/                             # Application logs (created at runtime)
```

## 🎮 Control Features

### Web Interface
- **Connection Management** - Connect/disconnect from robot
- **Movement Controls** - Directional buttons and virtual joystick
- **Safety Controls** - Emergency stop and gait selection
- **Real-time Status** - Battery, temperature, position monitoring
- **Visual Feedback** - Status indicators and alerts

### API Endpoints
- `POST /api/robot/connect` - Connect to robot
- `POST /api/robot/disconnect` - Disconnect from robot
- `GET /api/robot/status` - Get current status
- `POST /api/robot/move` - Send movement commands
- `POST /api/robot/stop` - Stop all movement
- `POST /api/robot/emergency_stop` - Emergency stop

### Movement Control
- **Velocity Control** - Linear X/Y and angular Z movement
- **Gait Management** - Walk, trot, and run gaits
- **Trajectory Planning** - Smooth path execution
- **Safety Limits** - Configurable velocity and position limits

## 🛡️ Safety Features

### Emergency Stop System
- **Hardware Emergency Stop** - Immediate motion halt
- **Web Emergency Stop** - One-click safety button
- **API Emergency Stop** - Programmatic safety trigger
- **Auto-Recovery** - Safe restart procedures

### Boundary Monitoring
- **Position Limits** - X/Y/Z position boundaries
- **Velocity Limits** - Maximum speed restrictions
- **Temperature Monitoring** - Overheat protection
- **Battery Monitoring** - Low battery alerts

### Safety Alerts
- **Real-time Monitoring** - Continuous safety checks
- **Visual Alerts** - Web interface warnings
- **Audio Alerts** - System notification sounds
- **Logged Events** - Safety incident recording

## 📊 Monitoring & Logging

### State Monitoring
- **Real-time Data** - Live robot state updates
- **Historical Tracking** - Time-series data storage
- **Performance Metrics** - Movement efficiency analysis
- **Data Export** - JSON/CSV export capabilities

### Logging System
- **Structured Logging** - JSON formatted logs
- **Log Rotation** - Automatic file management
- **Multiple Levels** - Debug, info, warning, error
- **Console & File** - Dual output destinations

## ⚙️ Configuration

### Robot Configuration (`robot_config.yaml`)
```yaml
connection:
  ip_address: "192.168.123.161"  # Robot's IP address
  udp_port: 8082                 # Main communication port
  low_level_port: 8007          # Low-level control port
  timeout: 5                     # Connection timeout
```

### Control Configuration (`control_config.yaml`)
```yaml
limits:
  max_linear_velocity: 1.0      # m/s
  max_angular_velocity: 2.0     # rad/s
  max_step_height: 0.2          # m
```

### Safety Configuration (`safety_config.yaml`)
```yaml
boundaries:
  position_x: [-2.0, 2.0]       # X-axis limits (m)
  position_y: [-2.0, 2.0]       # Y-axis limits (m)
  min_battery_level: 20         # Minimum battery %
```

## 🔧 Technical Architecture

### Core Components
- **RobotManager** - Handles robot communication and state
- **MotionController** - High-level movement coordination
- **SafetyMonitor** - Continuous safety oversight
- **StateMonitor** - Data collection and analysis
- **APIServer** - Web interface and REST API

### Communication Protocol
- **UDP Communication** - Primary robot communication
- **WebSocket Updates** - Real-time web interface updates
- **JSON Messaging** - Structured data exchange
- **Error Handling** - Robust error recovery

### Data Flow
```
Web Interface ← WebSocket ← APIServer ← RobotManager ← Robot
                     ↓           ↓            ↓
               SafetyMonitor StateMonitor  Database
```

## 🧪 Development

### Development Setup
```bash
# Clone repository
git clone https://github.com/risebt/butler-connect.git
cd butler-connect

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn src.web.api_server:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests (when implemented)
pytest tests/

# Safety testing checklist:
# ✅ Test emergency stop functionality
# ✅ Verify safety boundaries
# ✅ Check battery monitoring
# ✅ Validate connection timeout
```

## 🛠️ Troubleshooting

### Common Issues
1. **Connection Failed** - Check robot IP address and network
2. **Import Errors** - Install missing dependencies with `pip install -r requirements.txt`
3. **Permission Denied** - Run with appropriate permissions
4. **Port Conflicts** - Change port in configuration

### Debug Steps
1. Check logs in `logs/` directory
2. Verify configuration files in `config/`
3. Test network connectivity to robot
4. Review console output for errors

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for new features
- Ensure safety features are thoroughly tested

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About RISE Building Technology

Developed by RISE Building Technology - Leaders in innovative building automation and robotics solutions.

- **Website**: https://risetechnology.com.au
- **Email**: rav@risetechnology.com.au
- **Location**: Brisbane, Australia

## 📞 Support

For support and questions:
- **Create an Issue**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check the `/docs` directory for detailed documentation
- **API Docs**: Available at http://localhost:8000/docs when running

## ⚠️ Safety Disclaimer

**IMPORTANT**: Always prioritize safety when operating robotic systems:
- Keep emergency stop accessible at all times
- Ensure adequate space for robot movement
- Monitor battery levels during operation
- Never operate without safety boundaries configured
- Supervise robot operation continuously

## 🏷️ Version History

- **v1.0.0** - Initial release with core functionality
  - Web interface and API
  - Safety monitoring system
  - Motion control capabilities
  - Real-time state monitoring

---

**Butler Connect** - Professional-grade control system for Unitree Go2 quadruped robots.
