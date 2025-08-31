#!/usr/bin/env python3
"""
LocalSTA Setup Verification Script for Butler Connect
Verifies network connectivity and WebRTC setup for LocalSTA mode
"""

import socket
import subprocess
import sys
from pathlib import Path
import yaml
import asyncio

def load_config():
    """Load robot configuration"""
    config_path = Path("config/robot_config.yaml")
    if not config_path.exists():
        print("❌ Config file not found at config/robot_config.yaml")
        return None
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def check_network_connectivity(ip_address):
    """Check if robot IP is reachable"""
    print(f"🔍 Checking connectivity to robot at {ip_address}...")
    
    # Ping test
    try:
        result = subprocess.run(['ping', '-c', '3', ip_address], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ping successful to {ip_address}")
            return True
        else:
            print(f"❌ Ping failed to {ip_address}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Ping timeout to {ip_address}")
        return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False

def check_port_connectivity(ip_address, ports):
    """Check if specific ports are reachable"""
    results = {}
    
    for port_name, port_num in ports.items():
        print(f"🔍 Checking port {port_num} ({port_name}) on {ip_address}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip_address, port_num))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port_num} ({port_name}) is open")
                results[port_name] = True
            else:
                print(f"❌ Port {port_num} ({port_name}) is closed or filtered")
                results[port_name] = False
                
        except Exception as e:
            print(f"❌ Error checking port {port_num}: {e}")
            results[port_name] = False
    
    return results

def get_local_ip():
    """Get local machine IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine"

def check_webrtc_requirements():
    """Check if WebRTC requirements are met"""
    print("🔍 Checking WebRTC requirements...")
    
    try:
        import go2_webrtc_driver
        print("✅ go2_webrtc_driver is installed")
        
        from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
        print("✅ WebRTC driver classes imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ WebRTC driver not installed: {e}")
        print("💡 Install with: pip install go2-webrtc-driver")
        return False

def main():
    print("🤖 Butler Connect LocalSTA Setup Verification")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    if not config:
        return False
    
    robot_ip = config.get('robot', {}).get('ip_address', '192.168.100.94')
    protocol = config.get('communication', {}).get('protocol', 'udp')
    
    print(f"📋 Configuration Summary:")
    print(f"   Robot IP: {robot_ip}")
    print(f"   Protocol: {protocol}")
    print(f"   Local IP: {get_local_ip()}")
    print()
    
    # Check WebRTC requirements
    if not check_webrtc_requirements():
        print("\n❌ WebRTC requirements not met")
        return False
    
    print()
    
    # Check network connectivity
    if not check_network_connectivity(robot_ip):
        print("\n❌ Cannot reach robot. Check:")
        print("   1. Robot is powered on")
        print("   2. Robot is connected to your local network (WiFi)")
        print("   3. IP address in config is correct")
        print("   4. Both devices are on same network")
        return False
    
    print()
    
    # Check relevant ports
    ports_to_check = {
        'WebRTC Signaling': 8080,
        'High-level UDP': config.get('robot', {}).get('udp_port', 8082),
        'Low-level UDP': config.get('robot', {}).get('low_level_port', 8007)
    }
    
    port_results = check_port_connectivity(robot_ip, ports_to_check)
    
    print()
    
    # Summary
    all_good = all(port_results.values())
    
    if all_good:
        print("🎉 All checks passed! Your LocalSTA setup looks good.")
        print("\n🚀 To start Butler Connect:")
        print("   python quick_start.py")
        print(f"\n🌐 Access web interface at:")
        print(f"   http://{get_local_ip()}:8090")
        print(f"   http://localhost:8090")
        
    else:
        print("⚠️  Some issues found:")
        for port_name, status in port_results.items():
            if not status:
                print(f"   - {port_name} port connectivity issue")
        
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure robot is in LocalSTA mode (connected to WiFi)")
        print("   2. Check robot IP address with 'ifconfig' on robot")
        print("   3. Verify both devices are on same network")
        print("   4. Try connecting to robot's web interface directly")
        print(f"      http://{robot_ip}:8080")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)