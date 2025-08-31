#!/usr/bin/env python3

"""
WebRTC Connection Test for Butler Connect
Tests WebRTC connectivity and data flow without full application
"""

import asyncio
import sys
import os
import signal
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.webrtc_client import WebRTCClient
from utils.config_loader import ConfigLoader
from utils.logger import get_logger

# Setup logging
logger = get_logger("webrtc_test")

class WebRTCTester:
    def __init__(self):
        self.client = None
        self.running = False
        self.received_data = {
            'battery': None,
            'odometry': None, 
            'temperature': None
        }
    
    async def on_battery_data(self, data):
        """Handle battery data callback"""
        self.received_data['battery'] = data
        logger.info(f"📱 Battery: {data.get('percentage', 'N/A')}%, Voltage: {data.get('voltage', 'N/A')}V")
    
    async def on_odometry_data(self, data):
        """Handle odometry data callback"""
        self.received_data['odometry'] = data
        pos = data.get('position', {})
        logger.info(f"📍 Position: x={pos.get('x', 0):.2f}, y={pos.get('y', 0):.2f}, z={pos.get('z', 0):.2f}")
    
    async def on_temperature_data(self, data):
        """Handle temperature data callback"""
        self.received_data['temperature'] = data
        logger.info(f"🌡️  Temperature: {data.get('temperature', 'N/A')}°C")
    
    async def test_connection(self, robot_ip: str, signaling_port: int = 8765):
        """Test WebRTC connection to robot"""
        logger.info("🚀 Starting WebRTC connection test...")
        
        try:
            # Create WebRTC client
            config = {
                'webrtc': {
                    'robot_ip': robot_ip,
                    'signaling_port': signaling_port,
                    'video_enabled': False,  # Disable video for testing
                    'data_channel_enabled': True
                }
            }
            self.client = WebRTCClient(config)
            
            # Set up callbacks
            self.client.set_battery_callback(self.on_battery_data)
            self.client.set_odometry_callback(self.on_odometry_data)
            self.client.set_temperature_callback(self.on_temperature_data)
            
            # Connect
            logger.info(f"🔌 Connecting to robot at {robot_ip}:{signaling_port}...")
            await self.client.connect()
            
            logger.info("✅ WebRTC connection established!")
            self.running = True
            
            # Send test command
            logger.info("📤 Sending test movement command...")
            await self.client.send_command({
                'type': 'velocity',
                'linear': {'x': 0.1, 'y': 0, 'z': 0},
                'angular': {'x': 0, 'y': 0, 'z': 0.1}
            })
            
            # Wait for data
            logger.info("⏳ Waiting for sensor data... (Press Ctrl+C to stop)")
            start_time = asyncio.get_event_loop().time()
            
            while self.running:
                await asyncio.sleep(1)
                
                # Check if we've received any data
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time
                
                if elapsed > 10:  # After 10 seconds
                    data_received = any(self.received_data.values())
                    if data_received:
                        logger.info("✅ Successfully received sensor data!")
                        break
                    else:
                        logger.warning("⚠️  No sensor data received after 10 seconds")
                        break
        
        except KeyboardInterrupt:
            logger.info("⏹️  Test interrupted by user")
        except Exception as e:
            logger.error(f"❌ WebRTC test failed: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            logger.info("🧹 Cleaning up WebRTC connection...")
            # WebRTC client doesn't have disconnect method yet, just close connection
            if hasattr(self.client, 'pc') and self.client.pc:
                await self.client.pc.close()
        self.running = False

async def main():
    """Main test function"""
    print("🧪 Butler Connect WebRTC Test")
    print("=" * 40)
    
    # Load configuration
    try:
        config_path = Path(__file__).parent.parent / 'config' / 'robot_config.yaml'
        config = ConfigLoader.load_config(str(config_path))
        
        robot_config = config.get('robot', {})
        robot_ip = robot_config.get('ip_address', '192.168.100.94')
        webrtc_config = config.get('communication', {}).get('webrtc', {})
        signaling_port = webrtc_config.get('signaling_port', 8080)
        
        logger.info(f"📋 Loaded config - Robot: {robot_ip}, Port: {signaling_port}")
        
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        robot_ip = '192.168.100.94'
        signaling_port = 8765
        logger.info(f"📋 Using defaults - Robot: {robot_ip}, Port: {signaling_port}")
    
    # Run test
    tester = WebRTCTester()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("🛑 Received interrupt signal")
        tester.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await tester.test_connection(robot_ip, signaling_port)
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    for data_type, data in tester.received_data.items():
        status = "✅ Received" if data else "❌ Not received"
        print(f"  {data_type.capitalize()}: {status}")
    
    print("\n💡 Next Steps:")
    if any(tester.received_data.values()):
        print("  - WebRTC is working! You can now use it in Butler Connect")
        print("  - Run: ./scripts/switch_protocol.sh webrtc --restart")
    else:
        print("  - Check robot WebRTC server is running")
        print("  - Verify network connectivity to robot")
        print("  - Check signaling port configuration")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)
