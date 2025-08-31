"""
Motion Controller - High-level motion control for Unitree Go2
"""

import asyncio
import logging
import math
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from core.robot_manager import RobotManager, MotionCommand, RobotMode
from utils.logger import get_logger


class GaitType(Enum):
    """Available gait types"""
    WALK = "walk"
    TROT = "trot"
    RUN = "run"
    BOUND = "bound"


@dataclass
class TrajectoryPoint:
    """Single point in a trajectory"""
    x: float
    y: float
    z: float
    yaw: float
    timestamp: float


@dataclass
class MotionProfile:
    """Motion profile for smooth movement"""
    max_velocity: float = 1.0
    max_acceleration: float = 1.0
    max_angular_velocity: float = 1.0
    max_angular_acceleration: float = 1.0


class MotionController:
    """High-level motion controller for the robot"""
    
    def __init__(self, robot_manager: RobotManager, config: Dict[str, Any]):
        self.robot_manager = robot_manager
        self.config = config.get('control', {})
        self.logger = get_logger(__name__)
        
        # Motion parameters
        self.motion_config = self.config.get('motion', {})
        self.max_linear_vel = self.motion_config.get('max_linear_velocity', 1.5)
        self.max_angular_vel = self.motion_config.get('max_angular_velocity', 2.0)
        
        # Current motion state
        self.current_trajectory: list[TrajectoryPoint] = []
        self.trajectory_index = 0
        self.is_executing_trajectory = False
        
        # Motion profile
        self.motion_profile = MotionProfile(
            max_velocity=self.max_linear_vel,
            max_acceleration=self.motion_config.get('max_acceleration', 2.0),
            max_angular_velocity=self.max_angular_vel,
            max_angular_acceleration=2.0
        )
        
        # Control loop task
        self.control_task: Optional[asyncio.Task] = None
        self.running = False
        
        self.logger.info("Motion Controller initialized")
    
    async def start(self):
        """Start the motion controller"""
        if self.running:
            return
        
        self.running = True
        self.control_task = asyncio.create_task(self._control_loop())
        self.logger.info("Motion Controller started")
    
    async def stop(self):
        """Stop the motion controller"""
        self.running = False
        
        if self.control_task:
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        
        # Send stop command
        await self.stop_motion()
        self.logger.info("Motion Controller stopped")
    
    async def move_velocity(self, linear_x: float, linear_y: float, angular_z: float, 
                           gait: GaitType = GaitType.TROT, step_height: float = 0.1) -> bool:
        """Move robot with specified velocities"""
        try:
            # Clamp velocities to safe limits
            linear_x = max(-self.max_linear_vel, min(self.max_linear_vel, linear_x))
            linear_y = max(-self.max_linear_vel, min(self.max_linear_vel, linear_y))
            angular_z = max(-self.max_angular_vel, min(self.max_angular_vel, angular_z))
            
            # Create motion command
            command = MotionCommand(
                linear_x=linear_x,
                linear_y=linear_y,
                angular_z=angular_z,
                step_height=step_height,
                gait_type=gait.value
            )
            
            # Send command
            success = await self.robot_manager.send_motion_command(command)
            
            if success:
                self.logger.debug(f"Velocity command sent: x={linear_x:.2f}, y={linear_y:.2f}, z={angular_z:.2f}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send velocity command: {e}")
            return False
    
    async def move_to_position(self, target_x: float, target_y: float, target_yaw: float = 0.0,
                              max_speed: float = 0.5) -> bool:
        """Move robot to a specific position"""
        try:
            current_state = self.robot_manager.robot_state
            current_x, current_y, current_z = current_state.position
            current_roll, current_pitch, current_yaw = current_state.orientation
            
            # Calculate trajectory
            trajectory = self._plan_trajectory(
                (current_x, current_y, current_yaw),
                (target_x, target_y, target_yaw),
                max_speed
            )
            
            # Execute trajectory
            return await self.execute_trajectory(trajectory)
            
        except Exception as e:
            self.logger.error(f"Failed to move to position: {e}")
            return False
    
    async def execute_trajectory(self, trajectory: list[TrajectoryPoint]) -> bool:
        """Execute a planned trajectory"""
        try:
            if self.is_executing_trajectory:
                self.logger.warning("Already executing trajectory, stopping current one")
                await self.stop_trajectory()
            
            self.current_trajectory = trajectory
            self.trajectory_index = 0
            self.is_executing_trajectory = True
            
            self.logger.info(f"Starting trajectory execution with {len(trajectory)} points")
            
            # Trajectory will be executed by the control loop
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute trajectory: {e}")
            return False
    
    async def stop_trajectory(self):
        """Stop current trajectory execution"""
        self.is_executing_trajectory = False
        self.current_trajectory.clear()
        self.trajectory_index = 0
        await self.stop_motion()
        self.logger.info("Trajectory execution stopped")
    
    async def stop_motion(self):
        """Stop all robot motion"""
        stop_command = MotionCommand()  # All zeros
        await self.robot_manager.send_motion_command(stop_command)
    
    async def change_gait(self, gait: GaitType) -> bool:
        """Change robot gait"""
        try:
            # Get current motion state and update gait
            current_state = self.robot_manager.robot_state
            
            command = MotionCommand(
                linear_x=0.0,  # Maintain current velocity or stop
                linear_y=0.0,
                angular_z=0.0,
                gait_type=gait.value
            )
            
            success = await self.robot_manager.send_motion_command(command)
            
            if success:
                self.logger.info(f"Gait changed to: {gait.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to change gait: {e}")
            return False
    
    async def set_step_height(self, height: float) -> bool:
        """Set step height for walking"""
        try:
            # Clamp step height to reasonable limits
            height = max(0.05, min(0.2, height))
            
            command = MotionCommand(
                linear_x=0.0,
                linear_y=0.0,
                angular_z=0.0,
                step_height=height
            )
            
            success = await self.robot_manager.send_motion_command(command)
            
            if success:
                self.logger.info(f"Step height set to: {height:.3f}m")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set step height: {e}")
            return False
    
    def _plan_trajectory(self, start: Tuple[float, float, float], 
                        end: Tuple[float, float, float], max_speed: float) -> list[TrajectoryPoint]:
        """Plan a smooth trajectory between two points"""
        start_x, start_y, start_yaw = start
        end_x, end_y, end_yaw = end
        
        # Calculate distance and time
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        angular_distance = abs(end_yaw - start_yaw)
        
        # Estimate travel time
        linear_time = distance / max_speed
        angular_time = angular_distance / (self.max_angular_vel * 0.5)  # Conservative
        total_time = max(linear_time, angular_time, 1.0)  # Minimum 1 second
        
        # Generate trajectory points
        trajectory = []
        num_points = max(10, int(total_time * 10))  # 10 points per second
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # Smooth interpolation using cubic easing
            smooth_t = self._smooth_step(t)
            
            x = start_x + (end_x - start_x) * smooth_t
            y = start_y + (end_y - start_y) * smooth_t
            yaw = start_yaw + (end_yaw - start_yaw) * smooth_t
            
            timestamp = t * total_time
            
            trajectory.append(TrajectoryPoint(x, y, 0.0, yaw, timestamp))
        
        return trajectory
    
    def _smooth_step(self, t: float) -> float:
        """Smooth step function for trajectory interpolation"""
        # Smoothstep function: 3t² - 2t³
        return t * t * (3.0 - 2.0 * t)
    
    async def _control_loop(self):
        """Main control loop for trajectory execution"""
        control_rate = 20.0  # 20 Hz control rate
        dt = 1.0 / control_rate
        
        while self.running:
            try:
                if self.is_executing_trajectory and self.current_trajectory:
                    await self._execute_trajectory_step()
                
                await asyncio.sleep(dt)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Control loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_trajectory_step(self):
        """Execute one step of the current trajectory"""
        if not self.current_trajectory or self.trajectory_index >= len(self.current_trajectory):
            self.is_executing_trajectory = False
            await self.stop_motion()
            self.logger.info("Trajectory execution completed")
            return
        
        current_point = self.current_trajectory[self.trajectory_index]
        next_index = self.trajectory_index + 1
        
        if next_index < len(self.current_trajectory):
            next_point = self.current_trajectory[next_index]
            
            # Calculate velocity commands
            dt = next_point.timestamp - current_point.timestamp
            if dt > 0:
                linear_x = (next_point.x - current_point.x) / dt
                linear_y = (next_point.y - current_point.y) / dt
                angular_z = (next_point.yaw - current_point.yaw) / dt
                
                # Send velocity command
                await self.move_velocity(linear_x, linear_y, angular_z)
        
        self.trajectory_index += 1
