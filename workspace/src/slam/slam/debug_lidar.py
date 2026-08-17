#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import numpy as np

class DebugLidar(Node):
    def __init__(self):
        super().__init__('debug_lidar')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/vessel/lidar/points',
            self.callback,
            10)
        self.count = 0
        self.get_logger().info('===== LIDAR DEBUG NODE STARTED =====')
        self.get_logger().info('Waiting for LiDAR data...')

    def callback(self, msg):
        self.count += 1
        self.get_logger().info(f'\n--- Message #{self.count} ---')
        self.get_logger().info(f'Header: frame_id={msg.header.frame_id}, stamp={msg.header.stamp}')
        self.get_logger().info(f'Width: {msg.width}, Height: {msg.height}')
        self.get_logger().info(f'Point step: {msg.point_step}, Row step: {msg.row_step}')
        self.get_logger().info(f'Is dense: {msg.is_dense}')
        self.get_logger().info(f'Is bigendian: {msg.is_bigendian}')
        
        # Show fields
        field_names = [f.name for f in msg.fields]
        self.get_logger().info(f'Fields: {field_names}')
        
        # Try to read points
        try:
            points = pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
            points_list = list(points)
            self.get_logger().info(f'Number of valid points: {len(points_list)}')
            
            if len(points_list) > 0:
                # Show first 5 points
                self.get_logger().info('First 5 points:')
                for i, p in enumerate(points_list[:5]):
                    self.get_logger().info(f'  Point {i}: x={p[0]:.3f}, y={p[1]:.3f}, z={p[2]:.3f}')
                
                # Calculate statistics
                x_vals = [p[0] for p in points_list]
                y_vals = [p[1] for p in points_list]
                z_vals = [p[2] for p in points_list]
                
                self.get_logger().info(f'X range: {min(x_vals):.3f} to {max(x_vals):.3f}')
                self.get_logger().info(f'Y range: {min(y_vals):.3f} to {max(y_vals):.3f}')
                self.get_logger().info(f'Z range: {min(z_vals):.3f} to {max(z_vals):.3f}')
                
                # Check if all Z values are 0 (2D LiDAR)
                if all(abs(z) < 0.01 for z in z_vals):
                    self.get_logger().info('✅ All Z values are near 0 - This is a 2D LiDAR scan!')
                else:
                    self.get_logger().info('⚠️ Z values vary - This might be 3D LiDAR')
            else:
                self.get_logger().warning('No valid points found!')
                
        except Exception as e:
            self.get_logger().error(f'Error reading points: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = DebugLidar()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()