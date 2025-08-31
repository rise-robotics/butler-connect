#!/usr/bin/env python3
"""
Butler Connect - Quick Start Script
Installs dependencies and starts the application
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def main():
    """Main setup and start function"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                    🤖 Butler Connect                      ║
    ║               Unitree Go2 Robot Controller                ║
    ║                                                          ║
    ║                    Quick Start Setup                     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"📁 Working directory: {project_dir}")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("\n❌ Failed to install dependencies")
        print("💡 Try running: pip install --upgrade pip")
        print("💡 Or create a virtual environment first")
        return
    
    # Create log directory
    log_dir = project_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    print(f"📂 Created log directory: {log_dir}")
    
    # Check configuration files
    config_dir = project_dir / "config"
    required_configs = ["robot_config.yaml", "control_config.yaml", "safety_config.yaml"]
    
    print(f"\n🔍 Checking configuration files...")
    for config_file in required_configs:
        config_path = config_dir / config_file
        if config_path.exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ Missing: {config_file}")
    
    print(f"\n🚀 Starting Butler Connect...")
    print(f"📱 Web interface will be available at: http://localhost:8000")
    print(f"📖 API documentation at: http://localhost:8000/docs")
    print(f"\n⚠️  SAFETY REMINDER:")
    print(f"   - Always keep the emergency stop button ready")
    print(f"   - Ensure the robot has enough space to move")
    print(f"   - Check battery level before operation")
    print(f"\n🛑 Press Ctrl+C to stop the application")
    print(f"{'='*60}")
    
    # Start the application
    try:
        subprocess.run([sys.executable, "src/main.py"], check=True)
    except KeyboardInterrupt:
        print(f"\n\n🛑 Shutting down Butler Connect...")
        print(f"✅ Thank you for using Butler Connect!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Check that all dependencies are installed")
        print(f"   2. Verify configuration files are present")
        print(f"   3. Ensure robot is connected to network")

if __name__ == "__main__":
    main()
