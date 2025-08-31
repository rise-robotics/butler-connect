"""
API Server for Butler Connect - Web interface and REST API
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
import uvicorn

from core.robot_manager import RobotManager, MotionCommand, RobotState
from utils.logger import get_logger


class APIServer:
    """API Server for robot control and monitoring"""
    
    def __init__(self, robot_manager: RobotManager, config: Dict[str, Any]):
        self.robot_manager = robot_manager
        self.config = config
        self.logger = get_logger(__name__)
        
        # FastAPI app
        self.app = FastAPI(
            title="Butler Connect API",
            description="API for Unitree Go2 Robot Control",
            version="1.0.0"
        )
        
        # Setup routes
        self._setup_routes()

        # WebSocket connections
        self.websocket_connections: list[WebSocket] = []

        # Server configuration (configurable)
        server_cfg = (self.config or {}).get("server", {})
        # Allow env override for PORT commonly used in PaaS
        import os
        self.host = server_cfg.get("host", "localhost")
        self.port = int(os.environ.get("PORT", server_cfg.get("port", 8080)))

        # Register robot callbacks
        self.robot_manager.register_state_callback(self._on_robot_state_update)
        self.robot_manager.register_error_callback(self._on_robot_error)
        
        self.logger.info("API Server initialized")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Static files and templates
        static_path = Path("src/web/static")
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        template_path = Path("src/web/templates")
        if template_path.exists():
            self.templates = Jinja2Templates(directory=str(template_path))
        
        # Root route
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            if hasattr(self, 'templates'):
                return self.templates.TemplateResponse(
                    "index.html",
                    {"request": request, "protocol": self.robot_manager.protocol}
                )
            return HTMLResponse("<h1>Butler Connect - Unitree Go2 Interface</h1><p>Web interface not available</p>")
        
        # Robot status endpoints
        @self.app.get("/api/robot/status")
        async def get_robot_status():
            """Get current robot status"""
            return {
                "connected": self.robot_manager.is_connected,
                "state": {
                    "mode": self.robot_manager.robot_state.mode.name,
                    "battery_level": self.robot_manager.robot_state.battery_level,
                    "temperature": self.robot_manager.robot_state.temperature,
                    "position": self.robot_manager.robot_state.position,
                    "orientation": self.robot_manager.robot_state.orientation,
                    "last_update": self.robot_manager.robot_state.last_update
                }
            }
        
        @self.app.post("/api/robot/connect")
        async def connect_robot(background_tasks: BackgroundTasks):
            """Connect to robot"""
            if self.robot_manager.is_connected:
                return {"status": "already_connected"}
            
            background_tasks.add_task(self.robot_manager.connect)
            return {"status": "connecting"}
        
        @self.app.post("/api/robot/disconnect")
        async def disconnect_robot(background_tasks: BackgroundTasks):
            """Disconnect from robot"""
            if not self.robot_manager.is_connected:
                return {"status": "not_connected"}
            
            background_tasks.add_task(self.robot_manager.disconnect)
            return {"status": "disconnecting"}
        
        # Motion control endpoints
        @self.app.post("/api/robot/move")
        async def move_robot(command: Dict[str, float]):
            """Send movement command to robot"""
            try:
                if not self.robot_manager.is_connected:
                    raise HTTPException(status_code=400, detail="Robot not connected")
                
                motion_cmd = MotionCommand(
                    linear_x=command.get('linear_x', 0.0),
                    linear_y=command.get('linear_y', 0.0),
                    angular_z=command.get('angular_z', 0.0),
                    step_height=command.get('step_height', 0.1),
                    gait_type=str(command.get('gait_type', 'trot'))
                )
                
                success = await self.robot_manager.send_motion_command(motion_cmd)
                
                if success:
                    return {"status": "command_sent"}
                else:
                    raise HTTPException(status_code=400, detail="Failed to send command")
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/robot/stop")
        async def stop_robot():
            """Stop robot movement"""
            try:
                stop_command = MotionCommand()  # All zeros = stop
                success = await self.robot_manager.send_motion_command(stop_command)
                
                if success:
                    return {"status": "stopped"}
                else:
                    raise HTTPException(status_code=400, detail="Failed to stop robot")
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/robot/emergency_stop")
        async def emergency_stop():
            """Emergency stop robot"""
            try:
                await self.robot_manager.emergency_stop_robot()
                return {"status": "emergency_stop_activated"}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/robot/stand")
        async def stand_up():
            """Make robot stand up"""
            try:
                success = await self.robot_manager.stand_up()
                if success:
                    return {"status": "standing_up", "message": "Robot is standing up"}
                else:
                    raise HTTPException(status_code=400, detail="Failed to make robot stand up")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/robot/sit")
        async def sit_down():
            """Make robot sit down"""
            try:
                success = await self.robot_manager.sit_down()
                if success:
                    return {"status": "sitting_down", "message": "Robot is sitting down"}
                else:
                    raise HTTPException(status_code=400, detail="Failed to make robot sit down")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
                    
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
        
        # Health check endpoint
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "robot_connected": self.robot_manager.is_connected,
                "timestamp": self.robot_manager.robot_state.last_update,
                "protocol": self.robot_manager.protocol
            }

        # Protocol endpoint for UI verification
        @self.app.get("/api/protocol")
        async def get_protocol():
            return {"protocol": self.robot_manager.protocol}
    
    async def start(self):
        """Start the API server"""
        try:
            self.logger.info(f"Starting API server on {self.host}:{self.port}")
            
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            raise
    
    async def stop(self):
        """Stop the API server"""
        try:
            self.logger.info("Stopping API server...")
            
            # Close WebSocket connections
            for websocket in self.websocket_connections[:]:
                await websocket.close()
                
            self.websocket_connections.clear()
            
            self.logger.info("API server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping API server: {e}")
    
    async def _on_robot_state_update(self, state: RobotState):
        """Handle robot state updates"""
        try:
            # Broadcast state to WebSocket clients
            state_data = {
                "type": "state_update",
                "data": {
                    "mode": state.mode.name,
                    "battery_level": state.battery_level,
                    "temperature": state.temperature,
                    "position": state.position,
                    "orientation": state.orientation,
                    "is_connected": state.is_connected,
                    "last_update": state.last_update
                }
            }
            
            # Send to all connected WebSocket clients
            disconnected_clients = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_json(state_data)
                except Exception:
                    disconnected_clients.append(websocket)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                if client in self.websocket_connections:
                    self.websocket_connections.remove(client)
                    
        except Exception as e:
            self.logger.error(f"Error broadcasting state update: {e}")
    
    async def _on_robot_error(self, error_type: str, message: str):
        """Handle robot errors"""
        try:
            error_data = {
                "type": "error",
                "error_type": error_type,
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Broadcast error to WebSocket clients
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_json(error_data)
                except Exception:
                    pass  # Ignore disconnected clients
                    
        except Exception as e:
            self.logger.error(f"Error broadcasting error: {e}")
