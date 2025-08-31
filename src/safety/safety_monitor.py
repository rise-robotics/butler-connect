"""
Safety Monitor - Safety systems and monitoring for robot operation
"""

import asyncio
import logging
import time
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.robot_manager import RobotManager, RobotState
from src.utils.logger import get_logger


class SafetyLevel(Enum):
    """Safety alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SafetyAction(Enum):
    """Safety response actions"""
    MONITOR = "monitor"
    SLOW_DOWN = "slow_down"
    STOP = "stop"
    EMERGENCY_STOP = "emergency_stop"
    SHUTDOWN = "shutdown"


@dataclass
class SafetyAlert:
    """Safety alert information"""
    id: str
    level: SafetyLevel
    message: str
    action: SafetyAction
    timestamp: float
    resolved: bool = False


@dataclass
class SafetyBoundary:
    """Safety boundary definition"""
    name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    warning_threshold: float = 0.1  # Percentage before limit
    critical_threshold: float = 0.05  # Percentage before limit


class SafetyMonitor:
    """Safety monitoring and emergency response system"""
    
    def __init__(self, robot_manager: RobotManager, config: Dict[str, Any]):
        self.robot_manager = robot_manager
        self.config = config.get('safety', {})
        self.logger = get_logger(__name__)
        
        # Safety configuration
        self.boundaries_config = self.config.get('boundaries', {})
        self.emergency_config = self.config.get('emergency_stop', {})
        self.health_config = self.config.get('health_monitoring', {})
        
        # Safety state
        self.active_alerts: Dict[str, SafetyAlert] = {}
        self.safety_enabled = True
        self.emergency_stop_active = False
        
        # Monitoring parameters
        self.check_interval = self.health_config.get('check_interval', 1.0)
        
        # Safety boundaries
        self.boundaries = self._setup_boundaries()
        
        # Callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Monitoring task
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Performance tracking
        self.last_check_time = 0.0
        self.check_count = 0
        
        self.logger.info("Safety Monitor initialized")
    
    async def start(self):
        """Start safety monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        # Register with robot manager
        self.robot_manager.register_state_callback(self._on_robot_state_update)
        
        self.logger.info("Safety monitoring started")
    
    async def stop(self):
        """Stop safety monitoring"""
        self.running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Safety monitoring stopped")
    
    async def emergency_stop(self, reason: str = "Manual emergency stop"):
        """Trigger emergency stop"""
        if self.emergency_stop_active:
            return
        
        self.emergency_stop_active = True
        
        # Create emergency alert
        alert = SafetyAlert(
            id="emergency_stop",
            level=SafetyLevel.EMERGENCY,
            message=reason,
            action=SafetyAction.EMERGENCY_STOP,
            timestamp=time.time()
        )
        
        self.active_alerts["emergency_stop"] = alert
        
        # Stop robot
        await self.robot_manager.emergency_stop_robot()
        
        # Notify callbacks
        await self._notify_alert_callbacks(alert)
        
        self.logger.critical(f"EMERGENCY STOP: {reason}")
    
    async def reset_emergency_stop(self):
        """Reset emergency stop state"""
        if not self.emergency_stop_active:
            return
        
        self.emergency_stop_active = False
        
        # Resolve emergency alert
        if "emergency_stop" in self.active_alerts:
            self.active_alerts["emergency_stop"].resolved = True
        
        self.logger.warning("Emergency stop reset")
    
    def enable_safety_monitoring(self):
        """Enable safety monitoring"""
        self.safety_enabled = True
        self.logger.info("Safety monitoring enabled")
    
    def disable_safety_monitoring(self):
        """Disable safety monitoring (USE WITH CAUTION)"""
        self.safety_enabled = False
        self.logger.warning("Safety monitoring DISABLED - USE WITH EXTREME CAUTION")
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for safety alerts"""
        self.alert_callbacks.append(callback)
    
    def get_active_alerts(self) -> List[SafetyAlert]:
        """Get list of active safety alerts"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get comprehensive safety status"""
        active_alerts = self.get_active_alerts()
        
        return {
            "safety_enabled": self.safety_enabled,
            "emergency_stop_active": self.emergency_stop_active,
            "active_alerts_count": len(active_alerts),
            "highest_alert_level": self._get_highest_alert_level(),
            "last_check_time": self.last_check_time,
            "total_checks": self.check_count,
            "boundaries": {name: self._check_boundary_status(boundary) 
                          for name, boundary in self.boundaries.items()}
        }
    
    async def _monitoring_loop(self):
        """Main safety monitoring loop"""
        while self.running:
            try:
                if self.safety_enabled:
                    await self._perform_safety_checks()
                
                self.last_check_time = time.time()
                self.check_count += 1
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Safety monitoring error: {e}")
                await asyncio.sleep(1.0)
    
    async def _perform_safety_checks(self):
        """Perform all safety checks"""
        robot_state = self.robot_manager.robot_state
        
        # Check connection
        await self._check_connection(robot_state)
        
        # Check battery level
        await self._check_battery(robot_state)
        
        # Check temperature
        await self._check_temperature(robot_state)
        
        # Check orientation limits
        await self._check_orientation(robot_state)
        
        # Check joint limits (if available)
        await self._check_joint_limits(robot_state)
        
        # Check communication timeout
        await self._check_communication_timeout(robot_state)
    
    async def _check_connection(self, state: RobotState):
        """Check robot connection status"""
        if not state.is_connected:
            alert = SafetyAlert(
                id="connection_lost",
                level=SafetyLevel.CRITICAL,
                message="Robot connection lost",
                action=SafetyAction.STOP,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
    
    async def _check_battery(self, state: RobotState):
        """Check battery level"""
        battery_level = state.battery_level
        
        critical_level = self.health_config.get('alert_thresholds', {}).get('battery_critical', 10)
        warning_level = critical_level * 2  # Warning at 20% if critical at 10%
        
        if battery_level <= critical_level:
            alert = SafetyAlert(
                id="battery_critical",
                level=SafetyLevel.CRITICAL,
                message=f"Critical battery level: {battery_level:.1f}%",
                action=SafetyAction.EMERGENCY_STOP,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
        elif battery_level <= warning_level:
            alert = SafetyAlert(
                id="battery_low",
                level=SafetyLevel.WARNING,
                message=f"Low battery level: {battery_level:.1f}%",
                action=SafetyAction.MONITOR,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
    
    async def _check_temperature(self, state: RobotState):
        """Check operating temperature"""
        temperature = state.temperature
        
        warning_temp = self.health_config.get('alert_thresholds', {}).get('temperature_warning', 55)
        critical_temp = self.boundaries_config.get('max_temperature', 65)
        
        if temperature >= critical_temp:
            alert = SafetyAlert(
                id="temperature_critical",
                level=SafetyLevel.CRITICAL,
                message=f"Critical temperature: {temperature:.1f}°C",
                action=SafetyAction.EMERGENCY_STOP,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
        elif temperature >= warning_temp:
            alert = SafetyAlert(
                id="temperature_high",
                level=SafetyLevel.WARNING,
                message=f"High temperature: {temperature:.1f}°C",
                action=SafetyAction.SLOW_DOWN,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
    
    async def _check_orientation(self, state: RobotState):
        """Check robot orientation limits"""
        roll, pitch, yaw = state.orientation
        
        max_roll = self.boundaries_config.get('max_roll', 0.5)
        max_pitch = self.boundaries_config.get('max_pitch', 0.5)
        
        if abs(roll) > max_roll:
            alert = SafetyAlert(
                id="roll_limit",
                level=SafetyLevel.CRITICAL,
                message=f"Roll angle exceeded: {roll:.3f} rad",
                action=SafetyAction.EMERGENCY_STOP,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
        
        if abs(pitch) > max_pitch:
            alert = SafetyAlert(
                id="pitch_limit",
                level=SafetyLevel.CRITICAL,
                message=f"Pitch angle exceeded: {pitch:.3f} rad",
                action=SafetyAction.EMERGENCY_STOP,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
    
    async def _check_joint_limits(self, state: RobotState):
        """Check joint position limits"""
        # This would check actual joint positions against limits
        # Implementation depends on available joint data
        pass
    
    async def _check_communication_timeout(self, state: RobotState):
        """Check for communication timeout"""
        current_time = time.time()
        time_since_update = current_time - state.last_update
        
        timeout_threshold = 5.0  # 5 seconds
        
        if time_since_update > timeout_threshold:
            alert = SafetyAlert(
                id="communication_timeout",
                level=SafetyLevel.CRITICAL,
                message=f"Communication timeout: {time_since_update:.1f}s",
                action=SafetyAction.STOP,
                timestamp=time.time()
            )
            await self._handle_alert(alert)
    
    async def _handle_alert(self, alert: SafetyAlert):
        """Handle a safety alert"""
        # Store or update alert
        self.active_alerts[alert.id] = alert
        
        # Execute safety action
        await self._execute_safety_action(alert)
        
        # Notify callbacks
        await self._notify_alert_callbacks(alert)
        
        # Log alert
        log_method = {
            SafetyLevel.INFO: self.logger.info,
            SafetyLevel.WARNING: self.logger.warning,
            SafetyLevel.CRITICAL: self.logger.error,
            SafetyLevel.EMERGENCY: self.logger.critical
        }.get(alert.level, self.logger.info)
        
        log_method(f"SAFETY ALERT [{alert.level.value.upper()}]: {alert.message}")
    
    async def _execute_safety_action(self, alert: SafetyAlert):
        """Execute the appropriate safety action"""
        if alert.action == SafetyAction.EMERGENCY_STOP:
            await self.emergency_stop(alert.message)
        elif alert.action == SafetyAction.STOP:
            # Send stop command but don't trigger full emergency stop
            from src.core.robot_manager import MotionCommand
            stop_command = MotionCommand()
            await self.robot_manager.send_motion_command(stop_command)
        elif alert.action == SafetyAction.SLOW_DOWN:
            # Could implement speed reduction here
            pass
        # MONITOR action requires no immediate response
    
    async def _notify_alert_callbacks(self, alert: SafetyAlert):
        """Notify all registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    async def _on_robot_state_update(self, state: RobotState):
        """Handle robot state updates for real-time safety monitoring"""
        # This allows for immediate safety responses
        # without waiting for the monitoring loop
        pass
    
    def _setup_boundaries(self) -> Dict[str, SafetyBoundary]:
        """Setup safety boundaries from configuration"""
        boundaries = {}
        
        # Battery boundary
        min_battery = self.boundaries_config.get('min_battery_level', 20)
        boundaries['battery'] = SafetyBoundary(
            name='battery_level',
            min_value=min_battery,
            warning_threshold=0.2,  # 20% before limit
            critical_threshold=0.1   # 10% before limit
        )
        
        # Temperature boundary
        max_temp = self.boundaries_config.get('max_temperature', 65)
        boundaries['temperature'] = SafetyBoundary(
            name='temperature',
            max_value=max_temp,
            warning_threshold=0.15,  # 15% before limit
            critical_threshold=0.05   # 5% before limit
        )
        
        # Orientation boundaries
        max_roll = self.boundaries_config.get('max_roll', 0.5)
        max_pitch = self.boundaries_config.get('max_pitch', 0.5)
        
        boundaries['roll'] = SafetyBoundary(
            name='roll_angle',
            min_value=-max_roll,
            max_value=max_roll,
            warning_threshold=0.2,
            critical_threshold=0.1
        )
        
        boundaries['pitch'] = SafetyBoundary(
            name='pitch_angle',
            min_value=-max_pitch,
            max_value=max_pitch,
            warning_threshold=0.2,
            critical_threshold=0.1
        )
        
        return boundaries
    
    def _check_boundary_status(self, boundary: SafetyBoundary) -> Dict[str, Any]:
        """Check the status of a safety boundary"""
        # This would return the current status relative to the boundary
        return {
            "name": boundary.name,
            "status": "ok",  # Could be "ok", "warning", "critical"
            "current_value": None,
            "limit": boundary.max_value or boundary.min_value
        }
    
    def _get_highest_alert_level(self) -> str:
        """Get the highest active alert level"""
        active_alerts = self.get_active_alerts()
        
        if not active_alerts:
            return "none"
        
        levels = [alert.level for alert in active_alerts]
        
        if SafetyLevel.EMERGENCY in levels:
            return "emergency"
        elif SafetyLevel.CRITICAL in levels:
            return "critical"
        elif SafetyLevel.WARNING in levels:
            return "warning"
        else:
            return "info"
