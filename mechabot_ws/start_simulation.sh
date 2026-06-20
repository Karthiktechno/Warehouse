#!/bin/bash

# Source ROS 2 and workspace
source /opt/ros/humble/setup.bash
source install/setup.bash

# Check for a terminal emulator and launch teleop in it
if command -v gnome-terminal &> /dev/null; then
    echo "Starting teleop in a new gnome-terminal window..."
    gnome-terminal -- bash -c "source /opt/ros/humble/setup.bash && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel; exec bash"
elif command -v xterm &> /dev/null; then
    echo "Starting teleop in a new xterm window..."
    xterm -e "bash -c 'source /opt/ros/humble/setup.bash && ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel; exec bash'" &
else
    echo "No supported terminal emulator (gnome-terminal or xterm) found to launch teleop automatically."
    echo "Please open a new terminal manually for teleop."
fi

# Start the simulation and mapping in this terminal
echo "Starting Gazebo simulation and mapping..."
ros2 launch mechabot_bringup warehouse_mapping.launch.py
