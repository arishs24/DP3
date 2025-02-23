import time
from sensor_library import *  # Using your sensor library
from gpiozero import Servo, LED

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo motor on GPIO8

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 Store last 10 readings for rolling average
x_list, y_list, z_list = [], [], []

def main():
    """
    Main loop: Reads sensor data, computes rolling averages, and controls servo + LED.
    """
    while True:
        try:
            # 1️⃣ Read Sensor Data
            angles = sensor.euler_angles()
            lin_accel = sensor.lin_acceleration()
            accel = sensor.accelerometer()

            # Extract angles for X, Y, Z
            raw_x, raw_y, raw_z = angles  

            # 2️⃣ Store values for rolling average
            x_list.append(raw_x)
            y_list.append(raw_y)
            z_list.append(raw_z)

            # Keep only last 10 readings for smooth data
            if len(x_list) > 10:
                x_list.pop(0)
                y_list.pop(0)
                z_list.pop(0)

            # 3️⃣ Compute rolling average
            avg_x, avg_y, avg_z = rolling_average(x_list, y_list, z_list)

            # 4️⃣ Check Limits for Correct Posture
            check_limit_x = within_limit(avg_x, 200, 400)
            check_limit_y = within_limit_y(avg_y, -0.1, -78)
            check_limit_z = within_limit(avg_z, 0, 120)

            # 5️⃣ LED Alert for Incorrect Form
            if not check_limit_x or not check_limit_z:
                print("🚨 Incorrect Form Detected (X or Z Out of Range)")
                red_led.on()
            else:
                red_led.off()

            # 6️⃣ Servo Control for Resistance Adjustment
            if check_limit_y == 0:
                print("✅ Good Posture")
                servo.value = 0  # Neutral position
            elif check_limit_y == 1:
                print("⬇️ UNDER! Increasing Resistance")
                servo.value = -0.6  # Gradual increase in resistance
            elif check_limit_y == 2:
                print("⬆️ OVER! Decreasing Resistance")
                servo.value = 0.6  # Gradual decrease in resistance

            # 7️⃣ Display Data for Debugging
            print(f"ANGLES -> X: {avg_x:.2f}, Y: {avg_y:.2f}, Z: {avg_z:.2f}")

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")
        
        time.sleep(0.5)

def rolling_average(x_list, y_list, z_list):
    """
    Computes rolling averages for X, Y, and Z sensor data.
    """
    x_avg = sum(x_list) / len(x_list)
    y_avg = sum(y_list) / len(y_list)
    z_avg = sum(z_list) / len(z_list)

    if x_avg < 130:
        x_avg += 360
    if z_avg < 180:
        z_avg += 60

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
