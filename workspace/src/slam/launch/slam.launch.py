from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        
        # 1. Foxglove Bridge
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            parameters=[{
                'use_sim_time': True,
                'port': 8765,
            }],
            output='screen',
        ),

        # 2. Gazebo Bridge - FIXED FORMAT
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='lidar_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=[
                # CORRECT FORMAT: ros_topic@ros_type[gz_type
                '/vessel/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked'
            ],
            output='screen',
            # Add remapping to make the topic name simpler
            remappings=[
                ('/vessel/lidar/points', '/lidar/points')
            ]
        ),

        # 3. Static TF2 Publisher
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='lidar_tf_publisher',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '0', '0', '-0.1', '0', '0', '0', 
                'base_link', 'lidar_link'
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
            }.items(),
        ),
    ])
