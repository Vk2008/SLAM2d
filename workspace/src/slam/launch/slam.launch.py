from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import AnyLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        
        # 1. Foxglove WebSocket Bridge
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            parameters=[{'use_sim_time': True}],
            output='screen',
        ),

        # 2. Gazebo Bridge with explicit type
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='lidar_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '/vessel/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            ],
            output='screen',
            # Add this to see more debug info
            prefix=['stdbuf', '-o', 'L'],
        ),

        # 3. Static TF2 Publisher
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='lidar_tf_publisher',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '0', '0', '-0.1', '0', '0', '0', 
                'base_link', 'iris_with_gimbal/lidar_link/gpu_lidar'
            ],
            output='screen'
        ),

        # 4. MAVROS
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(
                os.path.join(get_package_share_directory('mavros'), 'launch', 'apm.launch')
            ),
            launch_arguments={
                'fcu_url': 'udp://127.0.0.1:14550@14555',
                'use_sim_time': 'true',
            }.items()
        ),
    ])