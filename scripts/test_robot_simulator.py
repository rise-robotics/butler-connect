#!/usr/bin/env python3
"""
Test ROS2 publisher to simulate real Unitree Go2 sensor data
This demonstrates how real robot data would flow into Butler Connect
"""
import rclpy
from rclpy.node import Node
import time
import random
import math

from sensor_msgs.msg import BatteryState, Temperature
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Quaternion, Twist, Vector3


class UnitreeSimulatorNode(Node):
    def __init__(self):
        super().__init__('unitree_simulator')
        
        # Publishers
        self.battery_pub = self.create_publisher(BatteryState, '/battery_state', 10)
        self.temp_pub = self.create_publisher(Temperature, '/temperature', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        
        # Timer for publishing sensor data
        self.timer = self.create_timer(0.1, self.publish_sensor_data)  # 10 Hz
        
        # Simulation state
        self.start_time = time.time()
        self.battery_level = 85.0  # Start at 85%
        self.position_x = 0.0
        self.position_y = 0.0
        self.yaw = 0.0
        
        self.get_logger().info('🤖 Unitree Go2 Simulator Node Started')
        self.get_logger().info('📡 Publishing real-like sensor data to:')
        self.get_logger().info('   - /battery_state (BatteryState)')
        self.get_logger().info('   - /temperature (Temperature)')
        self.get_logger().info('   - /odom (Odometry)')

    def publish_sensor_data(self):
        current_time = self.get_clock().now()
        elapsed = time.time() - self.start_time
        
        # Publish battery data (realistic Unitree Go2 values)
        battery_msg = BatteryState()
        battery_msg.header.stamp = current_time.to_msg()
        battery_msg.header.frame_id = "base_link"
        
        # Simulate battery drain over time
        self.battery_level = max(15.0, 85.0 - (elapsed / 3600.0) * 10.0)  # 10% per hour
        battery_msg.percentage = self.battery_level / 100.0
        battery_msg.voltage = 25.2 * (self.battery_level / 100.0)  # 6S LiPo nominal
        battery_msg.current = random.uniform(2.0, 8.0)  # 2-8A consumption
        battery_msg.charge = float('nan')  # Not measured
        battery_msg.capacity = 15.0  # Ah (approximate Go2 capacity)
        battery_msg.design_capacity = 15.0
        battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        battery_msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LIPO
        
        self.battery_pub.publish(battery_msg)
        
        # Publish temperature data (internal temperature)
        temp_msg = Temperature()
        temp_msg.header.stamp = current_time.to_msg()
        temp_msg.header.frame_id = "base_link"
        # Realistic robot internal temperature with some variation
        base_temp = 45.0 + 10.0 * math.sin(elapsed * 0.01)  # Slow variation
        temp_msg.temperature = base_temp + random.uniform(-2.0, 2.0)
        temp_msg.variance = 1.0
        
        self.temp_pub.publish(temp_msg)
        
        # Publish odometry data (position and orientation)
        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_link"
        
        # Simulate robot walking in a small circle
        self.yaw += 0.005  # Slow rotation
        radius = 2.0
        self.position_x = radius * math.cos(self.yaw)
        self.position_y = radius * math.sin(self.yaw)
        
        # Position
        odom_msg.pose.pose.position.x = self.position_x
        odom_msg.pose.pose.position.y = self.position_y
        odom_msg.pose.pose.position.z = 0.35  # Robot height
        
        # Orientation (quaternion from yaw)
        odom_msg.pose.pose.orientation.x = 0.0
        odom_msg.pose.pose.orientation.y = 0.0
        odom_msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        odom_msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        
        # Velocities (simple differential)
        odom_msg.twist.twist.linear.x = 0.01  # 1 cm/s forward
        odom_msg.twist.twist.angular.z = 0.005  # Rotation speed
        
        self.odom_pub.publish(odom_msg)


def main(args=None):
    rclpy.init(args=args)
    node = UnitreeSimulatorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Shutting down Unitree simulator')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
