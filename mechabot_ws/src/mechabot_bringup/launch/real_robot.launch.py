import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    serial_port = LaunchConfiguration("serial_port") #Port for RPLidar

    serial_port_arg = DeclareLaunchArgument(
        "serial_port",
        default_value="/dev/ttyUSB0", 
        description="Serial port for RPLIDAR"
    )

    laser_driver = Node(
        package="rplidar_ros",
        executable="rplidar_node",
        name="rplidar_node",
        parameters=[{
            "channel_type": "serial",
            "serial_port": serial_port,
            "serial_baudrate": 115200,
            "frame_id": "lidar_link",
            "inverted": False,
            "angle_compensate": True,
            "scan_mode": "Sensitivity", #Standard, #Express, #Stability
            "range_min": 0.05
        }],
        output="screen"
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(
                get_package_share_directory("mechabot_localization"),
                "rviz",
                "global_localization.rviz"
            )
        ],
        output="screen",
        parameters=[{"use_sim_time": False}]
    )

    return LaunchDescription([
        serial_port_arg,
        laser_driver,
        rviz,
    ])