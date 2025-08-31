#!/usr/bin/env bash
set -euo pipefail

# Install ROS 2 on Ubuntu (WSL). Supports jammy->humble, noble->jazzy.

if ! command -v lsb_release >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y lsb-release
fi

CODENAME=$(lsb_release -cs)
ARCH=$(dpkg --print-architecture)

case "$CODENAME" in
  jammy) DISTRO=humble ;;
  noble) DISTRO=jazzy ;;
  focal) DISTRO=foxy ;; # legacy
  *) echo "Unsupported Ubuntu codename: $CODENAME" >&2; exit 1 ;;
 esac

echo "[install_ros2_wsl] Ubuntu=$CODENAME arch=$ARCH -> ROS 2 distro=$DISTRO"

sudo apt update
sudo apt install -y curl gnupg2 software-properties-common

# Add ROS 2 apt repository
sudo mkdir -p /usr/share/keyrings
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo tee /usr/share/keyrings/ros-archive-keyring.gpg >/dev/null

echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu ${CODENAME} main" | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null

sudo apt update

# Core packages (headless)
sudo apt install -y \
  ros-${DISTRO}-ros-base \
  ros-${DISTRO}-geometry-msgs \
  ros-${DISTRO}-sensor-msgs \
  ros-${DISTRO}-nav-msgs \
  ros-${DISTRO}-std-msgs \
  ros-${DISTRO}-std-srvs \
  python3-argcomplete

# Optional dev tools (safe)
sudo apt install -y python3-colcon-common-extensions || true

# Convenience: auto-source in bash shell
if ! grep -q "/opt/ros/${DISTRO}/setup.bash" "$HOME/.bashrc" 2>/dev/null; then
  echo "source /opt/ros/${DISTRO}/setup.bash" >> "$HOME/.bashrc"
fi

echo "[install_ros2_wsl] ROS 2 ${DISTRO} installation complete."
