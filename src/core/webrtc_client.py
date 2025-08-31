"""
WebRTC Client for Unitree Go2 Robot Communication
Provides real-time video and data streaming capabilities
"""

import asyncio
import json
import logging
import struct
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

try:
    from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
    from aiortc.contrib.media import MediaPlayer, MediaRelay
    from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    RTCPeerConnection = None
    RTCConfiguration = None
    RTCIceServer = None

from utils.logger import get_logger


@dataclass
class WebRTCConfig:
    """WebRTC configuration"""
    robot_ip: str = "192.168.123.161"
    signaling_port: int = 8080
    ice_servers: list = None
    video_enabled: bool = True
    data_channel_enabled: bool = True
    
    def __post_init__(self):
        if self.ice_servers is None:
            self.ice_servers = [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"}
            ]


class WebRTCClient:
    """WebRTC client for Unitree Go2 robot communication"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        
        # Get WebRTC configuration and override robot IP from robot section
        webrtc_config = config.get('webrtc', {})
        robot_config = config.get('robot', {})
        
        # Use robot IP from robot config, fallback to webrtc config, then default
        robot_ip = (robot_config.get('ip_address') or 
                   webrtc_config.get('robot_ip', '192.168.123.161'))
        webrtc_config['robot_ip'] = robot_ip
        
        self.config = WebRTCConfig(**webrtc_config)
        
        # WebRTC components
        self.pc: Optional[RTCPeerConnection] = None
        self.data_channel = None
        self.video_track = None
        
        # Connection state
        self.is_connected = False
        self.is_initialized = False
        
        # Data callbacks
        self.battery_callback: Optional[Callable] = None
        self.odometry_callback: Optional[Callable] = None
        self.temperature_callback: Optional[Callable] = None
        self.video_callback: Optional[Callable] = None
        
        # State tracking
        self.last_battery_data = None
        self.last_odom_data = None
        self.last_temp_data = None
        
        if not WEBRTC_AVAILABLE:
            self.logger.error("WebRTC dependencies not available. Install with: pip install aiortc av")
    
    def initialize(self) -> bool:
        """Initialize WebRTC client"""
        try:
            if not WEBRTC_AVAILABLE:
                self.logger.error("WebRTC not available - missing dependencies")
                return False
            
            # Create RTCConfiguration
            ice_servers = [RTCIceServer(server["urls"]) for server in self.config.ice_servers]
            configuration = RTCConfiguration(iceServers=ice_servers)
            
            # Create peer connection
            self.pc = RTCPeerConnection(configuration)
            
            # Set up event handlers
            self._setup_connection_handlers()
            
            self.is_initialized = True
            self.logger.info(f"WebRTC client initialized for robot at {self.config.robot_ip}")
            return True
            
        except Exception as e:
            self.logger.error(f"WebRTC initialization failed: {e}")
            return False
    
    def _setup_connection_handlers(self):
        """Set up WebRTC connection event handlers"""
        if not self.pc:
            return
        
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            state = self.pc.connectionState
            self.logger.info(f"WebRTC connection state: {state}")
            self.is_connected = state == "connected"
            
            if state == "failed":
                await self.close()
        
        @self.pc.on("datachannel")
        def on_datachannel(channel):
            self.logger.info(f"Data channel created: {channel.label}")
            
            @channel.on("open")
            def on_open():
                self.logger.info("Data channel opened")
            
            @channel.on("message")
            def on_message(message):
                try:
                    self._handle_data_message(message)
                except Exception as e:
                    self.logger.error(f"Error handling data message: {e}")
        
        @self.pc.on("track")
        def on_track(track):
            self.logger.info(f"Track received: {track.kind}")
            if track.kind == "video":
                self.video_track = track
                if self.video_callback:
                    # Set up video frame processing
                    asyncio.create_task(self._process_video_frames())
    
    def _handle_data_message(self, message):
        """Handle incoming data channel messages"""
        try:
            if isinstance(message, str):
                data = json.loads(message)
            else:
                # Binary data - parse based on message type
                data = self._parse_binary_message(message)
            
            msg_type = data.get('type', '')
            
            if msg_type == 'battery_state' and self.battery_callback:
                self.last_battery_data = data
                self.battery_callback(data)
            elif msg_type == 'odometry' and self.odometry_callback:
                self.last_odom_data = data
                self.odometry_callback(data)
            elif msg_type == 'temperature' and self.temperature_callback:
                self.last_temp_data = data
                self.temperature_callback(data)
            else:
                self.logger.debug(f"Unhandled message type: {msg_type}")
                
        except Exception as e:
            self.logger.error(f"Error parsing data message: {e}")
    
    def _parse_binary_message(self, message: bytes) -> Dict[str, Any]:
        """Parse binary message from robot"""
        try:
            # Basic binary protocol parsing
            # This would need to match your robot's specific protocol
            if len(message) < 8:
                return {}
            
            # Example: first 4 bytes = message type, next 4 bytes = data length
            msg_type = struct.unpack('<I', message[:4])[0]
            data_len = struct.unpack('<I', message[4:8])[0]
            
            if msg_type == 1:  # Battery data
                if len(message) >= 16:
                    voltage = struct.unpack('<f', message[8:12])[0]
                    percentage = struct.unpack('<f', message[12:16])[0]
                    return {
                        'type': 'battery_state',
                        'voltage': voltage,
                        'percentage': percentage,
                        'timestamp': time.time()
                    }
            elif msg_type == 2:  # Odometry data
                if len(message) >= 32:
                    x = struct.unpack('<f', message[8:12])[0]
                    y = struct.unpack('<f', message[12:16])[0]
                    z = struct.unpack('<f', message[16:20])[0]
                    roll = struct.unpack('<f', message[20:24])[0]
                    pitch = struct.unpack('<f', message[24:28])[0]
                    yaw = struct.unpack('<f', message[28:32])[0]
                    return {
                        'type': 'odometry',
                        'position': [x, y, z],
                        'orientation': [roll, pitch, yaw],
                        'timestamp': time.time()
                    }
            elif msg_type == 3:  # Temperature data
                if len(message) >= 12:
                    temp = struct.unpack('<f', message[8:12])[0]
                    return {
                        'type': 'temperature',
                        'temperature': temp,
                        'timestamp': time.time()
                    }
            
            return {'type': 'unknown', 'raw_data': message}
            
        except Exception as e:
            self.logger.error(f"Error parsing binary message: {e}")
            return {}
    
    async def _process_video_frames(self):
        """Process incoming video frames"""
        if not self.video_track or not self.video_callback:
            return
        
        try:
            while True:
                frame = await self.video_track.recv()
                if self.video_callback:
                    self.video_callback(frame)
                await asyncio.sleep(0.033)  # ~30 FPS
        except Exception as e:
            self.logger.error(f"Video processing error: {e}")
    
    async def connect(self) -> bool:
        """Connect to robot via WebRTC"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return False
            
            # Create data channel for robot communication
            if self.config.data_channel_enabled:
                self.data_channel = self.pc.createDataChannel("robot_data")
                self.logger.info("Data channel created for robot communication")
            
            # Create offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            # Send offer to robot (this would need robot-specific signaling)
            await self._send_offer_to_robot(offer)
            
            # Wait for connection
            timeout = 10.0
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.1)
            
            if self.is_connected:
                self.logger.info("WebRTC connection established")
                return True
            else:
                self.logger.error("WebRTC connection timeout")
                return False
                
        except Exception as e:
            self.logger.error(f"WebRTC connection failed: {e}")
            return False
    
    async def _send_offer_to_robot(self, offer):
        """Send WebRTC offer to robot (robot-specific implementation needed)"""
        # This would need to be implemented based on your robot's signaling protocol
        # For now, this is a placeholder
        self.logger.info("Sending WebRTC offer to robot (implementation needed)")
        
        # Example: HTTP POST to robot's WebRTC endpoint
        # You would implement this based on your robot's API
        pass
    
    async def send_command(self, command: Dict[str, Any]) -> bool:
        """Send command to robot via data channel"""
        try:
            if not self.data_channel or self.data_channel.readyState != "open":
                self.logger.error("Data channel not available")
                return False
            
            message = json.dumps(command)
            self.data_channel.send(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            return False
    
    def set_battery_callback(self, callback: Callable):
        """Set callback for battery data"""
        self.battery_callback = callback
    
    def set_odometry_callback(self, callback: Callable):
        """Set callback for odometry data"""
        self.odometry_callback = callback
    
    def set_temperature_callback(self, callback: Callable):
        """Set callback for temperature data"""
        self.temperature_callback = callback
    
    def set_video_callback(self, callback: Callable):
        """Set callback for video frames"""
        self.video_callback = callback
    
    def get_last_battery_data(self) -> Optional[Dict[str, Any]]:
        """Get last received battery data"""
        return self.last_battery_data
    
    def get_last_odometry_data(self) -> Optional[Dict[str, Any]]:
        """Get last received odometry data"""
        return self.last_odom_data
    
    def get_last_temperature_data(self) -> Optional[Dict[str, Any]]:
        """Get last received temperature data"""
        return self.last_temp_data
    
    async def close(self):
        """Close WebRTC connection"""
        try:
            if self.data_channel:
                self.data_channel.close()
            
            if self.pc:
                await self.pc.close()
            
            self.is_connected = False
            self.logger.info("WebRTC connection closed")
            
        except Exception as e:
            self.logger.error(f"Error closing WebRTC connection: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
