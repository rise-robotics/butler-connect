#!/usr/bin/env python3

"""
Unitree WebRTC Discovery Script
Attempts to discover WebRTC signaling methods and ports
"""

import asyncio
import json
import socket
import struct
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from utils.logger import get_logger

logger = get_logger("webrtc_discovery")

class UnitreeWebRTCDiscovery:
    def __init__(self, robot_ip: str = "192.168.100.94"):
        self.robot_ip = robot_ip
        
    async def test_multicast_discovery(self):
        """Test WebRTC multicast responder"""
        logger.info("🔍 Testing WebRTC multicast discovery...")
        
        try:
            # Try to send multicast discovery packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Common WebRTC discovery patterns
            discovery_messages = [
                b"WEBRTC_DISCOVERY",
                b"UNITREE_WEBRTC_DISCOVER", 
                json.dumps({"type": "discover"}).encode(),
                json.dumps({"action": "discover", "protocol": "webrtc"}).encode()
            ]
            
            # Try different ports
            ports = [8080, 8081, 8765, 9000, 9001, 5000, 5001]
            
            for port in ports:
                for msg in discovery_messages:
                    try:
                        logger.info(f"📤 Sending discovery to {self.robot_ip}:{port}")
                        sock.sendto(msg, (self.robot_ip, port))
                        
                        # Try to receive response
                        data, addr = sock.recvfrom(1024)
                        logger.info(f"📥 Received response from {addr}: {data}")
                        return port, data
                        
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.debug(f"Error on port {port}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Multicast discovery failed: {e}")
            
        return None, None
    
    async def test_http_signaling(self):
        """Test HTTP-based WebRTC signaling"""
        logger.info("🌐 Testing HTTP WebRTC signaling...")
        
        import aiohttp
        
        # Common WebRTC HTTP endpoints
        endpoints = [
            "/webrtc/offer",
            "/api/webrtc/offer", 
            "/signaling/offer",
            "/rtc/offer",
            "/webrtc",
            "/api/webrtc"
        ]
        
        ports = [8080, 8081, 8000, 8001, 9000, 9001]
        
        for port in ports:
            for endpoint in endpoints:
                url = f"http://{self.robot_ip}:{port}{endpoint}"
                
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                        # Try GET first
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                content = await resp.text()
                                logger.info(f"✅ HTTP endpoint found: {url}")
                                logger.info(f"📄 Response: {content[:200]}...")
                                return url, content
                                
                except Exception as e:
                    logger.debug(f"HTTP test failed for {url}: {e}")
                    continue
                    
        return None, None
    
    async def test_websocket_signaling(self):
        """Test WebSocket-based WebRTC signaling"""
        logger.info("🔌 Testing WebSocket WebRTC signaling...")
        
        import websockets
        
        # Common WebSocket endpoints
        ws_endpoints = [
            "/webrtc",
            "/ws/webrtc",
            "/signaling", 
            "/ws/signaling",
            "/rtc",
            "/ws"
        ]
        
        ports = [8080, 8081, 8765, 9000, 9001]
        
        for port in ports:
            for endpoint in ws_endpoints:
                ws_url = f"ws://{self.robot_ip}:{port}{endpoint}"
                
                try:
                    logger.info(f"🔌 Trying WebSocket: {ws_url}")
                    async with websockets.connect(ws_url, timeout=3) as websocket:
                        # Try to send a WebRTC offer request
                        offer_request = {
                            "type": "offer_request",
                            "sdp_type": "offer"
                        }
                        
                        await websocket.send(json.dumps(offer_request))
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        
                        logger.info(f"✅ WebSocket connection successful: {ws_url}")
                        logger.info(f"📥 Response: {response}")
                        return ws_url, response
                        
                except Exception as e:
                    logger.debug(f"WebSocket test failed for {ws_url}: {e}")
                    continue
                    
        return None, None
    
    async def scan_open_ports(self):
        """Scan for open ports on robot"""
        logger.info("🔍 Scanning for open ports...")
        
        open_ports = []
        # Test common WebRTC/media ports
        test_ports = range(8000, 8100)
        
        for port in test_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            
            try:
                result = sock.connect_ex((self.robot_ip, port))
                if result == 0:
                    open_ports.append(port)
                    logger.info(f"✅ Port {port} is open")
            except:
                pass
            finally:
                sock.close()
                
        return open_ports

async def main():
    logger.info("🤖 Unitree WebRTC Discovery Starting...")
    logger.info("=" * 50)
    
    discovery = UnitreeWebRTCDiscovery("192.168.100.94")
    
    # Test different discovery methods
    results = {}
    
    # 1. Port scanning
    logger.info("\n📡 Step 1: Port Scanning")
    open_ports = await discovery.scan_open_ports()
    results['open_ports'] = open_ports
    
    # 2. Multicast discovery
    logger.info("\n📡 Step 2: Multicast Discovery")
    mc_port, mc_data = await discovery.test_multicast_discovery()
    results['multicast'] = {'port': mc_port, 'data': mc_data}
    
    # 3. HTTP signaling test
    logger.info("\n📡 Step 3: HTTP Signaling Test")  
    http_url, http_data = await discovery.test_http_signaling()
    results['http'] = {'url': http_url, 'data': http_data}
    
    # 4. WebSocket signaling test
    logger.info("\n📡 Step 4: WebSocket Signaling Test")
    ws_url, ws_data = await discovery.test_websocket_signaling()
    results['websocket'] = {'url': ws_url, 'data': ws_data}
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Discovery Results Summary:")
    logger.info(f"🔌 Open Ports: {open_ports}")
    
    if mc_port:
        logger.info(f"📡 Multicast: Port {mc_port} responded")
    if http_url:
        logger.info(f"🌐 HTTP: {http_url} responded")  
    if ws_url:
        logger.info(f"🔌 WebSocket: {ws_url} responded")
        
    if not any([mc_port, http_url, ws_url]):
        logger.warning("⚠️  No WebRTC signaling methods discovered")
        logger.info("💡 The robot's WebRTC services may use custom protocols")
        logger.info("💡 Check Unitree documentation for WebRTC API details")
    
    return results

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Discovery cancelled by user")
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()
