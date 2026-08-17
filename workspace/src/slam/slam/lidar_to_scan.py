#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, LaserScan
import sensor_msgs_py.point_cloud2 as pc2
import math

class LidarToScan(Node):
    def __init__(self):
        super().__init__('lidar_to_scan')
        
        # Publisher for LaserScan
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        
        # Subscriber to 2D LiDAR point cloud
        self.subscription = self.create_subscription(
            PointCloud2,
            '/vessel/lidar/points',
            self.pointcloud_callback,
            10
        )
        
        self.get_logger().info('2D LiDAR to LaserScan converter started')

    def pointcloud_callback(self, msg):
        # Create LaserScan message
        scan = LaserScan()
        scan.header = msg.header
        scan.header.frame_id = 'iris_with_gimbal/lidar_link/gpu_lidar'
        
        # 2D LiDAR parameters (horizontal scan only)
        scan.angle_min = -3.14159265
        scan.angle_max = 3.14159265
        scan.angle_increment = (3.14159265 * 2) / 720.0  # 720 samples
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = 0.2
        scan.range_max = 30.0
        
        # Read points from PointCloud2
        points = pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
        
        ranges = []
        intensities = []
        
        for p in points:
            # Calculate distance in XY plane (2D)
            dist = math.sqrt(p[0]*p[0] + p[1]*p[1])
            
            if dist >= scan.range_min and dist <= scan.range_max:
                ranges.append(dist)
                intensities.append(0.0)  # No intensity data
            else:
                ranges.append(float('inf'))
                intensities.append(0.0)
        
        # Pad to exactly 720 samples if needed
        while len(ranges) < 720:
            ranges.append(float('inf'))
            intensities.append(0.0)
        
        # Trim if more than 720
        if len(ranges) > 720:
            ranges = ranges[:720]
            intensities = intensities[:720]
        
        scan.ranges = ranges
        scan.intensities = intensities
        
        self.scan_pub.publish(scan)

def main(args=None):
    rclpy.init(args=args)
    node = LidarToScan()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()