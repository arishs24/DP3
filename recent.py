import time
import threading
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gpiozero import Servo, LED
from sensor_library import *

red_led = LED(6)
servo = Servo(8)

sensor = Orientation_Sensor()

time_stamps = []
y_angle_values = []
servo_positions = []
angular_velocity_values = []
acceleration_values = []
rep_count = 0
start_time = time.time()

MAX_VELOCITY_THRESHOLD = 2.5  # If movement is too fast, restrict motion

def collect_user_bicep_curl_range():
    print("📢 Perform a few bicep curls to determine range of motion.")
    time.sleep(2)

    collected_y_angles = []

    for _ in range(10):
        angles = sensor.euler_angles()
        if angles is not None and len(angles) >= 3:
            collected_y_angles.append(angles[1])
        time.sleep(0.5)

    if len(collected_y_angles) < 5:
        print("⚠️ Calibration failed: Not enough movement data detected. Try again.")
        return None, None

    min_flexion = min(collected_y_angles)
    max_flexion = max(collected_y_angles)

    print(f"✅ Calibration Complete! Your Range: Min: {min_flexion:.2f}°, Max: {max_flexion:.2f}°")
    return min_flexion, max_flexion  

def adjust_servo_resistance(y_angle, angular_velocity, min_flexion, max_flexion):
    if min_flexion is None or max_flexion is None:
        return 0  

    if abs(angular_velocity) > MAX_VELOCITY_THRESHOLD:
        print("⚠️ TOO FAST! Restricting movement.")
        servo.mid()  
        return 0  

    resistance = (y_angle - min_flexion) / (max_flexion - min_flexion)
    resistance = max(0, min(1, resistance))  

    if resistance < 0.3:
        servo.min()
    elif resistance > 0.7:
        servo.max()
    else:
        servo.mid()

    return resistance

def update_graph():
    ax.clear()
    ax.plot(time_stamps, y_angle_values, label="Y-Angle (Posture)", color="blue")
    ax.plot(time_stamps, angular_velocity_values, label="Angular Velocity", color="green")
    ax.plot(time_stamps, acceleration_values, label="Acceleration", color="purple")
    ax.plot(time_stamps, servo_positions, label="Servo Position", color="red")

    ax.set_title("Posture & Motion Tracking")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(True)

    canvas.draw()

def tracking_loop(min_flexion, max_flexion):
    global rep_count

    prev_angular_velocity = 0  
    rep_in_progress = False  

    while True:
        angles = sensor.euler_angles()
        angular_velocity = sensor.gyroscope()  
        linear_accel = sensor.lin_acceleration()  

        if angles is None or len(angles) < 3 or angular_velocity is None or linear_accel is None:
            continue  

        y_angle = angles[1]
        angular_velocity_y = angular_velocity[1]
        acceleration_y = linear_accel[1]

        resistance = adjust_servo_resistance(y_angle, angular_velocity_y, min_flexion, max_flexion)

        if angular_velocity_y > 0.5 and not rep_in_progress:  
            rep_in_progress = True
        elif angular_velocity_y < 0.1 and rep_in_progress:
            rep_count += 1
            print(f"✅ Rep {rep_count} Completed!")
            rep_in_progress = False  

        elapsed_time = round(time.time() - start_time, 1)
        time_stamps.append(elapsed_time)
        y_angle_values.append(y_angle)
        servo_positions.append(resistance)
        angular_velocity_values.append(angular_velocity_y)
        acceleration_values.append(acceleration_y)

        if len(time_stamps) > 50:
            time_stamps.pop(0)
            y_angle_values.pop(0)
            servo_positions.pop(0)
            angular_velocity_values.pop(0)
            acceleration_values.pop(0)

        root.after(0, update_graph)
        root.after(0, lambda: posture_status.set(f"📏 Y-Angle: {y_angle:.2f}° | 🎛️ Servo: {resistance:.2f} | 🔄 Reps: {rep_count}"))

        time.sleep(0.5)

def start_tracking():
    min_flexion, max_flexion = collect_user_bicep_curl_range()
    if min_flexion is not None and max_flexion is not None:
        threading.Thread(target=tracking_loop, args=(min_flexion, max_flexion), daemon=True).start()
        root.after(0, lambda: posture_status.set("✅ Tracking Started!"))

root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("800x700")
root.config(bg="#282c34")

posture_status = tk.StringVar()
posture_status.set("Waiting...")

tk.Button(root, text="📝 Perform Calibration (Do 10 Reps)", command=start_tracking).pack(pady=5)

tracking_frame = tk.Frame(root, bg="#282c34")
tracking_frame.pack()

status_label = tk.Label(tracking_frame, textvariable=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=tracking_frame)
canvas.get_tk_widget().pack()

root.mainloop()
