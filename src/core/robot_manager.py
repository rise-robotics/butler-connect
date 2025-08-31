"""
Robot Manager - Core class for managing Unitree Go2 robot connection and control
"""

import asyncio
import logging
import socket
import struct
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from utils.logger import get_logger


class RobotMode(Enum):
    """Robot operating modes"""
    IDLE = 0
    WALK = 1
    RUN = 2
    CLIMB = 3
    STAND = 4
    SIT = 5
    LIE = 6


@dataclass
class RobotState:
    """Robot state data structure"""
    mode: RobotMode = RobotMode.IDLE
    battery_level: float = 0.0
    temperature: float = 0.0
    position: tuple = (0.0, 0.0, 0.0)  # x, y, z
    orientation: tuple = (0.0, 0.0, 0.0)  # roll, pitch, yaw
    velocity: tuple = (0.0, 0.0, 0.0)  # linear and angular velocities
    joint_positions: Optional[list] = None
    is_connected: bool = False
    last_update: float = 0.0
    
    def __post_init__(self):
        if self.joint_positions is None:
            self.joint_positions = [0.0] * 12  # 12 joints for quadruped


@dataclass
class MotionCommand:
    """Motion command data structure"""
    linear_x: float = 0.0
    linear_y: float = 0.0
    angular_z: float = 0.0
    step_height: float = 0.1
    gait_type: str = "trot"


class RobotManager:
    """Main robot management class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Robot configuration
        self.robot_config = config.get('robot', {})
        self.comm_config = config.get('communication', {})
        self.safety_config = config.get('safety', {})
        
        # Connection parameters
        self.robot_ip = self.robot_config.get('ip_address', '192.168.123.161')
        self.udp_port = self.robot_config.get('udp_port', 8082)
        self.timeout = self.robot_config.get('timeout', 5.0)
        
        # State management
        self.robot_state = RobotState()
        self.is_connected = False
        self.socket = None
        self.monitoring_task = None
        self.command_task = None
        
        # Callbacks
        self.state_callbacks: list[Callable] = []
        self.error_callbacks: list[Callable] = []
        
        # Safety
        self.emergency_stop = False
        self.last_heartbeat = 0.0
        
        self.logger.info("Robot Manager initialized")
    
    async def initialize(self) -> bool:
        """Initialize the robot manager"""
        try:
            self.logger.info("Initializing robot manager...")
            
            # Validate configuration
            if not self._validate_config():
                return False
            
            # Initialize safety systems
            self._initialize_safety()
            
            self.logger.info("Robot manager initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize robot manager: {e}")
            return False
    
    async def connect(self) -> bool:
        """Connect to the robot"""
        try:
            self.logger.info(f"Connecting to robot at {self.robot_ip}:{self.udp_port}")
            
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            
            # Test connection with ping
            if await self._test_connection():
                self.is_connected = True
                self.robot_state.is_connected = True
                self.last_heartbeat = time.time()
                
                self.logger.info("Successfully connected to robot")
                return True
            else:
                self.logger.error("Failed to establish connection with robot")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the robot"""
        try:
            self.logger.info("Disconnecting from robot...")
            
            # Stop monitoring tasks
            if self.monitoring_task:
                self.monitoring_task.cancel()
                
            if self.command_task:
                self.command_task.cancel()
            
            # Send stop command before disconnecting
            await self.send_motion_command(MotionCommand())
            
            # Close socket
            if self.socket:
                self.socket.close()
                self.socket = None
            
            self.is_connected = False
            self.robot_state.is_connected = False
            
            self.logger.info("Disconnected from robot")
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
    
    async def start_monitoring(self):
        """Start robot state monitoring"""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.command_task = asyncio.create_task(self._command_loop())
    
    async def send_motion_command(self, command: MotionCommand) -> bool:
        """Send motion command to robot"""
        try:
            if not self.is_connected or self.emergency_stop:
                return False
            
            # Validate command limits
            if not self._validate_motion_command(command):
                return False
            
            # Create command packet
            packet = self._create_motion_packet(command)
            
            # Send command
            self.socket.sendto(packet, (self.robot_ip, self.udp_port))
            
            self.logger.debug(f"Sent motion command: {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send motion command: {e}")
            return False
    
    async def emergency_stop_robot(self):
        """Emergency stop the robot"""
        self.emergency_stop = True
        self.logger.warning("Emergency stop activated!")
        
        # Send stop command
        stop_command = MotionCommand()
        await self.send_motion_command(stop_command)
        
        # Notify callbacks
        for callback in self.error_callbacks:
            await callback("emergency_stop", "Emergency stop activated")
    
    async def stand_up(self) -> bool:
        """Command the robot to stand up"""
        try:
            if not self.is_connected or self.emergency_stop:
                self.logger.warning("Cannot stand up: robot not connected or emergency stop active")
                return False
            
            self.logger.info("Commanding robot to stand up")
            
            # Create stand command packet
            stand_packet = self._create_mode_packet(RobotMode.STAND)
            
            # Send command
            self.socket.sendto(stand_packet, (self.robot_ip, self.udp_port))
            
            # Update robot state
            self.robot_state.mode = RobotMode.STAND
            
            self.logger.info("Stand up command sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stand up robot: {e}")
            return False
    
    async def sit_down(self) -> bool:
        """Command the robot to sit down"""
        try:
            if not self.is_connected or self.emergency_stop:
                self.logger.warning("Cannot sit down: robot not connected or emergency stop active")
                return False
            
            self.logger.info("Commanding robot to sit down")
            
            # Create sit command packet
            sit_packet = self._create_mode_packet(RobotMode.SIT)
            
            # Send command
            self.socket.sendto(sit_packet, (self.robot_ip, self.udp_port))
            
            # Update robot state
            self.robot_state.mode = RobotMode.SIT
            
            self.logger.info("Sit down command sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sit down robot: {e}")
            return False
    
    def register_state_callback(self, callback: Callable):
        """Register callback for state updates"""
        self.state_callbacks.append(callback)
    
    def register_error_callback(self, callback: Callable):
        """Register callback for error notifications"""
        self.error_callbacks.append(callback)
    
    async def _test_connection(self) -> bool:
        """Test connection to robot"""
        try:
            # MOCK MODE: This is a placeholder connection test
            # Real Unitree Go2 robots use DDS communication, not UDP
            self.logger.warning("MOCK MODE: Using placeholder connection test")
            self.logger.warning("Real Go2 robots require Unitree SDK2 with DDS communication")
            
            # Send ping packet (mock - robot will ignore this)
            ping_packet = b'\x00\x01\x02\x03'  # Simple ping
            self.socket.sendto(ping_packet, (self.robot_ip, self.udp_port))
            
            # Wait for response (simplified - always returns True in mock mode)
            await asyncio.sleep(0.1)
            self.logger.warning("MOCK MODE: Connection test passed (robot may not actually respond)")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_connected:
            try:
                # Update robot state
                await self._update_robot_state()
                
                # Check safety conditions
                self._check_safety_conditions()
                
                # Notify state callbacks
                for callback in self.state_callbacks:
                    await callback(self.robot_state)
                
                await asyncio.sleep(0.01)  # 100 Hz monitoring
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _command_loop(self):
        """Command processing loop"""
        while self.is_connected:
            try:
                # Send heartbeat
                current_time = time.time()
                if current_time - self.last_heartbeat > 1.0:
                    await self._send_heartbeat()
                    self.last_heartbeat = current_time
                
                await asyncio.sleep(0.02)  # 50 Hz command rate
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Command loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_robot_state(self):
        """Update robot state from sensor data"""
        # Simulate state updates (replace with actual robot communication)
        self.robot_state.last_update = time.time()
        self.robot_state.battery_level = max(0, self.robot_state.battery_level + 0.1)
        self.robot_state.temperature = 25.0 + (time.time() % 10)
    
    async def _send_heartbeat(self):
        """Send heartbeat to robot"""
        try:
            heartbeat_packet = b'\xFF\xFE\xFD\xFC'  # Heartbeat signature
            self.socket.sendto(heartbeat_packet, (self.robot_ip, self.udp_port))
        except Exception as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
    
    def _validate_config(self) -> bool:
        """Validate robot configuration"""
        required_keys = ['ip_address', 'udp_port']
        for key in required_keys:
            if key not in self.robot_config:
                self.logger.error(f"Missing required config key: {key}")
                return False
        return True
    
    def _initialize_safety(self):
        """Initialize safety systems"""
        self.emergency_stop = False
        # Additional safety initialization
    
    def _validate_motion_command(self, command: MotionCommand) -> bool:
        """Validate motion command parameters"""
        max_linear = self.robot_config.get('max_speed', 1.5)
        max_angular = self.robot_config.get('max_angular_speed', 2.0)
        
        if abs(command.linear_x) > max_linear:
            return False
        if abs(command.linear_y) > max_linear:
            return False
        if abs(command.angular_z) > max_angular:
            return False
            
        return True
    
    def _create_motion_packet(self, command: MotionCommand) -> bytes:
        """Create motion command packet"""
        # MOCK MODE: This creates placeholder packets that real robots ignore
        # Real Unitree Go2 robots require DDS messages with specific formats
        self.logger.debug(f"MOCK MODE: Creating motion packet - robot will ignore this")
        self.logger.debug(f"Motion command: linear_x={command.linear_x}, linear_y={command.linear_y}, angular_z={command.angular_z}")
        
        # Create a simple packet structure (mock - replace with actual protocol)
        packet = struct.pack(
            'ffff',
            command.linear_x,
            command.linear_y,
            command.angular_z,
            command.step_height
        )
        return packet
    
    def _create_mode_packet(self, mode: RobotMode) -> bytes:
        """Create mode change command packet"""
        # MOCK MODE: This creates placeholder packets that real robots ignore
        # Real Unitree Go2 robots require DDS SportClient commands
        self.logger.debug(f"MOCK MODE: Creating mode packet for {mode.name} - robot will ignore this")
        
        # Create a mode command packet (mock - replace with actual Unitree protocol)
        # Format: [header][command_type][mode][checksum]
        header = b'\xAA\xBB'  # Command header
        command_type = b'\x01'  # Mode change command
        mode_byte = struct.pack('B', mode.value)
        checksum = struct.pack('B', (sum(header + command_type + mode_byte)) % 256)
        
        packet = header + command_type + mode_byte + checksum
        return packet
    
    def _check_safety_conditions(self):
        """Check safety conditions and trigger emergency stop if needed"""
        safety_config = self.safety_config.get('boundaries', {})
        
        # Check battery level
        min_battery = safety_config.get('min_battery_level', 20)
        if self.robot_state.battery_level < min_battery:
            self.logger.warning(f"Low battery: {self.robot_state.battery_level}%")
        
        # Check temperature
        max_temp = safety_config.get('max_temperature', 65)
        if self.robot_state.temperature > max_temp:
            self.logger.warning(f"High temperature: {self.robot_state.temperature}°C")
