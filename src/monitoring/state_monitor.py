"""
State Monitor - Real-time monitoring and logging of robot state
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import deque

from core.robot_manager import RobotManager, RobotState
from utils.logger import get_logger


@dataclass
class StateSnapshot:
    """Snapshot of robot state at a point in time"""
    timestamp: float
    mode: str
    battery_level: float
    temperature: float
    position: tuple
    orientation: tuple
    velocity: tuple
    joint_positions: list
    is_connected: bool


class StateMonitor:
    """Monitor and log robot state information"""
    
    def __init__(self, robot_manager: RobotManager, config: Dict[str, Any]):
        self.robot_manager = robot_manager
        self.config = config
        self.logger = get_logger(__name__)
        
        # Monitoring configuration
        self.monitoring_config = config.get('monitoring', {})
        self.update_rate = self.monitoring_config.get('update_rate', 10.0)  # Hz
        self.history_size = self.monitoring_config.get('history_size', 1000)
        
        # State history
        self.state_history: deque[StateSnapshot] = deque(maxlen=self.history_size)
        
        # Statistics
        self.stats = {
            'total_updates': 0,
            'average_update_rate': 0.0,
            'last_update_time': 0.0,
            'connection_uptime': 0.0,
            'connection_start_time': 0.0
        }
        
        # Data logging
        self.logging_enabled = self.monitoring_config.get('enable_logging', True)
        self.log_file_path = self.monitoring_config.get('log_file', 'logs/state_log.json')
        self.log_interval = self.monitoring_config.get('log_interval', 60.0)  # seconds
        
        # Tasks
        self.monitor_task: Optional[asyncio.Task] = None
        self.logging_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Performance tracking
        self.update_times: deque[float] = deque(maxlen=100)
        
        self.logger.info("State Monitor initialized")
    
    async def start(self):
        """Start state monitoring"""
        if self.running:
            return
        
        self.running = True
        
        # Register with robot manager
        self.robot_manager.register_state_callback(self._on_state_update)
        
        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        # Start logging task if enabled
        if self.logging_enabled:
            self.logging_task = asyncio.create_task(self._logging_loop())
        
        self.stats['connection_start_time'] = time.time()
        
        self.logger.info("State monitoring started")
    
    async def stop(self):
        """Stop state monitoring"""
        self.running = False
        
        # Cancel tasks
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.logging_task:
            self.logging_task.cancel()
            try:
                await self.logging_task
            except asyncio.CancelledError:
                pass
        
        # Save final state log
        if self.logging_enabled:
            await self._save_state_log()
        
        self.logger.info("State monitoring stopped")
    
    def get_current_state(self) -> Optional[StateSnapshot]:
        """Get the most recent state snapshot"""
        return self.state_history[-1] if self.state_history else None
    
    def get_state_history(self, duration_seconds: Optional[float] = None) -> List[StateSnapshot]:
        """Get state history for a specified duration"""
        if not duration_seconds:
            return list(self.state_history)
        
        current_time = time.time()
        cutoff_time = current_time - duration_seconds
        
        return [snapshot for snapshot in self.state_history 
                if snapshot.timestamp >= cutoff_time]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        current_time = time.time()
        
        # Calculate connection uptime
        if self.robot_manager.is_connected and self.stats['connection_start_time'] > 0:
            self.stats['connection_uptime'] = current_time - self.stats['connection_start_time']
        
        # Calculate average update rate
        if len(self.update_times) > 1:
            time_span = self.update_times[-1] - self.update_times[0]
            if time_span > 0:
                self.stats['average_update_rate'] = (len(self.update_times) - 1) / time_span
        
        return {
            **self.stats,
            'history_size': len(self.state_history),
            'max_history_size': self.history_size,
            'current_time': current_time
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        current_state = self.get_current_state()
        
        # Calculate data rates
        recent_history = self.get_state_history(60.0)  # Last minute
        data_points = len(recent_history)
        
        # Battery trend
        battery_trend = self._calculate_battery_trend(recent_history)
        
        # Temperature trend
        temperature_trend = self._calculate_temperature_trend(recent_history)
        
        return {
            'data_points_last_minute': data_points,
            'current_battery': current_state.battery_level if current_state else 0,
            'battery_trend': battery_trend,
            'current_temperature': current_state.temperature if current_state else 0,
            'temperature_trend': temperature_trend,
            'connection_status': self.robot_manager.is_connected,
            'last_update_age': time.time() - self.stats['last_update_time'] if self.stats['last_update_time'] > 0 else 0
        }
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        update_interval = 1.0 / self.update_rate
        
        while self.running:
            try:
                # Update statistics
                current_time = time.time()
                self.stats['last_update_time'] = current_time
                self.stats['total_updates'] += 1
                
                await asyncio.sleep(update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _logging_loop(self):
        """Periodic state logging loop"""
        while self.running:
            try:
                await self._save_state_log()
                await asyncio.sleep(self.log_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Logging loop error: {e}")
                await asyncio.sleep(self.log_interval)
    
    async def _on_state_update(self, state: RobotState):
        """Handle robot state updates"""
        try:
            # Create state snapshot
            snapshot = StateSnapshot(
                timestamp=time.time(),
                mode=state.mode.name,
                battery_level=state.battery_level,
                temperature=state.temperature,
                position=state.position,
                orientation=state.orientation,
                velocity=state.velocity,
                joint_positions=state.joint_positions.copy() if state.joint_positions else [],
                is_connected=state.is_connected
            )
            
            # Add to history
            self.state_history.append(snapshot)
            
            # Track update timing
            self.update_times.append(snapshot.timestamp)
            
            # Log significant state changes
            self._log_state_changes(snapshot)
            
        except Exception as e:
            self.logger.error(f"Error processing state update: {e}")
    
    def _log_state_changes(self, current: StateSnapshot):
        """Log significant state changes"""
        if len(self.state_history) < 2:
            return
        
        previous = self.state_history[-2]
        
        # Log mode changes
        if current.mode != previous.mode:
            self.logger.info(f"Robot mode changed: {previous.mode} -> {current.mode}")
        
        # Log connection changes
        if current.is_connected != previous.is_connected:
            status = "connected" if current.is_connected else "disconnected"
            self.logger.info(f"Robot {status}")
        
        # Log significant battery changes
        battery_change = abs(current.battery_level - previous.battery_level)
        if battery_change > 5.0:  # 5% change
            self.logger.info(f"Battery level: {current.battery_level:.1f}%")
        
        # Log significant temperature changes
        temp_change = abs(current.temperature - previous.temperature)
        if temp_change > 5.0:  # 5°C change
            self.logger.info(f"Temperature: {current.temperature:.1f}°C")
    
    async def _save_state_log(self):
        """Save state history to log file"""
        try:
            if not self.state_history:
                return
            
            # Ensure log directory exists
            log_path = Path(self.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare log data
            log_data = {
                'timestamp': time.time(),
                'statistics': self.get_statistics(),
                'recent_states': [asdict(snapshot) for snapshot in 
                                list(self.state_history)[-100:]]  # Last 100 states
            }
            
            # Write to file
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.debug(f"State log saved to {log_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save state log: {e}")
    
    def _calculate_battery_trend(self, history: List[StateSnapshot]) -> str:
        """Calculate battery level trend"""
        if len(history) < 2:
            return "stable"
        
        # Compare first and last values
        start_battery = history[0].battery_level
        end_battery = history[-1].battery_level
        
        difference = end_battery - start_battery
        
        if difference < -1.0:  # Dropping by more than 1%
            return "decreasing"
        elif difference > 1.0:  # Increasing by more than 1%
            return "increasing"
        else:
            return "stable"
    
    def _calculate_temperature_trend(self, history: List[StateSnapshot]) -> str:
        """Calculate temperature trend"""
        if len(history) < 2:
            return "stable"
        
        # Compare first and last values
        start_temp = history[0].temperature
        end_temp = history[-1].temperature
        
        difference = end_temp - start_temp
        
        if difference < -2.0:  # Dropping by more than 2°C
            return "decreasing"
        elif difference > 2.0:  # Increasing by more than 2°C
            return "increasing"
        else:
            return "stable"
    
    def export_state_history(self, file_path: str, format: str = "json") -> bool:
        """Export state history to file"""
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                data = {
                    'export_timestamp': time.time(),
                    'statistics': self.get_statistics(),
                    'state_history': [asdict(snapshot) for snapshot in self.state_history]
                }
                
                with open(export_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            elif format.lower() == "csv":
                import csv
                
                with open(export_path, 'w', newline='') as f:
                    if self.state_history:
                        fieldnames = asdict(self.state_history[0]).keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for snapshot in self.state_history:
                            writer.writerow(asdict(snapshot))
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"State history exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export state history: {e}")
            return False
