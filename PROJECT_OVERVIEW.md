# 🤖 Butler Connect - Project Overview

## What We've Built

Butler Connect is a comprehensive control system for the Unitree Go2 quadruped robot. This project provides:

### 🌟 Key Features
- **Web-based Control Interface** - Modern, responsive UI for robot control
- **Real-time Monitoring** - Live status updates via WebSocket
- **Safety-First Design** - Emergency stop and boundary monitoring
- **Motion Control** - Velocity control, trajectory planning, and gait management
- **State Monitoring** - Historical data tracking and performance analysis
- **RESTful API** - Complete API for programmatic control

### 📁 Project Structure

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

## 🚀 Getting Started

### Quick Start (Recommended)
```bash
# Windows
start.bat

# Linux/macOS  
./start.sh

# Cross-platform Python
python quick_start.py
```

### Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure robot settings
# Edit config/robot_config.yaml with your robot's IP

# 3. Start the application
python src/main.py
```

### 🌐 Access the Interface
- **Web Control Panel**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket Endpoint**: ws://localhost:8000/ws

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

## 🧪 Testing & Development

### Development Mode
```python
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with hot reload
uvicorn src.web.api_server:app --reload --host 0.0.0.0 --port 8000
```

### Safety Testing
- Test emergency stop functionality before robot operation
- Verify safety boundaries with small movements
- Check battery and temperature monitoring
- Validate connection timeout behavior

## 📈 Future Enhancements

### Planned Features
- **Autonomous Navigation** - Path planning and obstacle avoidance
- **Camera Integration** - Live video streaming and computer vision
- **Voice Control** - Speech recognition for hands-free operation
- **Mobile App** - Native mobile control interface
- **Multi-Robot Support** - Control multiple robots simultaneously

### API Extensions
- **Recording & Playback** - Motion sequence recording
- **Custom Gaits** - User-defined movement patterns
- **Sensor Data** - Extended sensor information access
- **Cloud Integration** - Remote monitoring and control

## 🛠️ Troubleshooting

### Common Issues
1. **Connection Failed** - Check robot IP address and network
2. **Import Errors** - Install missing dependencies
3. **Permission Denied** - Run with appropriate permissions
4. **Port Conflicts** - Change port in configuration

### Debug Steps
1. Check logs in `logs/` directory
2. Verify configuration files
3. Test network connectivity to robot
4. Review console output for errors

## 📞 Support

### Resources
- **Documentation**: README.md and inline code comments
- **API Docs**: http://localhost:8000/docs (when running)
- **Configuration**: YAML files in `config/` directory
- **Logs**: Application logs in `logs/` directory

### Safety Reminders
- ⚠️ Always keep emergency stop accessible
- ⚠️ Ensure adequate space for robot movement
- ⚠️ Monitor battery levels during operation
- ⚠️ Never operate without safety boundaries configured

---

**Butler Connect** - Professional-grade control system for Unitree Go2 quadruped robots.
Built with safety, reliability, and ease of use as core principles.
