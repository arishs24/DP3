import time
from sensor_library import *

sensor = Orientation_sensor()

# Lists to store rolling averages
x_list = []
y_list = []
z_list = []

def rolling_average(x_list, y_list, z_list):
    if len(x_list) == 0:  # Prevent division by zero
        return 0, 0, 0

    x_avg = sum(x_list) / len(x_list)
    y_avg = sum(y_list) / len(y_list)
    z_avg = sum(z_list) / len(z_list)

    return x_avg, y_avg, z_avg

while True:
    angles = sensor.euler_angles()
    lin_accel = sensor.lin_acceleration()
    accel = sensor.accelerometer()  # Fixed typo

    raw_x = angles[0]
    raw_y = angles[1]
    raw_z = angles[2]

    print(f"raw_x: {raw_x}")
    print(f"raw_y: {raw_y}")
    print(f"raw_z: {raw_z}")

    # Keep last 10 values
    if len(x_list) >= 10:
        x_list.pop(0)
        y_list.pop(0)
        z_list.pop(0)

    x_list.append(raw_x)
    y_list.append(raw_y)
    z_list.append(raw_z)

    # Compute rolling average
    x_avg, y_avg, z_avg = rolling_average(x_list, y_list, z_list)
    print(f"Rolling Averages -> X: {x_avg:.2f}, Y: {y_avg:.2f}, Z: {z_avg:.2f}")

    time.sleep(0.1)  # Prevents excessive CPU usage
