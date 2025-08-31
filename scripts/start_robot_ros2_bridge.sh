#!/bin/bash
# Script to start Unitree Go2 ROS2 bridge on the robot
# Run this script ON the robot (via SSH)

echo "🤖 Starting Unitree Go2 ROS2 Bridge..."

# Source ROS2 environment (adjust path as needed for your robot's ROS2 installation)
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
elif [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
elif [ -f "/opt/ros/foxy/setup.bash" ]; then
    source /opt/ros/foxy/setup.bash
else
    echo "❌ ROS2 not found. Please install ROS2 on the robot first."
    exit 1
fi

# Set ROS domain ID (match your Butler Connect configuration)
export ROS_DOMAIN_ID=0

# Unitree Go2 ROS2 bridge (adjust command based on your robot's setup)
# This might be different depending on your Unitree SDK version
echo "🚀 Starting ROS2 bridge for sensor data..."

# Option 1: If you have unitree_ros2 package installed
ros2 run unitree_go2_bridge sensor_bridge &

# Option 2: If you have custom bridge
# ./unitree_ros2_bridge &

# Option 3: Start individual topic publishers (example)
# ros2 run unitree_sensors battery_publisher &
# ros2 run unitree_sensors temperature_publisher &
# ros2 run unitree_sensors odometry_publisher &

echo "✅ ROS2 bridge started! Check with: ros2 topic list"
echo "📡 Your Butler Connect should now receive real sensor data"

wait
