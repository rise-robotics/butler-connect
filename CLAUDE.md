# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Butler Connect is a comprehensive control system for Unitree Go2 quadruped robots. It provides web-based control interface, real-time monitoring, safety systems, and supports multiple communication protocols (UDP, ROS2, WebRTC).

## Core Architecture

**Main Components:**
- `src/main.py` - Application entry point, coordinates all components
- `src/core/robot_manager.py` - Core robot communication and state management
- `src/web/api_server.py` - FastAPI server providing REST API and WebSocket interface
- `src/core/ros2_client.py` - ROS2 communication layer
- `src/core/webrtc_client.py` - Generic WebRTC communication layer
- `src/core/unitree_webrtc_client.py` - Unitree-specific WebRTC SDK integration

**Key Design Patterns:**
- **Protocol Abstraction**: RobotManager supports multiple communication protocols (UDP/ROS2/WebRTC) with fallback to mock mode
- **Async Event-Driven**: Uses asyncio for concurrent robot monitoring, command processing, and web server
- **State Management**: Centralized robot state in RobotManager with callback-based updates to API server
- **Safety-First**: Emergency stop system, boundary monitoring, and validation at multiple levels

## Development Commands

**Start Application:**
```bash
# Quick start (recommended)
python quick_start.py

# Manual start
python src/main.py

# With PM2 process manager
pm2 start ecosystem.config.js
```

**Dependencies:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# For WSL development
pip install -r requirements-wsl.txt
```

**Development Mode:**
```bash
# FastAPI with hot reload
uvicorn src.web.api_server:app --reload --host 0.0.0.0 --port 8000

# Set debug logging
export LOG_LEVEL=DEBUG
```

**Testing:**
```bash
# Run pytest (when tests exist)
pytest tests/

# Test robot simulator
python scripts/test_robot_simulator.py

# Test WebRTC functionality
python scripts/test_webrtc.py
```

## Configuration System

**Configuration Structure:**
- `config/robot_config.yaml` - Robot connection settings, protocol selection, network parameters
- `config/control_config.yaml` - Motion control limits and parameters  
- `config/safety_config.yaml` - Safety boundaries, alerts, and emergency stop settings

**Protocol Configuration:**
The system supports three communication protocols configured in `robot_config.yaml`:
- `protocol: "udp"` - Direct UDP communication (mock mode)
- `protocol: "ros2"` - ROS2 integration with cmd_vel, odom, battery topics
- `protocol: "webrtc"` - Unitree WebRTC SDK integration for direct robot communication

**Critical Config Notes:**
- Robot IP address must be set in `robot_config.yaml` for UDP/WebRTC modes
- ROS2 mode requires proper ROS_DOMAIN_ID and topic configuration
- Server host/port configurable via `server` section or PORT environment variable

## File Structure Patterns

**Source Organization:**
- `src/core/` - Robot communication and protocol implementations
- `src/web/` - FastAPI server, templates, static files
- `src/utils/` - Configuration loading, logging utilities
- `src/control/` - Motion control algorithms
- `src/safety/` - Safety monitoring systems
- `src/monitoring/` - State monitoring and data collection

**Key Integration Points:**
- `ButlerConnectApp` in main.py coordinates startup of RobotManager and APIServer
- RobotManager uses protocol factories to create ros2_client or unitree_webrtc_client
- APIServer registers callbacks with RobotManager for real-time WebSocket updates
- ConfigLoader loads all YAML configs into unified config dictionary

## Robot State Management

**RobotState Dataclass** contains:
- Connection status, battery level, temperature
- 3D position and orientation (x,y,z / roll,pitch,yaw)
- Robot mode (IDLE, WALK, RUN, STAND, SIT, etc.)
- Joint positions array for 12 DOF quadruped

**State Updates:**
- ROS2: Pulls from subscribed topics (battery_state, odom, temperature)
- WebRTC: Updates via Unitree WebRTC SDK callbacks with comprehensive robot data (battery, IMU, position, velocity, motors, mode)
- UDP/Mock: Simulates realistic state with battery drain, temperature variation

## Safety Implementation

**Multi-Layer Safety:**
1. **Emergency Stop**: Immediate motion halt via multiple triggers
2. **Boundary Checking**: Position and velocity limits from safety_config.yaml
3. **Health Monitoring**: Battery level, temperature thresholds
4. **Command Validation**: Motion limits enforced before sending commands

**Safety is checked in:**
- RobotManager._validate_motion_command() for motion limits
- RobotManager._check_safety_conditions() for ongoing monitoring
- Emergency stop accessible via API endpoint and web interface

## API Integration

**REST Endpoints:**
- `/api/robot/status` - Get current robot state
- `/api/robot/connect` - Initiate robot connection
- `/api/robot/move` - Send motion commands
- `/api/robot/stand`, `/api/robot/sit` - Posture commands
- `/api/robot/emergency_stop` - Safety override

**WebSocket Updates:**
- Real-time robot state broadcasts to connected web clients
- Error notifications and safety alerts
- Connection at `/ws` endpoint

## Development Notes

**Adding New Protocols:**
1. Create new client in `src/core/` following ros2_client.py pattern
2. Add protocol initialization in RobotManager.initialize()
3. Implement motion command sending in RobotManager.send_motion_command()
4. Add state update handling in RobotManager._update_robot_state()

**WebRTC Protocol Implementation:**
- Uses `UnitreeWebRTCClient` for direct Unitree SDK integration
- Real-time data callbacks update robot state with comprehensive sensor data
- Supports all robot commands (movement, stand, sit, stop) via SDK methods
- Provides IMU, battery, position, velocity, and joint data

**Mock Mode Behavior:**
- Falls back automatically when ROS2/WebRTC initialization fails
- Simulates realistic robot behavior for development without hardware
- Provides battery drain, temperature variation, and position updates

**Protocol-Specific Implementation Details:**
- **ROS2**: Uses standard ROS2 topics and services (cmd_vel, battery_state, stand/sit services)
- **WebRTC**: Direct Unitree SDK integration with real-time data streaming and native robot commands
- **UDP**: Mock mode for development and testing without robot hardware

**Logging:**
- Uses structured logging via utils/logger.py
- Log levels configurable in robot_config.yaml
- Separate log files for application, PM2 output, and errors
- Protocol-specific debug messages help track communication status