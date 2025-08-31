#!/usr/bin/env bash
set -eo pipefail

# Usage: start-ros2-wsl.sh <ros_distro> <project_path>
ROS_DISTRO_NAME="${1:-jazzy}"
PROJECT_PATH="${2:-$PWD}"

echo "[Butler][WSL] Using ROS distro: ${ROS_DISTRO_NAME} | Domain: ${ROS_DOMAIN_ID:-unset}"

# Source ROS 2 environment
if [ -f "/opt/ros/${ROS_DISTRO_NAME}/setup.bash" ]; then
  # Temporarily disable nounset because ROS setup uses unbound variables
  set +u
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO_NAME}/setup.bash"
  set -u
else
  echo "[Butler][WSL] ERROR: /opt/ros/${ROS_DISTRO_NAME}/setup.bash not found" >&2
  exit 1
fi

cd "${PROJECT_PATH}"

# Default PORT if not provided
if [ -z "${PORT:-}" ]; then
  export PORT=8090
fi

# Ensure python3-venv is available
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "[Butler][WSL] Installing python3-venv..."
  sudo apt-get update -y
  sudo apt-get install -y python3-venv
fi

# Create venv with system site packages (to see rclpy)
if [ ! -d .venv ]; then
  python3 -m venv --system-site-packages .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

# If rclpy isn't visible, recreate venv with system packages
if ! python3 -c 'import rclpy' >/dev/null 2>&1; then
  deactivate || true
  rm -rf .venv
  python3 -m venv --system-site-packages .venv
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

# Bootstrap pip toolchain (keep setuptools <80 to avoid colcon breakage)
python3 -m pip install --upgrade pip "setuptools<80" wheel

# Handle NumPy for Python 3.12 to avoid building incompatible pins
PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "${PYVER}" = "3.12" ]; then
  python3 -m pip install numpy==1.26.4
fi

# Install requirements, filtering out pinned numpy to avoid downgrades
grep -v '^numpy==' requirements.txt > /tmp/req-no-numpy.txt || cp requirements.txt /tmp/req-no-numpy.txt
python3 -m pip install -r /tmp/req-no-numpy.txt

export PYTHONUNBUFFERED=1
echo "[Butler][WSL] Starting app..."
exec python3 src/main.py
