import time
import random  # Simulating sensor data

# Lists to store rolling averages
x_list = []
y_list = []
z_list = []

def rolling_average(x_list, y_list, z_list):
    """Calculates the rolling average of the last 10 readings."""
    if not x_list:  # Avoid division by zero
        return 0, 0, 0

    x_avg = sum(x_list) / len(x_list)
    y_avg = sum(y_list) / len(y_list)
    z_avg = sum(z_list) / len(z_list)

    return x_avg, y_avg, z_avg

while True:
    # Simulating raw sensor readings
    raw_x = random.uniform(-180, 180)  # Simulated angle range
    raw_y = random.uniform(-90, 90)    # Simulated angle range
    raw_z = random.uniform(-90, 90)    # Simulated angle range

    print(f"raw_x: {raw_x:.2f}")
    print(f"raw_y: {raw_y:.2f}")
    print(f"raw_z: {raw_z:.2f}")

    # Keep last 10 values for rolling average
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

    time.sleep(0.1)  # Adds delay to simulate real-time processing
