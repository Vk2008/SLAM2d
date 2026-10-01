import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    pkg_share = get_package_share_directory('slam')
    cartographer_config_dir = os.path.join(pkg_share, 'config')
    configuration_basename = 'cartographer.lua'

    return LaunchDescription([
        # 1. Foxglove Bridge
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),

        # 2. ROS-GZ Parameter Bridge (Laser, Clock, Odom, IMU)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=[
                '/vessel/lidar@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/model/iris_with_gimbal/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/model/iris_with_gimbal/imu@sensor_msgs/msg/Imu[gz.msgs.IMU'
            ],
            remappings=[
                ('/model/iris_with_gimbal/odometry', '/gazebo/odometry'),
                ('/model/iris_with_gimbal/imu', '/imu/data')
            ],
            parameters=[{'use_sim_time': True}]
        ),

        # 3. Static Transform for LiDAR
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

        # 4. MAVROS Integration
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(
                os.path.join(get_package_share_directory('mavros'), 'launch', 'apm.launch')
            ),
            launch_arguments={
                'fcu_url': 'udp://127.0.0.1:14550@14555',
                'use_sim_time': 'true',
            }.items()
        ),

        # 5. Cartographer Node
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '-configuration_directory', cartographer_config_dir,
                '-configuration_basename', configuration_basename
            ],
            remappings=[
                ('scan', '/vessel/lidar'),
                ('odom', '/odom')
            ]
        ),

        # 6. Cartographer Occupancy Grid Node
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '-resolution', '0.05',
                '-publish_period_sec', '1.0'
            ]
        ),

        # 7. EKF Localization Node (Replaces odom_to_tf_relay)
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {
                    'frequency': 30.0,
                    'sensor_timeout': 0.1,
                    'two_d_mode': True,
                    'publish_tf': True,
                    'map_frame': 'map',
                    'odom_frame': 'odom',
                    'base_link_frame': 'base_link',
                    'world_frame': 'odom',
                    'imu0': '/imu/data',
                    'imu0_config': [
                        False, False, False, 
                        False, False, True,   # Yaw orientation from IMU
                        False, False, False, 
                        False, False, True,   # Angular velocity
                        True,  True,  False   # Linear acceleration
                    ],
                    'imu0_differential': False,
                    'imu0_relative': False,
                }
            ],
            remappings=[('odometry/filtered', '/odom')]
        ),
    ])