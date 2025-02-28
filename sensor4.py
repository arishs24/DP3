import time
import threading
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gpiozero import Servo, LED, Motor
from sensor_library import *  # Your existing sensor module

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo for adjustments
motor = Motor(forward=17, backward=27)  # Motor for resistance

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 Global Variables
is_tracking = False
user_max_flexion = None  # Max curl position
user_min_flexion = None  # Fully extended position
calibrated = False  # Ensure calibration is completed first

# 🔹 Data Storage for Graphing
time_stamps = []
y_angle_values = []
resistance_values = []
start_time = time.time()

def collect_user_bicep_curl_range():
    """
    Asks the user to perform a few reps to determine their **actual** range of motion.
    """
    global user_max_flexion, user_min_flexion, calibrated

    print("📢 Please perform a few bicep curls to determine your range of motion.")
    time.sleep(2)

    collected_y_angles = []

    for _ in range(10):  # Collect motion data for 10 reps
        angles = sensor.euler_angles()
        if angles is not None and len(angles) >= 3:
            collected_y_angles.append(angles[1])  # Y-axis (bicep flexion)
        time.sleep(0.5)

    if len(collected_y_angles) < 5:
        print("⚠️ Calibration failed: Not enough movement data detected. Try again.")
        return

    user_min_flexion = min(collected_y_angles)  # Fully extended
    user_max_flexion = max(collected_y_angles)  # Fully curled

    print(f"✅ Calibration Complete! Your Range: Min: {user_min_flexion:.2f}°, Max: {user_max_flexion:.2f}°")
    calibrated = True  # Allow tracking to start

def adjust_resistance(y_angle):
    """
    Adjusts resistance dynamically based on the user's **calibrated bicep curl range**.
    - If **too extended**, the motor **reduces resistance** and the servo **loosens**.
    - If **over-flexed**, the motor **increases resistance** and the servo **tightens**.
    """
    if not calibrated:
        return 0  # If calibration hasn't been completed, return no resistance

    # Normalize resistance based on user-defined min/max flexion
    resistance = (y_angle - user_min_flexion) / (user_max_flexion - user_min_flexion)
    resistance = max(0, min(1, resistance))  # Ensure resistance stays between 0 and 1

    # Apply resistance to motor
    motor.forward(resistance)

    # Servo tightening logic
    if resistance < 0.3:
        servo.min()  # Loosen band
    elif resistance > 0.7:
        servo.max()  # Tighten band
    else:
        servo.mid()  # Neutral position

    return resistance

def update_graph():
    """Updates real-time graph for posture & resistance."""
    ax.clear()
    ax.plot(time_stamps, y_angle_values, label="Y-Angle (Posture)", color="blue")
    ax.plot(time_stamps, resistance_values, label="Motor Resistance", color="red")

    ax.set_title("Posture & Resistance Tracking")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(True)

    canvas.draw()

def tracking_loop():
    """Tracks sensor values and adjusts motor resistance in real-time."""
    global is_tracking, time_stamps, y_angle_values, resistance_values

    while is_tracking:
        if not calibrated:
            continue  # Skip tracking until calibration is complete

        try:
            angles = sensor.euler_angles()
            if angles is None or len(angles) < 3:
                continue  # Skip bad readings

            y_angle = angles[1]  # Y-axis tracks bicep curl motion
            resistance = adjust_resistance(y_angle)

            # **Print tracking info**
            print(f"📏 Y-Angle: {y_angle:.2f}° | 🏋️ Resistance: {resistance:.2f} | Range: {user_min_flexion:.2f}° to {user_max_flexion:.2f}°")

            # **Graph Data Update**
            elapsed_time = round(time.time() - start_time, 1)
            time_stamps.append(elapsed_time)
            y_angle_values.append(y_angle)
            resistance_values.append(resistance)

            # Keep last 50 points
            if len(time_stamps) > 50:
                time_stamps.pop(0)
                y_angle_values.pop(0)
                resistance_values.pop(0)

            root.after(0, update_graph)  # **Fix: Runs graph update in main thread**
            root.after(0, lambda: posture_status.set(f"📏 Y-Angle: {y_angle:.2f}° | 🏋️ Resistance: {resistance:.2f}"))

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")

        time.sleep(0.5)

def stop_tracking():
    """Stops tracking and resets servo & motor."""
    global is_tracking
    is_tracking = False
    motor.stop()
    servo.mid()
    root.after(0, lambda: posture_status.set("🛑 Tracking Stopped"))

def start_tracking():
    """Starts tracking in a separate thread (Fixes UI thread issues)."""
    global is_tracking
    if not calibrated:
        print("⚠️ Cannot start tracking. Please perform calibration first!")
        return

    is_tracking = True
    threading.Thread(target=tracking_loop, daemon=True).start()
    root.after(0, lambda: posture_status.set("✅ Tracking Started!"))

# ✅ GUI SETUP
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("800x700")  # Increased size for graph & injury buttons
root.config(bg="#282c34")

posture_status = tk.StringVar()
posture_status.set("Waiting...")

# **Calibration Button**
tk.Button(root, text="📝 Perform Calibration (Do 10 Reps)", command=collect_user_bicep_curl_range).pack(pady=5)

# **Tracking Page**
tracking_frame = tk.Frame(root, bg="#282c34")
tracking_frame.pack()

status_label = tk.Label(tracking_frame, textvariable=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

tk.Button(tracking_frame, text="▶ Start Tracking", command=start_tracking).pack(pady=5)
tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

# **Graph Setup**
fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=tracking_frame)
canvas.get_tk_widget().pack()

root.mainloop()
