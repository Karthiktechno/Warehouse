#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import RPi.GPIO as GPIO
import time
from collections import deque  # For moving average filter

# GPIO pin numbers for the ultrasonic sensor
TRIG_PIN = 17
ECHO_PIN = 27

class DistancePublisher(Node):
    def __init__(self):
        super().__init__('ultrasonic_publisher')

        # Distance publisher
        self.distance_pub = self.create_publisher(Float32, 'ultrasonic_distance', 10)

        # Timer to publish data at 5Hz
        self.timer = self.create_timer(0.2, self.measure_and_publish_distance)

        # GPIO setup
        self.setup_gpio()

        # Buffer for moving average
        self.window_size = 5
        self.distance_buffer = deque(maxlen=self.window_size)

        self.get_logger().info('Ultrasonic Publisher Node started.')

    def setup_gpio(self):
        try:
            GPIO.setwarnings(False)  # Disable warnings
            GPIO.cleanup()  # Clean up any previous GPIO usage
            GPIO.setmode(GPIO.BCM)  # BCM pin numbering
            GPIO.setup(TRIG_PIN, GPIO.OUT)
            GPIO.setup(ECHO_PIN, GPIO.IN)
            GPIO.output(TRIG_PIN, False)
            time.sleep(2)  # Sensor settle time
        except Exception as e:
            self.get_logger().error(f'GPIO Setup Error: {e}')
            GPIO.cleanup()
            rclpy.shutdown()

    def moving_average(self, buffer, new_value):
        buffer.append(new_value)
        return sum(buffer) / len(buffer)

    def measure_and_publish_distance(self):
        try:
            # Trigger ultrasonic pulse
            GPIO.output(TRIG_PIN, True)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(TRIG_PIN, False)

            # Wait for echo to go HIGH
            timeout = time.time() + 1
            while GPIO.input(ECHO_PIN) == 0:
                pulse_start = time.time()
                if pulse_start > timeout:
                    raise TimeoutError("Timeout waiting for ECHO high")

            # Wait for echo to go LOW
            while GPIO.input(ECHO_PIN) == 1:
                pulse_end = time.time()
                if pulse_end > timeout:
                    raise TimeoutError("Timeout waiting for ECHO low")

            # Calculate distance in cm
            pulse_duration = pulse_end - pulse_start
            distance_cm = (pulse_duration * 34300) / 2
            distance_cm = round(distance_cm, 2)

            # Apply moving average filter
            filtered_distance = self.moving_average(self.distance_buffer, distance_cm)

            # Publish Float32 distance
            msg = Float32()
            msg.data = float(filtered_distance) / 100.0  # convert cm to meters
            
            # Print the distance data
            self.get_logger().info(f"Ultrasonic Distance: {msg.data:.3f} m ({filtered_distance:.2f} cm)")
            
            self.distance_pub.publish(msg)

        except TimeoutError as e:
            self.get_logger().warn(str(e))
        except Exception as e:
            self.get_logger().error(f'Error measuring distance: {e}')

    def destroy_node(self):
        self.get_logger().info('Cleaning up GPIO...')
        GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = DistancePublisher()
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