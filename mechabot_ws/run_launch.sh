#!/bin/bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch mechabot_bringup warehouse_mapping.launch.py > /tmp/launch.log 2>&1 &
PID=$!
sleep 15
kill -INT $PID
