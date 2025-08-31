"""
Main application entry point for Butler Connect - Unitree Go2 Integration
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from core.robot_manager import RobotManager
from web.api_server import APIServer
from utils.config_loader import ConfigLoader
from utils.logger import setup_logging


class ButlerConnectApp:
    """Main application class for Butler Connect"""
    
    def __init__(self):
        self.robot_manager = None
        self.api_server = None
        self.running = False
        
    async def initialize(self):
        """Initialize the application components"""
        try:
            # Load configuration
            config = ConfigLoader.load_all_configs()
            
            # Setup logging
            setup_logging(config.get('logging', {}))
            self.logger = logging.getLogger(__name__)
            
            self.logger.info("Initializing Butler Connect application...")
            
            # Initialize robot manager
            self.robot_manager = RobotManager(config)
            await self.robot_manager.initialize()
            
            # Initialize API server
            self.api_server = APIServer(self.robot_manager, config)
            
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize application: {e}")
            return False
    
    async def start(self):
        """Start the application"""
        if not await self.initialize():
            return False
            
        self.running = True
        self.logger.info("Starting Butler Connect application...")
        
        try:
            # Start robot connection
            await self.robot_manager.connect()
            
            # Start API server
            server_task = asyncio.create_task(self.api_server.start())
            
            # Start robot monitoring
            monitor_task = asyncio.create_task(self.robot_manager.start_monitoring())
            
            self.logger.info("Application started successfully")
            self.logger.info("Web interface available at http://localhost:8080")
            
            # Wait for shutdown signal
            await asyncio.gather(server_task, monitor_task)
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            return False
        
        return True
    
    async def shutdown(self):
        """Shutdown the application gracefully"""
        self.logger.info("Shutting down Butler Connect application...")
        self.running = False
        
        try:
            if self.robot_manager:
                await self.robot_manager.disconnect()
                
            if self.api_server:
                await self.api_server.stop()
                
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def signal_handler(signum, frame, app):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal. Gracefully shutting down...")
    asyncio.create_task(app.shutdown())


async def main():
    """Main application entry point"""
    app = ButlerConnectApp()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, app))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, app))
    
    try:
        success = await app.start()
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        await app.shutdown()
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await app.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run the application
    asyncio.run(main())
