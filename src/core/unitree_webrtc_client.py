"""
Unitree WebRTC Client using go2_webrtc_connect SDK
Enhanced WebRTC communication with proper Unitree protocol support
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD

class UnitreeWebRTCClient:
    """Enhanced WebRTC client for Unitree Go2 robot using official SDK"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.robot_config = config.get('robot', {})
        self.webrtc_config = config.get('webrtc', {})
        
        # Get robot IP from config
        self.robot_ip = self.robot_config.get('ip_address', '192.168.100.94')
        self.connection = None
        
        # Data storage for latest sensor readings
        self.latest_data = {
            'battery': {'level': 0, 'voltage': 0, 'current': 0, 'temperature': 0},
            'imu': {'roll': 0, 'pitch': 0, 'yaw': 0, 'gyroscope': [0, 0, 0], 'accelerometer': [0, 0, 0]},
            'motors': [],
            'position': {'x': 0, 'y': 0, 'z': 0},
            'velocity': {'x': 0, 'y': 0, 'z': 0},
            'foot_force': [0, 0, 0, 0],
            'body_height': 0,
            'mode': 0,
            'connected': False
        }
        
        # Data callbacks for real-time updates
        self.data_callbacks = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    async def connect(self) -> bool:
        """Connect to Unitree robot using WebRTC"""
        try:
            self.logger.info(f"Connecting to Unitree robot at {self.robot_ip}")
            
            # Try LocalSTA method first (robot connected via router)
            try:
                self.logger.info(f"Trying LocalSTA connection method with IP {self.robot_ip}...")
                self.connection = Go2WebRTCConnection(
                    WebRTCConnectionMethod.LocalSTA, 
                    ip=self.robot_ip
                )
                await self.connection.connect()
                self.logger.info("Successfully connected using LocalSTA method")
            except Exception as e:
                self.logger.warning(f"LocalSTA connection failed: {e}")
                
                # Fall back to LocalAP if STA fails
                try:
                    self.logger.info("Trying LocalAP connection method...")
                    self.connection = Go2WebRTCConnection(WebRTCConnectionMethod.LocalAP)
                    await self.connection.connect()
                    self.logger.info("Successfully connected using LocalAP method")
                except Exception as e2:
                    self.logger.error(f"Both connection methods failed. LocalAP: {e}, LocalSTA: {e2}")
                    raise e2
            
            # Subscribe to various data topics
            self._setup_subscriptions()
            
            self.latest_data['connected'] = True
            self.logger.info("Successfully connected to Unitree robot")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to robot: {e}")
            self.latest_data['connected'] = False
            return False
    
    def _setup_subscriptions(self):
        """Setup subscriptions to robot data topics"""
        if not self.connection:
            return
            
        # Subscribe to low-level state (detailed sensor data)
        self.connection.datachannel.pub_sub.subscribe(
            RTC_TOPIC['LOW_STATE'], 
            self._handle_low_state
        )
        
        # Subscribe to sport mode state (higher-level movement data)
        self.connection.datachannel.pub_sub.subscribe(
            RTC_TOPIC['LF_SPORT_MOD_STATE'], 
            self._handle_sport_mode_state
        )
        
        # Subscribe to battery/multiple state data
        self.connection.datachannel.pub_sub.subscribe(
            RTC_TOPIC['MULTIPLE_STATE'], 
            self._handle_multiple_state
        )
        
    def _handle_low_state(self, message):
        """Handle low-level state data (motors, IMU, battery)"""
        try:
            data = message['data']
            
            # Update IMU data
            if 'imu_state' in data:
                imu = data['imu_state']
                if 'rpy' in imu and len(imu['rpy']) >= 3:
                    self.latest_data['imu']['roll'] = imu['rpy'][0]
                    self.latest_data['imu']['pitch'] = imu['rpy'][1]
                    self.latest_data['imu']['yaw'] = imu['rpy'][2]
                if 'gyroscope' in imu:
                    self.latest_data['imu']['gyroscope'] = imu['gyroscope']
                if 'accelerometer' in imu:
                    self.latest_data['imu']['accelerometer'] = imu['accelerometer']
                if 'temperature' in imu:
                    self.latest_data['imu']['temperature'] = imu['temperature']
            
            # Update motor data
            if 'motor_state' in data:
                motors = []
                for i, motor in enumerate(data['motor_state']):
                    motors.append({
                        'id': i,
                        'position': motor.get('q', 0),
                        'velocity': motor.get('dq', 0),
                        'torque': motor.get('tau_est', 0),
                        'temperature': motor.get('temperature', 0),
                        'lost': motor.get('lost', False)
                    })
                self.latest_data['motors'] = motors
            
            # Update battery data
            if 'bms_state' in data:
                bms = data['bms_state']
                self.latest_data['battery'].update({
                    'level': bms.get('soc', 0),
                    'voltage': bms.get('voltage', 0) / 1000.0,  # Convert mV to V
                    'current': bms.get('current', 0),
                    'temperature': bms.get('mcu_ntc', 0)
                })
            
            # Update foot force
            if 'foot_force' in data:
                self.latest_data['foot_force'] = data['foot_force']
            
            # Update power voltage
            if 'power_v' in data:
                self.latest_data['battery']['voltage'] = data['power_v']
                
            # Trigger callbacks
            self._trigger_callbacks()
            
        except Exception as e:
            self.logger.error(f"Error handling low state data: {e}")
    
    def _handle_sport_mode_state(self, message):
        """Handle sport mode state data (position, velocity, mode)"""
        try:
            data = message['data']
            
            # Update position
            if 'position' in data and len(data['position']) >= 3:
                pos = data['position']
                self.latest_data['position'] = {
                    'x': pos[0], 'y': pos[1], 'z': pos[2]
                }
            
            # Update velocity
            if 'velocity' in data and len(data['velocity']) >= 3:
                vel = data['velocity']
                self.latest_data['velocity'] = {
                    'x': vel[0], 'y': vel[1], 'z': vel[2]
                }
            
            # Update mode and other sport mode data
            self.latest_data['mode'] = data.get('mode', 0)
            self.latest_data['body_height'] = data.get('body_height', 0)
            
            # Update gait information
            self.latest_data['gait_type'] = data.get('gait_type', 0)
            self.latest_data['foot_raise_height'] = data.get('foot_raise_height', 0)
            
            # Trigger callbacks
            self._trigger_callbacks()
            
        except Exception as e:
            self.logger.error(f"Error handling sport mode state data: {e}")
    
    def _handle_multiple_state(self, message):
        """Handle multiple state data (additional sensors)"""
        try:
            data = message['data']
            # Handle any additional state data here
            # This topic provides various robot states and can be extended
            
            self._trigger_callbacks()
            
        except Exception as e:
            self.logger.error(f"Error handling multiple state data: {e}")
    
    def _trigger_callbacks(self):
        """Trigger all registered data callbacks"""
        for callback in self.data_callbacks:
            try:
                callback(self.latest_data.copy())
            except Exception as e:
                self.logger.error(f"Error in data callback: {e}")
    
    def add_data_callback(self, callback: Callable):
        """Add a callback function for data updates"""
        self.data_callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable):
        """Remove a callback function"""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    async def send_sport_command(self, command: str, **kwargs):
        """Send sport mode command to robot"""
        if not self.connection:
            self.logger.error("Not connected to robot")
            return False
            
        try:
            # Map command name to command ID
            cmd_id = SPORT_CMD.get(command)
            if cmd_id is None:
                self.logger.error(f"Unknown sport command: {command}")
                return False
            
            # Prepare command message
            command_msg = {
                "api_id": cmd_id,
                **kwargs
            }
            
            # Send command via data channel
            self.connection.datachannel.pub_sub.publish(
                RTC_TOPIC['SPORT_MOD'], 
                command_msg
            )
            
            self.logger.info(f"Sent sport command: {command} (ID: {cmd_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending sport command {command}: {e}")
            return False
    
    async def move_robot(self, x: float, y: float, yaw: float):
        """Move robot with linear and angular velocities"""
        return await self.send_sport_command(
            'Move', 
            vx=x, 
            vy=y, 
            vyaw=yaw
        )
    
    async def stand_up(self):
        """Make robot stand up"""
        return await self.send_sport_command('StandUp')
    
    async def sit_down(self):
        """Make robot sit down"""
        return await self.send_sport_command('StandDown')
    
    async def stop_movement(self):
        """Stop robot movement"""
        return await self.send_sport_command('StopMove')
    
    def get_sensor_data(self) -> Dict[str, Any]:
        """Get latest sensor data"""
        return self.latest_data.copy()
    
    def is_connected(self) -> bool:
        """Check if connected to robot"""
        return self.latest_data.get('connected', False)
    
    async def disconnect(self):
        """Disconnect from robot"""
        try:
            if self.connection:
                # Clean up subscriptions
                if hasattr(self.connection, 'datachannel') and self.connection.datachannel:
                    # Unsubscribe from topics
                    topics = [
                        RTC_TOPIC['LOW_STATE'],
                        RTC_TOPIC['LF_SPORT_MOD_STATE'],
                        RTC_TOPIC['MULTIPLE_STATE']
                    ]
                    for topic in topics:
                        try:
                            self.connection.datachannel.pub_sub.unsubscribe(topic)
                        except:
                            pass
                
                # Close connection
                if hasattr(self.connection, 'disconnect'):
                    await self.connection.disconnect()
                elif hasattr(self.connection, 'close'):
                    await self.connection.close()
                
                self.connection = None
            
            self.latest_data['connected'] = False
            self.logger.info("Disconnected from Unitree robot")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
