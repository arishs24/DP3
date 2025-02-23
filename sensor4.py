import time
import smbus
import RPi.GPIO as GPIO
from gpiozero import Servo, LED
from board import SCL, SDA
import busio
import adafruit_mpu6050  # MPU6050 Library

# 🔹 Initialize Raspberry Pi I2C Bus
i2c = busio.I2C(SCL, SDA)
mpu = adafruit_mpu6050.MPU6050(i2c)

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(18)  # Servo on GPIO18 (Pin 12)

# 🔹 Rolling Average Data Storage
x_list, y_list, z_list = [], [], []

def read_mpu6050():
    """ Reads acceleration and Euler angles from MPU6050 """
    try:
        accel = mpu.acceleration
        angles = mpu.gyro  # Gyroscope for orientation
        return accel, angles
    except Exception as e:
        print(f"⚠️ MPU6050 Error: {e}")
        return None, None

def rolling_average(x_list, y_list, z_list):
    """ Computes rolling averages for X, Y, and Z angles """
    x_avg = sum(x_list) / len(x_list)
    y_avg = sum(y_list) / len(y_list)
    z_avg = sum(z_list) / len(z_list)

    # Adjust X/Z values for better range mapping
    if x_avg < 130:
        x_avg += 360
    if z_avg < 180:
        z_avg += 60

    print("ROLLING AVERAGE: ", x_avg, y_avg, z_avg)
    return x_avg, y_avg, z_avg

def within_limit(value, lower, upper):
    """ Checks if value is within a range """
    return lower < value < upper

def within_limit_y(y_angle, lower, upper):
    """ Determines if Y angle is within limit, under, or over """
    if lower < y_angle < upper:
        return 0  # Within limit
    elif y_angle < lower:
        return 1  # Under limit
    else:
        return 2  # Over limit

def main():
    """ Main loop: Reads sensor data, calculates rolling averages, and controls LED + Servo """
    while True:
        # 1️⃣ Read Sensor Data
        accel, angles = read_mpu6050()
        if accel is None or angles is None:
            continue  # Skip iteration if sensor fails

        raw_x, raw_y, raw_z = angles  # Assign Gyro angles

        # 2️⃣ Update Rolling Average
        x_list.append(raw_x)
        y_list.append(raw_y)
        z_list.append(raw_z)

        if len(x_list) > 10:
            x_list.pop(0)
            y_list.pop(0)
            z_list.pop(0)

        avg_x, avg_y, avg_z = rolling_average(x_list, y_list, z_list)

        # 3️⃣ Check Limits
        check_limit_x = within_limit(avg_x, 200, 400)
        check_limit_y = within_limit_y(avg_y, -0.1, -78)
        check_limit_z = within_limit(avg_z, 0, 120)

        # 4️⃣ LED Alert (Bad Form Detection)
        if not check_limit_x or not check_limit_z:
            print("🚨 INCORRECT FORM DETECTED (X or Z)")
            red_led.on()
        else:
            red_led.off()

        # 5️⃣ Adjust Resistance (Servo Control)
        if check_limit_y == 0:
            print("✅ Good Posture")
            servo.value = 0  # Neutral position
        elif check_limit_y == 1:
            print("⬇️ UNDER! Adjusting resistance...")
            servo.value = -0.8  # Gradual resistance increase
        elif check_limit_y == 2:
            print("⬆️ OVER! Adjusting resistance...")
            servo.value = 0.8  # Gradual resistance decrease

        time.sleep(0.5)

if __name__ == "__main__":
    main()
