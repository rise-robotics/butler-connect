"""
ROS 2 client for Unitree Go2 using rclpy.

This module provides a thin wrapper around rclpy to:
- Publish geometry_msgs/Twist to a configurable cmd_vel topic
- Optionally call std_srvs/Trigger services for stand/sit if available
- Subscribe to common status topics (battery, temperature, imu/odometry if present)

It runs the ROS 2 executor in a background thread and maintains a small
shared state snapshot readable by the app.

Note: rclpy and ROS 2 message packages must be available in the environment.
We import them lazily and degrade gracefully if not found.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
import importlib
from typing import Any, Dict, Optional

from utils.logger import get_logger


@dataclass
class ROS2ClientState:
    battery_percentage: Optional[float] = None
    temperature_c: Optional[float] = None
    position_xyz: Optional[tuple[float, float, float]] = None
    orientation_rpy: Optional[tuple[float, float, float]] = None
    last_update_ts: float = 0.0


class ROS2Client:
    """Encapsulates rclpy node, pubs/subs, and a spin thread."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        self._rclpy = None
        self._node = None
        self._executor = None
        self._spin_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Shared state with lightweight lock
        self.state = ROS2ClientState()
        self._lock = threading.Lock()

        # Handles
        self._pub_cmd_vel = None
        self._svc_stand = None
        self._svc_sit = None

        # Configurable topic/service names
        comm_cfg = self.config.get("communication", {})
        ros2_cfg = comm_cfg.get("ros2", {})
        ns = ros2_cfg.get("namespace", "")

        def ns_join(name: str) -> str:
            if not ns:
                return name
            if name.startswith("/"):
                name = name[1:]
            return f"/{ns}/{name}".replace("//", "/")

        self.topic_cmd_vel = ns_join(ros2_cfg.get("cmd_vel_topic", "cmd_vel"))
        self.topic_battery = ns_join(ros2_cfg.get("battery_topic", "battery_state"))
        self.topic_temperature = ns_join(ros2_cfg.get("temperature_topic", "temperature"))
        self.topic_odom = ns_join(ros2_cfg.get("odom_topic", "odom"))
        self.service_stand = ns_join(ros2_cfg.get("stand_service", "stand_up"))
        self.service_sit = ns_join(ros2_cfg.get("sit_service", "sit_down"))

    # ----- Lifecycle -----
    def initialize(self) -> bool:
        """Import rclpy and set up the node, publishers, subscribers, services."""
        try:
            try:
                rclpy = importlib.import_module('rclpy')
                rclpy_node_mod = importlib.import_module('rclpy.node')  # noqa: F401
                rclpy_exec_mod = importlib.import_module('rclpy.executors')
                geom_msgs_mod = importlib.import_module('geometry_msgs.msg')
                sensor_msgs_mod = importlib.import_module('sensor_msgs.msg')
            except Exception as e:
                self.logger.error(
                    f"ROS 2 (rclpy) not available: {e}. Ensure ROS 2 is installed and sourced.")
                return False

            # Extract classes
            MultiThreadedExecutor = getattr(rclpy_exec_mod, 'MultiThreadedExecutor')
            Twist = getattr(geom_msgs_mod, 'Twist')
            BatteryState = getattr(sensor_msgs_mod, 'BatteryState')

            self._rclpy = rclpy
            self._rclpy.init(args=None)

            # Create node
            self._node = self._rclpy.create_node("butler_connect_go2")

            # Publishers
            self._pub_cmd_vel = self._node.create_publisher(Twist, self.topic_cmd_vel, 10)

            # Subscribers (optional; will simply be quiet if no publishers present)
            self._node.create_subscription(BatteryState, self.topic_battery, self._on_battery, 10)

            # Try to subscribe to temperature if message type exists
            try:
                Temperature = getattr(sensor_msgs_mod, 'Temperature')
                self._node.create_subscription(Temperature, self.topic_temperature, self._on_temperature, 10)
            except Exception:
                # Sensor message may not exist or topic not provided
                pass

            # Try to subscribe to odom for position/orientation
            try:
                nav_msgs_mod = importlib.import_module('nav_msgs.msg')
                Odometry = getattr(nav_msgs_mod, 'Odometry')
                self._node.create_subscription(Odometry, self.topic_odom, self._on_odom, 10)
            except Exception:
                pass

            # Service clients (optional)
            try:
                std_srvs_mod = importlib.import_module('std_srvs.srv')
                Trigger = getattr(std_srvs_mod, 'Trigger')
                self._svc_stand = self._node.create_client(Trigger, self.service_stand)
                self._svc_sit = self._node.create_client(Trigger, self.service_sit)
            except Exception:
                self._svc_stand = None
                self._svc_sit = None

            # Start executor thread
            self._executor = MultiThreadedExecutor()
            self._executor.add_node(self._node)
            self._spin_thread = threading.Thread(target=self._spin_loop, name="ros2-spin", daemon=True)
            self._spin_thread.start()

            self.logger.info(
                f"ROS 2 initialized. cmd_vel: {self.topic_cmd_vel}, battery: {self.topic_battery}, odom: {self.topic_odom}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ROS 2 client: {e}")
            self.shutdown()
            return False

    def shutdown(self):
        try:
            self._stop_event.set()
            if self._executor is not None:
                # remove node first
                try:
                    if self._node:
                        self._executor.remove_node(self._node)
                except Exception:
                    pass
            if self._spin_thread and self._spin_thread.is_alive():
                self._spin_thread.join(timeout=2.0)
            if self._node is not None:
                try:
                    self._node.destroy_node()
                except Exception:
                    pass
            if self._rclpy is not None:
                try:
                    self._rclpy.shutdown()
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Error shutting down ROS 2 client: {e}")

    # ----- Spin thread -----
    def _spin_loop(self):
        try:
            while not self._stop_event.is_set():
                # Non-blocking spin some time slice
                if self._executor:
                    self._executor.spin_once(timeout_sec=0.1)
        except Exception as e:
            self.logger.error(f"ROS 2 spin loop error: {e}")

    # ----- Publishers -----
    def publish_twist(self, linear_x: float, linear_y: float, angular_z: float):
        try:
            geom_msgs_mod = importlib.import_module('geometry_msgs.msg')
            Twist = getattr(geom_msgs_mod, 'Twist')
            msg = Twist()  # type: ignore[call-arg]
            msg.linear.x = float(linear_x)
            msg.linear.y = float(linear_y)
            msg.linear.z = 0.0
            msg.angular.x = 0.0
            msg.angular.y = 0.0
            msg.angular.z = float(angular_z)
            if self._pub_cmd_vel:
                self._pub_cmd_vel.publish(msg)
        except Exception as e:
            self.logger.error(f"Failed to publish Twist: {e}")

    # ----- Services -----
    def call_stand(self, timeout_sec: float = 2.0) -> bool:
        if not self._svc_stand:
            self.logger.warning("Stand service client not available")
            return False
        try:
            # Ensure module is present (mostly for environments without ROS 2)
            importlib.import_module('std_srvs.srv')
            if not self._svc_stand.wait_for_service(timeout_sec=timeout_sec):
                self.logger.warning("Stand service not available")
                return False
            req = type(self._svc_stand.srv_type.Request)()  # type: ignore[attr-defined]
            future = self._svc_stand.call_async(req)
            start = time.time()
            while time.time() - start < timeout_sec:
                if future.done():
                    result = future.result()
                    return bool(getattr(result, "success", False))
                time.sleep(0.05)
            self.logger.warning("Stand service call timed out")
            return False
        except Exception as e:
            self.logger.error(f"Stand service call failed: {e}")
            return False

    def call_sit(self, timeout_sec: float = 2.0) -> bool:
        if not self._svc_sit:
            self.logger.warning("Sit service client not available")
            return False
        try:
            importlib.import_module('std_srvs.srv')
            if not self._svc_sit.wait_for_service(timeout_sec=timeout_sec):
                self.logger.warning("Sit service not available")
                return False
            req = type(self._svc_sit.srv_type.Request)()  # type: ignore[attr-defined]
            future = self._svc_sit.call_async(req)
            start = time.time()
            while time.time() - start < timeout_sec:
                if future.done():
                    result = future.result()
                    return bool(getattr(result, "success", False))
                time.sleep(0.05)
            self.logger.warning("Sit service call timed out")
            return False
        except Exception as e:
            self.logger.error(f"Sit service call failed: {e}")
            return False

    # ----- Subscribers -----
    def _on_battery(self, msg):
        try:
            with self._lock:
                # BatteryState.percentage: 0.0..1.0
                perc = float(getattr(msg, "percentage", 0.0))
                self.state.battery_percentage = max(0.0, min(100.0, perc * 100.0))
                self.state.last_update_ts = time.time()
        except Exception:
            pass

    def _on_temperature(self, msg):
        try:
            # sensor_msgs/Temperature has .temperature in Celsius
            temp_c = float(getattr(msg, "temperature", 0.0))
            with self._lock:
                self.state.temperature_c = temp_c
                self.state.last_update_ts = time.time()
        except Exception:
            pass

    def _on_odom(self, msg):
        try:
            # nav_msgs/Odometry: pose.pose.position and orientation (quat)
            pos = msg.pose.pose.position
            ox, oy, oz, ow = (
                msg.pose.pose.orientation.x,
                msg.pose.pose.orientation.y,
                msg.pose.pose.orientation.z,
                msg.pose.pose.orientation.w,
            )

            # Convert quaternion to roll/pitch/yaw
            import math

            sinr_cosp = 2 * (ow * ox + oy * oz)
            cosr_cosp = 1 - 2 * (ox * ox + oy * oy)
            roll = math.atan2(sinr_cosp, cosr_cosp)

            sinp = 2 * (ow * oy - oz * ox)
            if abs(sinp) >= 1:
                pitch = math.copysign(math.pi / 2, sinp)
            else:
                pitch = math.asin(sinp)

            siny_cosp = 2 * (ow * oz + ox * oy)
            cosy_cosp = 1 - 2 * (oy * oy + oz * oz)
            yaw = math.atan2(siny_cosp, cosy_cosp)

            with self._lock:
                self.state.position_xyz = (float(pos.x), float(pos.y), float(pos.z))
                self.state.orientation_rpy = (roll, pitch, yaw)
                self.state.last_update_ts = time.time()
        except Exception:
            pass
