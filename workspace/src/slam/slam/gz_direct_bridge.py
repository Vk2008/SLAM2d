#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
import gz.transport as gz_transport
from gz.msgs.pointcloud_packed_pb2 import PointCloudPacked
import struct
import numpy as np

class GzDirectBridge(Node):
    def __init__(self):
        super().__init__('gz_direct_bridge')
        
        # ROS publisher
        self.publisher = self.create_publisher(PointCloud2, '/lidar/points', 10)
        
        # Gazebo subscriber
        self.gz_node = gz_transport.Node()
        
        # Subscribe to the Gazebo topic
        try:
            self.gz_node.subscribe('/vessel/lidar/points', self.gz_callback)
            self.get_logger().info('✅ Subscribed to /vessel/lidar/points in Gazebo')
        except Exception as e:
            self.get_logger().error(f'Failed to subscribe to Gazebo topic: {e}')
        
        self.get_logger().info('✅ Gazebo Direct Bridge started')
        self.get_logger().info('📤 Publishing to /lidar/points in ROS')
        self.count = 0
        
    def gz_callback(self, msg):
        try:
            self.count += 1
            if self.count % 10 == 0:  # Log every 10th message
                self.get_logger().info(f'Received message #{self.count} from Gazebo')
            
            # Parse the point cloud
            pc = PointCloudPacked()
            pc.ParseFromString(msg)
            
            # Create ROS PointCloud2 message
            ros_msg = PointCloud2()
            ros_msg.header = Header()
            ros_msg.header.stamp = self.get_clock().now().to_msg()
            
            # Extract frame_id from metadata
            frame_id = "iris_with_gimbal/lidar_link/gpu_lidar"
            for data in pc.header.data:
                if data.key == "frame_id":
                    frame_id = data.value
                    break
            ros_msg.header.frame_id = frame_id
            
            # Set fields (only x, y, z)
            ros_msg.fields = [
                PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            ]
            
            ros_msg.height = pc.height
            ros_msg.width = pc.width
            ros_msg.is_bigendian = False
            ros_msg.point_step = 12  # 3 * 4 bytes
            ros_msg.row_step = ros_msg.point_step * ros_msg.width
            ros_msg.is_dense = True
            
            # Extract x, y, z from the data
            # Each point: x, y, z, intensity, ring
            data_bytes = bytearray()
            for i in range(pc.width):
                offset = i * pc.point_step
                # Extract x, y, z (12 bytes)
                data_bytes.extend(pc.data[offset:offset+12])
            
            ros_msg.data = bytes(data_bytes)
            
            # Publish to ROS
            self.publisher.publish(ros_msg)
            
            if self.count % 10 == 0:
                self.get_logger().info(f'✅ Published {pc.width} points to /lidar/points')
            
        except Exception as e:
            self.get_logger().error(f'Error processing message: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = GzDirectBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()