import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import GroupAction
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import SetParameter
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
        GroupAction(
            scoped=True,
            actions=[
                SetParameter(
                    name='use_sim_time',
                    value=True
                ),

                IncludeLaunchDescription(
                    AnyLaunchDescriptionSource(
                        os.path.join(
                            get_package_share_directory('mavros'),
                            'launch',
                            'apm.launch'
                        )
                    ),
                    launch_arguments={
                        'fcu_url': 'udp://127.0.0.1:14550@14555',
                    }.items()
                )
            ]
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
                ('imu', '/mavros/imu/data_raw')
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

        # 7. MAVROS Service Call to increase IMU publish rate
        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'service', 'call',
                        '/mavros/cmd/command',
                        'mavros_msgs/srv/CommandLong',
                        '{broadcast: false, command: 511, confirmation: 0, '
                        'param1: 105.0, param2: 20000.0, '
                        'param3: 0.0, param4: 0.0, '
                        'param5: 0.0, param6: 0.0, param7: 0.0}'
                    ],
                    output='screen'
                )
            ]
        ),
    ])
