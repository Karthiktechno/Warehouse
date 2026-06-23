#!/bin/bash

echo "Sourcing ROS 2 workspace..."
source /opt/ros/humble/setup.bash
source install/setup.bash

echo "Starting Gazebo and Mapping in the background..."
ros2 launch mechabot_bringup warehouse_mapping.launch.py > /tmp/launch.log 2>&1 &
LAUNCH_PID=$!

echo "Waiting 15 seconds for simulation to initialize..."
sleep 15

# Determine screen resolution for ffmpeg
RES=$(xdpyinfo 2>/dev/null | awk '/dimensions:/ {print $2}')
if [ -z "$RES" ]; then
    RES="1920x1080"
fi
DISPLAY_VAR=${DISPLAY:-:0.0}

echo "Starting screen recording (using ffmpeg) on display $DISPLAY_VAR with resolution $RES..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg -y -video_size $RES -framerate 25 -f x11grab -i $DISPLAY_VAR -c:v libx264 -preset ultrafast mapping_video.mp4 > /tmp/ffmpeg.log 2>&1 &
    FFMPEG_PID=$!
else
    echo "ffmpeg not found. Skipping video recording."
fi

echo "Starting autonomous teleop for 45 seconds..."
python3 auto_teleop.py &
TELEOP_PID=$!

sleep 45

echo "Stopping teleop..."
kill -INT $TELEOP_PID || true

echo "Saving the map to 'warehouse_map'..."
ros2 run nav2_map_server map_saver_cli -f warehouse_map

if [ -n "$FFMPEG_PID" ]; then
    echo "Stopping video recording. Video will be saved as mapping_video.mp4."
    kill -INT $FFMPEG_PID || true
    sleep 2
fi

echo "Shutting down the simulation..."
kill -INT $LAUNCH_PID || true
sleep 3
pkill -f gzserver || true
pkill -f gzclient || true
pkill -f rviz2 || true

echo "Mapping process complete! Your map is saved as 'warehouse_map.yaml' and video as 'mapping_video.mp4'."
