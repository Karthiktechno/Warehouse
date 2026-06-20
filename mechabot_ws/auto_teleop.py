import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import math

class AutoTeleop(Node):
    def __init__(self):
        super().__init__('auto_teleop')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.twist_msg = Twist()
        self.state = 'FORWARD'
        self.turn_count = 0

    def scan_callback(self, msg):
        # The laser scan usually goes from -180 to 180 degrees or similar.
        # We check the front arc (e.g. -30 to 30 degrees)
        ranges = msg.ranges
        num_ranges = len(ranges)
        
        # If no data, do nothing
        if num_ranges == 0:
            return
            
        front_arc = int(num_ranges * 0.1)  # 10% on each side of the center
        center = num_ranges // 2
        
        front_ranges = ranges[center - front_arc : center + front_arc]
        
        # Filter out invalid values (inf, nan) and find min distance
        valid_ranges = [r for r in front_ranges if not math.isinf(r) and not math.isnan(r) and r > 0.0]
        
        min_dist = min(valid_ranges) if valid_ranges else float('inf')
        
        # Simple obstacle avoidance state machine
        if min_dist < 1.0:
            self.state = 'TURN'
            self.turn_count = 15  # turn for 1.5 seconds (15 * 0.1s)
        elif self.turn_count == 0:
            self.state = 'FORWARD'

    def timer_callback(self):
        if self.state == 'FORWARD':
            self.twist_msg.linear.x = 0.5
            self.twist_msg.angular.z = 0.0
        elif self.state == 'TURN':
            self.twist_msg.linear.x = 0.0
            self.twist_msg.angular.z = 0.5  # turn left
            if self.turn_count > 0:
                self.turn_count -= 1
        
        self.publisher_.publish(self.twist_msg)

def main(args=None):
    rclpy.init(args=args)
    auto_teleop = AutoTeleop()
    rclpy.spin(auto_teleop)
    auto_teleop.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
