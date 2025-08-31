# WebRTC Communication Protocol

Butler Connect now supports WebRTC as an alternative to ROS2 for robot communication. WebRTC provides real-time, low-latency peer-to-peer communication with built-in NAT traversal.

## Features

- **Real-time Communication**: Direct peer-to-peer data streaming
- **Low Latency**: Optimized for real-time robot control
- **NAT Traversal**: Works across different network configurations
- **Video Support**: Optional video streaming from robot cameras
- **Data Channels**: Binary data transmission for sensor readings
- **Fallback Option**: Use when ROS2 is not available

## Quick Start

### 1. Install Dependencies

```bash
# Install WebRTC libraries
./scripts/setup_webrtc.sh
```

### 2. Switch to WebRTC Protocol

```bash
# Interactive mode
./scripts/switch_protocol.sh

# Or direct command
./scripts/switch_protocol.sh webrtc --restart
```

### 3. Test Connection

```bash
# Test WebRTC connectivity
./scripts/test_webrtc.py
```

## Configuration

WebRTC settings are configured in `config/robot_config.yaml`:

```yaml
robot:
  ip: "192.168.100.94"  # Your robot's IP
  protocol: "webrtc"    # Use WebRTC protocol
  
  webrtc:
    signaling_port: 8765      # WebRTC signaling port
    video_enabled: true       # Enable video streaming
    data_channel_enabled: true # Enable data channels
    ice_servers:              # STUN/TURN servers for NAT traversal
      - urls: "stun:stun.l.google.com:19302"
      - urls: "stun:stun1.l.google.com:19302"
```

## Robot-Side Requirements

Your Unitree robot needs to support WebRTC signaling. This typically involves:

1. **WebRTC Signaling Server**: Running on the robot to handle connection setup
2. **Data Channel Support**: For sending sensor data (battery, odometry, temperature)
3. **Video Stream**: Optional camera feed via WebRTC
4. **Command Handling**: Processing movement commands received via data channels

## Data Format

### Sensor Data (Robot → Butler Connect)

**Battery Data:**
```json
{
  "type": "battery",
  "percentage": 85,
  "voltage": 24.2,
  "current": -2.1,
  "temperature": 25.0
}
```

**Odometry Data:**
```json
{
  "type": "odometry", 
  "position": {"x": 1.5, "y": 0.3, "z": 0.0},
  "orientation": {"x": 0.0, "y": 0.0, "z": 0.1, "w": 0.99},
  "linear_velocity": {"x": 0.2, "y": 0.0, "z": 0.0},
  "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.05}
}
```

**Temperature Data:**
```json
{
  "type": "temperature",
  "temperature": 45.2,
  "location": "cpu"
}
```

### Commands (Butler Connect → Robot)

**Movement Command:**
```json
{
  "type": "velocity",
  "linear": {"x": 0.5, "y": 0.0, "z": 0.0},
  "angular": {"x": 0.0, "y": 0.0, "z": 0.2}
}
```

## Troubleshooting

### Connection Issues

1. **Check Network Connectivity:**
   ```bash
   ping 192.168.100.94  # Your robot IP
   ```

2. **Verify Signaling Port:**
   ```bash
   telnet 192.168.100.94 8765
   ```

3. **Test WebRTC Client:**
   ```bash
   ./scripts/test_webrtc.py
   ```

### No Sensor Data

1. **Check Robot WebRTC Server**: Ensure the robot is running WebRTC signaling
2. **Verify Data Channels**: Check if data channels are properly established
3. **Protocol Compatibility**: Confirm robot supports the expected data format

### Video Issues

1. **Disable Video**: Set `video_enabled: false` for testing
2. **Bandwidth**: Check network bandwidth for video streaming
3. **Codecs**: Ensure compatible video codecs between robot and client

## Protocol Switching

You can easily switch between protocols:

```bash
# Switch to ROS2
./scripts/switch_protocol.sh ros2 --restart

# Switch to WebRTC  
./scripts/switch_protocol.sh webrtc --restart

# Switch to UDP (simulation)
./scripts/switch_protocol.sh udp --restart
```

## Development

### Adding New Data Types

1. **Update WebRTC Client** (`src/core/webrtc_client.py`):
   - Add new message parser in `_parse_binary_message()`
   - Create new callback method
   - Add callback setter method

2. **Update Robot Manager** (`src/core/robot_manager.py`):
   - Add callback setup in WebRTC initialization
   - Handle new data type in state updates

3. **Update API** (`src/web/api_server.py`):
   - Add new endpoint if needed
   - Include new data in WebSocket broadcasts

### Testing WebRTC Changes

```bash
# Test WebRTC client directly
./scripts/test_webrtc.py

# Test full integration
pm2 restart butler-connect
pm2 logs butler-connect
```

## Comparison: WebRTC vs ROS2

| Feature | WebRTC | ROS2 |
|---------|--------|------|
| **Latency** | Very Low | Low-Medium |
| **Setup Complexity** | Medium | High |
| **Network Traversal** | Built-in NAT | Manual configuration |
| **Video Streaming** | Native | Additional packages |
| **Ecosystem** | Limited | Extensive |
| **Robot Support** | Custom implementation | Standard |
| **Development** | Web-focused | Robotics-focused |

## When to Use WebRTC

- **Network Challenges**: Behind NATs or firewalls
- **Low Latency**: Real-time control requirements  
- **Video Streaming**: Integrated camera feeds
- **Simplified Deployment**: Less infrastructure setup
- **ROS2 Unavailable**: When ROS2 can't be installed/configured

## When to Use ROS2

- **Standard Robotics**: Industry-standard robotics middleware
- **Rich Ecosystem**: Extensive packages and tools
- **Complex Applications**: Multi-robot or advanced scenarios
- **Robot Native**: When robot already supports ROS2
- **Development Tools**: Superior debugging and visualization

---

*For more information, see the [Butler Connect Documentation](README.md)*
