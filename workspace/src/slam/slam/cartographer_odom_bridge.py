#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from tf2_ros import Buffer, TransformListener, TransformException
from nav_msgs.msg import Odometry


def get_yaw(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    )


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class CartographerOdomBridge(Node):

    def __init__(self):
        super().__init__('cartographer_odom_bridge')

        self.parent_frame = 'odom'
        self.child_frame = 'base_link'

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer, self
        )

        self.publisher = self.create_publisher(
            Odometry,
            '/mavros/odometry/out',
            10
        )

        self.previous = None

        self.timer = self.create_timer(
            1.0 / 30.0,
            self.publish_odometry
        )

        self.get_logger().info(
            'Cartographer odometry bridge started'
        )

    def publish_odometry(self):

        try:
            transform = self.tf_buffer.lookup_transform(
                self.parent_frame,
                self.child_frame,
                Time()
            )
        except TransformException:
            return

        t = transform.transform
        stamp = transform.header.stamp

        timestamp_ns = (
            stamp.sec * 1_000_000_000
            + stamp.nanosec
        )

        if timestamp_ns == 0:
            return

        x = t.translation.x
        y = t.translation.y
        z = t.translation.z

        yaw = get_yaw(t.rotation)

        current = (timestamp_ns, x, y, z, yaw)

        if self.previous is None:
            self.previous = current
            return

        prev_t, px, py, pz, prev_yaw = self.previous

        dt = (timestamp_ns - prev_t) * 1e-9

        self.previous = current

        # Reject duplicate, reversed or stale TF samples.
        if dt <= 0.0 or dt > 0.25:
            return

        # Velocity in the parent (odom) frame.
        vx_world = (x - px) / dt
        vy_world = (y - py) / dt

        # Convert ENU/world velocity into base_link (FLU).
        c = math.cos(yaw)
        s = math.sin(yaw)

        vx_body = c * vx_world + s * vy_world
        vy_body = -s * vx_world + c * vy_world

        # Planar angular velocity.
        yaw_rate = wrap_angle(yaw - prev_yaw) / dt

        msg = Odometry()

        msg.header.stamp = stamp
        msg.header.frame_id = self.parent_frame
        msg.child_frame_id = self.child_frame

        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = z

        msg.pose.pose.orientation = t.rotation

        msg.twist.twist.linear.x = vx_body
        msg.twist.twist.linear.y = vy_body
        msg.twist.twist.linear.z = 0.0

        msg.twist.twist.angular.x = 0.0
        msg.twist.twist.angular.y = 0.0
        msg.twist.twist.angular.z = yaw_rate

        # Initial SITL covariance assumptions (variances).
        # These must be calibrated for the real sensor later.
        msg.pose.covariance[0] = 0.05 ** 2
        msg.pose.covariance[7] = 0.05 ** 2
        msg.pose.covariance[14] = 0.05 ** 2

        msg.pose.covariance[21] = math.radians(3) ** 2
        msg.pose.covariance[28] = math.radians(3) ** 2
        msg.pose.covariance[35] = math.radians(5) ** 2

        msg.twist.covariance[0] = 0.1 ** 2
        msg.twist.covariance[7] = 0.1 ** 2
        msg.twist.covariance[14] = 0.1 ** 2

        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = CartographerOdomBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
