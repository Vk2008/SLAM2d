#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
import numpy as np
import struct

class LidarRepublisher(Node):
    def __init__(self):
        super().__init__('lidar_republisher')
        
        # Publisher for cleaned point cloud
        self.publisher = self.create_publisher(PointCloud2, '/lidar/points_cleaned', 10)
        
        # Subscriber to the bridge
        self.subscription = self.create_subscription(
            PointCloud2,
            '/vessel/lidar/points',
            self.lidar_callback,
            10
        )
        
        self.get_logger().info('LiDAR Republisher started')

    def lidar_callback(self, msg):
        try:
            # Create a new point cloud message with only x,y,z fields
            new_msg = PointCloud2()
            new_msg.header = msg.header
            new_msg.header.frame_id = 'iris_with_gimbal/lidar_link/gpu_lidar'
            
            # Only keep x, y, z fields
            new_msg.fields = [
                PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            ]
            
            new_msg.height = msg.height
            new_msg.width = msg.width
            new_msg.is_bigendian = msg.is_bigendian
            new_msg.point_step = 12  # 3 * 4 bytes
            new_msg.row_step = new_msg.point_step * new_msg.width
            new_msg.is_dense = True
            
            # Extract x, y, z from the original message
            # Skip intensity (4 bytes) and ring (2 bytes)
            new_data = bytearray()
            for i in range(msg.width):
                offset = i * msg.point_step
                # Extract x, y, z (12 bytes)
                new_data.extend(msg.data[offset:offset+12])
            
            new_msg.data = bytes(new_data)
            
            self.publisher.publish(new_msg)
            self.get_logger().debug(f'Published {msg.width} points')
            
        except Exception as e:
            self.get_logger().error(f'Error processing LiDAR data: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = LidarRepublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()