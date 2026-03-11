#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class CameraViewer(Node):
    def __init__(self):
        super().__init__('camera_viewer')
        
        # Create CV Bridge to convert ROS Image to OpenCV format
        self.bridge = CvBridge()
        
        # Subscribe to the camera image topic
        self.image_sub = self.create_subscription(
            Image,
            '/image_raw',  # Default topic from v4l2_camera
            self.image_callback,
            10
        )
        
        # Create OpenCV window
        self.window_name = 'Camera Feed'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        self.get_logger().info('Camera Viewer Node started')
        self.get_logger().info('Subscribing to /image_raw topic')
        self.get_logger().info('Press "q" in the window to quit')
        
        # Frame counter for FPS display
        self.frame_count = 0

    def image_callback(self, msg):
        """Callback function to display camera images"""
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Add frame counter to image
            self.frame_count += 1
            cv2.putText(cv_image, f'Frame: {self.frame_count}', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 255, 0), 2)
            
            # Display the image
            cv2.imshow(self.window_name, cv_image)
            
            # Wait for 1ms and check for 'q' key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.get_logger().info('Quit key pressed. Shutting down...')
                rclpy.shutdown()
                
        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')

    def destroy_node(self):
        """Cleanup when shutting down"""
        cv2.destroyAllWindows()
        self.get_logger().info('Camera viewer closed')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = CameraViewer()
    except Exception as e:
        print(f"Failed to start node: {e}")
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()