#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from sensor_msgs.msg import Image, LaserScan, Imu
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import Int8
from cv_bridge import CvBridge
import cv2
import math
import numpy as np
import tf_transformations

class DockingNode(Node):
    def __init__(self):
        super().__init__('simple_docking_node')
        
        self.UNDOCK_DISTANCE = 4.0      
        self.DOCK_STOP_DISTANCE = 0.2   
        self.PREDOCK_DISTANCE = 0.8    
        
        self.DOCK_X = 2.0
        self.DOCK_Y = 5.0
        self.DOCK_THETA = 0.0
        
        self.PATROL_WAYPOINTS = [
            [0.0, 0.0, 0.0],
            [-5.0, 0.0, 1.57],
            [5.0, 1.0, 3.14],
            [2.0, 1.0, -1.57],
        ]
        
        self.bridge = CvBridge()
        self.qr_decoder = cv2.QRCodeDetector()
        self.nav = BasicNavigator() 
        
        self.state = "UNDOCKING"
        self.battery_status = -1
        
        self.qr_detected = False
        self.qr_center_x = 0
        self.image_width = 640
        self.front_distance = 10.0
        self.current_yaw = 0.0
        
        self.traveled_distance = 0.0
        self.target_yaw = 0.0
        
        self.create_subscription(Image, '/camera/image_raw', self.camera_callback, 10)
        self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.create_subscription(Imu, '/imu/out', self.imu_callback, 10)
        self.create_subscription(Int8, '/battery_status', self.battery_callback, 10)
        
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.create_timer(0.1, self.control_loop)
        
        print("Docking Node Started!")
        print("Send 0 to /battery_status to RETURN TO DOCK")
    
    def camera_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        self.image_width = frame.shape[1]
        
        data, points, _ = self.qr_decoder.detectAndDecode(frame)
        
        self.qr_detected = False
        
        if points is not None and data:
            data = data.lower().strip()
            
            if data == "stop":
                self.qr_detected = True
                points = points[0].astype(int)
                self.qr_center_x = int(np.mean(points[:, 0]))
                
                cv2.polylines(frame, [points], True, (0, 255, 0), 3)
                image_center = self.image_width // 2
                cv2.line(frame, (image_center, 0), (image_center, frame.shape[0]), (255, 0, 0), 2)
                cv2.putText(frame, 'QR FOUND!', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.putText(frame, f'State: {self.state}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.imshow('Camera', frame)
        cv2.waitKey(1)
    
    def lidar_callback(self, msg):
        ranges = np.array(msg.ranges)
        front_rays = np.concatenate([ranges[-20:], ranges[:20]])
        front_rays = front_rays[np.isfinite(front_rays)]
        if len(front_rays) > 0:
            self.front_distance = np.mean(front_rays)
    
    def imu_callback(self, msg):
        x = msg.orientation.x
        y = msg.orientation.y
        z = msg.orientation.z
        w = msg.orientation.w
        self.current_yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    
    def battery_callback(self, msg):
        self.battery_status = msg.data
        
        if msg.data == 0:
            print("BATTERY LOW - Canceling patrol and returning to dock!")
            self.nav.cancelTask()
            self.state = "GOING_TO_DOCK"
            
        elif msg.data == -1:
            print("STAY command - stopping robot")
            self.nav.cancelTask()
            self.state = "DOCKED"
    
    def control_loop(self):
        vel = Twist()
        
        if self.state == "UNDOCKING":
            vel.linear.x = -0.2
            vel.angular.z = 0.0
            
            self.traveled_distance += 0.2 * 0.1
            
            if self.traveled_distance >= self.UNDOCK_DISTANCE:
                print("Undocked! Now rotating...")
                self.state = "ROTATING"
                self.target_yaw = self.normalize_angle(self.current_yaw + 1.57)  # +90°
        
        elif self.state == "ROTATING":
            vel.linear.x = 0.0
            vel.angular.z = 0.4
            
            yaw_diff = self.normalize_angle(self.target_yaw - self.current_yaw)
            
            if abs(yaw_diff) < 0.1:
                print("Rotation done! Starting patrol...")
                self.state = "PATROLLING"
                self.start_patrol()
        
        elif self.state == "PATROLLING":
            if not self.nav.isTaskComplete():
                vel.linear.x = 0.0
                vel.angular.z = 0.0
            else:
                print("Patrol complete! Returning to dock...")
                self.state = "GOING_TO_DOCK"
                self.go_to_predock()
        
        elif self.state == "GOING_TO_DOCK":
            if not self.nav.isTaskComplete():
                vel.linear.x = 0.0
                vel.angular.z = 0.0
            else:
                print("Reached pre-dock! Starting final docking...")
                self.state = "DOCKING"
        
        elif self.state == "DOCKING":
            if self.front_distance <= self.DOCK_STOP_DISTANCE:
                vel.linear.x = 0.0
                vel.angular.z = 0.0
                self.state = "DOCKED"
                print("DOCKED!")
            
            elif self.qr_detected:
                image_center = self.image_width // 2
                offset = self.qr_center_x - image_center
                
                vel.angular.z = -offset * 0.003
                
                if abs(offset) < 50:
                    vel.linear.x = 0.15
                else:
                    vel.linear.x = 0.08
            
            else:
                vel.linear.x = 0.1
                vel.angular.z = 0.0
        
        elif self.state == "DOCKED":
            vel.linear.x = 0.0
            vel.angular.z = 0.0
        
        self.vel_pub.publish(vel)
    
    def create_pose(self, x, y, theta):
        q_x, q_y, q_z, q_w = tf_transformations.quaternion_from_euler(0.0, 0.0, theta)
        
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.nav.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = q_x
        pose.pose.orientation.y = q_y
        pose.pose.orientation.z = q_z
        pose.pose.orientation.w = q_w
        
        return pose
    
    def start_patrol(self):
        print("Sending waypoints to Nav2...")
        
        self.nav.waitUntilNav2Active()
        
        waypoints = []
        for wp in self.PATROL_WAYPOINTS:
            waypoints.append(self.create_pose(wp[0], wp[1], wp[2]))
        
        self.nav.followWaypoints(waypoints)
        print("Patrol started!")
    
    def go_to_predock(self):
        print("Going to pre-dock position...")
        
        predock_x = self.DOCK_X - self.PREDOCK_DISTANCE * math.cos(self.DOCK_THETA)
        predock_y = self.DOCK_Y - self.PREDOCK_DISTANCE * math.sin(self.DOCK_THETA)
        
        predock_pose = self.create_pose(predock_x, predock_y, self.DOCK_THETA)
        
        self.nav.goToPose(predock_pose)
        print("Navigating to pre-dock...")
    
    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

def main(args=None):
    rclpy.init(args=args)
    node = DockingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()