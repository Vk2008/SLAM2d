#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, SensorDataQoS

class DroneSafetyFilter(Node):
    def __init__(self):
        super().__init__('drone_safety_filter')
        
        mavros_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Subscriptions
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/mavros/local_position/pose',
            self.pose_callback,
            mavros_qos
        )
        
        # Use SensorDataQoS to handle potential QoS mismatches from the bridge
        self.lidar_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            SensorDataQoS()
        )
        
        self.current_altitude = 0.0
        self.TAKEOFF_ALTITUDE_THRESHOLD = 0.5 
        
        self.SELF_RADIUS = 0.55 
        self.WARNING_DISTANCE = 3.5 

        self.get_logger().info("=============================================")
        self.get_logger().info("  2D LASERSCAN PROXIMITY NODE ACTIVE          ")
        self.get_logger().info("=============================================")

    def pose_callback(self, msg):
        self.current_altitude = msg.pose.position.z

    def scan_callback(self, msg):
        if self.current_altitude < self.TAKEOFF_ALTITUDE_THRESHOLD:
            self.get_logger().info(
                f"[SAFETY] Masked (On Ground). Altitude: {self.current_altitude:.2f}m", 
                throttle_duration_sec=3.0
            )
            return

        min_external_dist = float('inf')
        closest_point = None

        for i, r in enumerate(msg.ranges):
            if math.isnan(r) or math.isinf(r) or r < msg.range_min or r > msg.range_max:
                continue
            
            if r <= self.SELF_RADIUS:
                continue
                
            if r < min_external_dist:
                min_external_dist = r
                angle = msg.angle_min + i * msg.angle_increment
                x = r * math.cos(angle)
                y = r * math.sin(angle)
                closest_point = (x, y)

        if min_external_dist == float('inf'):
            return

        if min_external_dist <= self.WARNING_DISTANCE:
            self.get_logger().warn(
                f"!!! COLLISION WARNING !!! Object detected at {min_external_dist:.2f}m! "
                f"(Relative X: {closest_point[0]:.2f}m, Y: {closest_point[1]:.2f}m)",
                throttle_duration_sec=0.4
            )
        else:
            self.get_logger().info(
                f"[SAFETY] Air Clear. Nearest item at: {min_external_dist:.2f}m", 
                throttle_duration_sec=2.0
            )

def main(args=None):
    rclpy.init(args=args)
    node = DroneSafetyFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()