import os
from launch import LaunchDescription
from launch_ros.actions import Node

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

        # # Static TF Chain
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     name='static_tf_map_odom',
        #     arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        #     parameters=[{'use_sim_time': True}]
        # ),
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     name='static_tf_odom_base',
        #     arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'],
        #     parameters=[{'use_sim_time': True}]
        # ),
        # # ok
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     name='static_tf_vessel_lidar',
        #     arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'vessel/lidar'],
        #     parameters=[{'use_sim_time': True}]
        # ),

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