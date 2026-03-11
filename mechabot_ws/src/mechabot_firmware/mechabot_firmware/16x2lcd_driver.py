#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import smbus2
import time

# I2C LCD Configuration
I2C_ADDR = 0x27  # Default I2C address (can also be 0x3F)
LCD_WIDTH = 16   # Maximum characters per line

# LCD Commands
LCD_CHR = 1  # Mode - Sending data
LCD_CMD = 0  # Mode - Sending command

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line

LCD_BACKLIGHT = 0x08  # On
ENABLE = 0b00000100   # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005


class LCDVelocityDisplay(Node):
    def __init__(self):
        super().__init__('lcd_velocity_display')

        # Subscribe to cmd_vel topic
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # Initialize I2C bus
        try:
            self.bus = smbus2.SMBus(1)  # Rev 2 Pi uses 1
            self.get_logger().info('I2C bus initialized')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize I2C: {e}')
            rclpy.shutdown()
            return

        # Initialize LCD
        self.lcd_init()

        # Display startup message
        self.lcd_string("Robot Velocity", LCD_LINE_1)
        self.lcd_string("Display Ready", LCD_LINE_2)
        time.sleep(2)

        self.get_logger().info('LCD Velocity Display Node started')

    def lcd_init(self):
        """Initialize the LCD display"""
        try:
            self.lcd_byte(0x33, LCD_CMD)  # Initialize
            self.lcd_byte(0x32, LCD_CMD)  # Initialize
            self.lcd_byte(0x06, LCD_CMD)  # Cursor move direction
            self.lcd_byte(0x0C, LCD_CMD)  # Display On, Cursor Off, Blink Off
            self.lcd_byte(0x28, LCD_CMD)  # Data length, number of lines, font size
            self.lcd_byte(0x01, LCD_CMD)  # Clear display
            time.sleep(E_DELAY)
            self.get_logger().info('LCD initialized successfully')
        except Exception as e:
            self.get_logger().error(f'LCD initialization failed: {e}')
            raise

    def lcd_byte(self, bits, mode):
        """Send byte to data pins"""
        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        # High bits
        self.bus.write_byte(I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)

        # Low bits
        self.bus.write_byte(I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)

    def lcd_toggle_enable(self, bits):
        """Toggle enable"""
        time.sleep(E_DELAY)
        self.bus.write_byte(I2C_ADDR, (bits | ENABLE))
        time.sleep(E_PULSE)
        self.bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
        time.sleep(E_DELAY)

    def lcd_string(self, message, line):
        """Send string to display"""
        message = message.ljust(LCD_WIDTH, " ")  # Pad with spaces
        self.lcd_byte(line, LCD_CMD)
        for i in range(LCD_WIDTH):
            self.lcd_byte(ord(message[i]), LCD_CHR)

    def cmd_vel_callback(self, msg):
        """Callback function for cmd_vel subscriber"""
        try:
            linear_x = msg.linear.x
            angular_z = msg.angular.z

            # Format and display on LCD
            # Line 1: Linear velocity
            line1 = f"Lin: {linear_x:+.2f} m/s"
            # Line 2: Angular velocity
            line2 = f"Ang: {angular_z:+.2f} r/s"

            self.lcd_string(line1, LCD_LINE_1)
            self.lcd_string(line2, LCD_LINE_2)

            # Also log to console
            self.get_logger().info(f'Linear X: {linear_x:.2f} m/s, Angular Z: {angular_z:.2f} rad/s')

        except Exception as e:
            self.get_logger().error(f'Error displaying velocity: {e}')

    def destroy_node(self):
        """Cleanup when shutting down"""
        try:
            self.lcd_byte(0x01, LCD_CMD)  # Clear display
            self.lcd_string("Shutting down..", LCD_LINE_1)
            time.sleep(1)
            self.get_logger().info('LCD display cleared')
        except:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = LCDVelocityDisplay()
    except Exception as e:
        print(f"[FATAL] Failed to start node: {e}")
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