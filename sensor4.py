import time
from sensor_library import *  # Your existing sensor module
from gpiozero import Servo, LED, Motor

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo motor on GPIO8
motor = Motor(forward=17, backward=27)  # Motor Control (L298N Driver)

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 Calibration Values
calibrated_x = 0
calibrated_y = 0
calibrated_z = 0

def calibrate_sensor():
    """
    Captures initial sensor values as the "neutral" posture reference.
    """
    global calibrated_x, calibrated_y, calibrated_z
    
    print("📏 Starting Calibration... Hold still for 5 seconds.")
    x_list, y_list, z_list = [], [], []

    for _ in range(10):  # Collect data for calibration
        angles = sensor.euler_angles()
        x_list.append(angles[0])
        y_list.append(angles[1])
        z_list.append(angles[2])
        time.sleep(0.5)

    # Compute the average as the calibrated neutral position
    calibrated_x = sum(x_list) / len(x_list)
    calibrated_y = sum(y_list) / len(y_list)
    calibrated_z = sum(z_list) / len(z_list)

    print(f"✅ Calibration Complete: X={calibrated_x:.2f}, Y={calibrated_y:.2f}, Z={calibrated_z:.2f}")
    print("🎯 Starting Posture Tracking...")

def main():
    """
    Main loop: Reads sensor data, applies calibration, and controls motor + servo.
    """
    x_list, y_list, z_list = [], [], []  # Rolling average storage

    # Run calibration first
    calibrate_sensor()

    while True:
        try:
            # 1️⃣ Read Sensor Data
            angles = sensor.euler_angles()
            raw_x, raw_y, raw_z = angles  

            # Apply calibration (adjust relative to neutral position)
            adj_x = raw_x - calibrated_x
            adj_y = raw_y - calibrated_y
            adj_z = raw_z - calibrated_z

            # 2️⃣ Store values for rolling average
            x_list.append(adj_x)
            y_list.append(adj_y)
            z_list.append(adj_z)

            if len(x_list) > 10:
                x_list.pop(0)
                y_list.pop(0)
                z_list.pop(0)

            # 3️⃣ Compute rolling average
            avg_x, avg_y, avg_z = rolling_average(x_list, y_list, z_list)

            # 4️⃣ Check Limits for Correct Posture
            check_limit_x = within_limit(avg_x, -50, 50)  # Neutral range
            check_limit_y = within_limit_y(avg_y, -10, 10)  # Custom threshold
            check_limit_z = within_limit(avg_z, -30, 30)  # Neutral range

            # 5️⃣ LED Alert for Incorrect Form
            if not check_limit_x or not check_limit_z:
                print("🚨 Incorrect Form Detected!")
                red_led.on()
            else:
                red_led.off()

            # 6️⃣ Servo & Motor Control for Resistance Adjustment
            if check_limit_y == 0:
                print("✅ Good Posture")
                servo.mid()  # Set to neutral position
                motor.stop()  # Stop motor
            elif check_limit_y == 1:
                print("⬇️ UNDER! Increasing Resistance...")
                servo.max()  # Move servo to max resistance
                motor.forward(0.7)  # Increase motor tension (PWM speed 70%)
                time.sleep(0.5)  # Delay to let motor adjust
                motor.stop()  # Stop after adjustment
            elif check_limit_y == 2:
                print("⬆️ OVER! Decreasing Resistance...")
                servo.min()  # Move servo to minimum resistance
                motor.backward(0.7)  # Decrease motor tension (PWM speed 70%)
                time.sleep(0.5)  # Delay to let motor adjust
                motor.stop()  # Stop after adjustment

            # 7️⃣ Display Data for Debugging
            print(f"CALIBRATED ANGLES -> X: {avg_x:.2f}, Y: {avg_y:.2f}, Z={avg_z:.2f}")

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")
        
        time.sleep(0.5)

def rolling_average(x_list, y_list, z_list):
    """
    Computes rolling averages for X, Y, and Z angles.
    """
    x_avg = sum(x_list) / len(x_list)
    y_avg = sum(y_list) / len(y_list)
    z_avg = sum(z_list) / len(z_list)

    return x_avg, y_avg, z_avg

def within_limit(value, lower, upper):
    """Checks if a value is within a given range."""
    return lower < value < upper

def within_limit_y(y_angle, lower, upper):
    """
    Determines if Y angle is within limit, under, or over.
    Returns:
        0 → Within limit
        1 → Under limit
        2 → Over limit
    """
    if lower < y_angle < upper:
        return 0
    elif y_angle < lower:
        return 1
    else:
        return 2

if __name__ == "__main__":
    main()
