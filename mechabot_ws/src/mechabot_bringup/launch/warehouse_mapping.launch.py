import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

# Path to SLAM configuration
slam_rviz_config_path = os.path.join(
    get_package_share_directory('mechabot_mapping'),
    'rviz',
    'slam.rviz'
)

def generate_launch_description():

    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mechabot_description"),
            "launch",
            "gazebo.launch.py"
        ),
        launch_arguments={
            "world_name": "small_warehouse"
        }.items()
    )

    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mechabot_controller"),
            "launch",
            "controller.launch.py"
        ),
    )
    
    twist_mux = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("twist_mux"),
            "launch",
            "twist_mux_launch.py"
        ),
        launch_arguments={
            "cmd_vel_out": "wheel_controller/cmd_vel_unstamped",
            "config_locks": os.path.join(get_package_share_directory("mechabot_controller"), "config", "twist_mux_locks.yaml"),
            "config_topics": os.path.join(get_package_share_directory("mechabot_controller"), "config", "twist_mux_topics.yaml"),
            "config_joy": os.path.join(get_package_share_directory("mechabot_controller"), "config", "twist_mux_joy.yaml"),
            "use_sim_time": "True",
        }.items(),
    )

    slam = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mechabot_mapping"),
            "launch",
            "slam.launch.py"
        ),
        launch_arguments={
            "use_sim_time": "True"
        }.items()
    )

    rviz = Node(
        package='rviz2', 
        executable='rviz2', 
        name='rviz', 
        output='screen',
        arguments=['-d', slam_rviz_config_path]
    )

    return LaunchDescription([
        gazebo,
        controller,
        twist_mux,
        slam,
        rviz,
    ])
