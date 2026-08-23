import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        # Foxglove Bridge
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),

        # ROS-GZ Parameter Bridge for 2D LaserScan
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=[
                '/vessel/lidar@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/model/iris_with_gimbal/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'
            ],
            remappings=[
                ('/model/iris_with_gimbal/odometry', '/odom')
            ],
            parameters=[{'use_sim_time': True}]
        ),

        # OK
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='lidar_tf_publisher',
            parameters=[{'use_sim_time': True}], # <-- Added Sim Time
            arguments=[
                '0', '0', '-0.1', '0', '0', '0', 
                'base_link', 'iris_with_gimbal/lidar_link/gpu_lidar'
            ],
            output='screen'
        ),

        # OK
        Node(
            package='slam',
            executable='odom_to_tf_relay',
            name='odom_to_tf_relay',
            parameters=[{'use_sim_time': True}], # <-- Added Sim Time
            output='screen'
        ),

        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(
                os.path.join(get_package_share_directory('mavros'), 'launch', 'apm.launch')
            ),
            launch_arguments={
                'fcu_url': 'udp://127.0.0.1:14550@14555',
                'use_sim_time': 'true',          # <-- Added Sim Time for MAVROS
            }.items()
        ),

        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',
                'scan_topic': '/vessel/lidar',
                'mode': 'mapping'
            }]
        )
    ])
