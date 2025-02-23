import time
import threading
import tkinter as tk
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

# Global Variables for UI
posture_status = "Calibrating..."
angles_text = "X: 0.00, Y: 0.00, Z: 0.00"
is_tracking = False

def calibrate_sensor():
    """
    Captures initial sensor values as the "neutral" posture reference.
    """
    global calibrated_x, calibrated_y, calibrated_z, posture_status
    
    posture_status = "📏 Calibrating... Hold still!"
    update_ui()

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

    posture_status = "✅ Calibration Complete! Starting..."
    update_ui()
    time.sleep(1)

def update_ui():
    """
    Updates the GUI labels with the latest sensor data.
    """
    status_label.config(text=posture_status)
    angles_label.config(text=angles_text)
    root.update_idletasks()

def tracking_loop():
    """
    Runs posture tracking in a loop and updates the GUI.
    """
    global posture_status, angles_text, is_tracking
    x_list, y_list, z_list = [], [], []

    while is_tracking:
        try:
            # 1️⃣ Read Sensor Data
            angles = sensor.euler_angles()
            raw_x, raw_y, raw_z = angles  

            # Apply calibration (adjust relative to neutral position)
            adj_x = raw_x - calibrated_x
            adj_y = raw_y - calibrated_y
            adj_z = raw_z - calibrated_z

            # Store values for rolling average
            x_list.append(adj_x)
            y_list.append(adj_y)
            z_list.append(adj_z)

            if len(x_list) > 10:
                x_list.pop(0)
                y_list.pop(0)
                z_list.pop(0)

            # Compute rolling average
            avg_x, avg_y, avg_z = rolling_average(x_list, y_list, z_list)

            # Check Limits for Correct Posture
            check_limit_x = within_limit(avg_x, -50, 50)
            check_limit_y = within_limit_y(avg_y, -10, 10)
            check_limit_z = within_limit(avg_z, -30, 30)

            # Update UI Text
            angles_text = f"X: {avg_x:.2f}, Y: {avg_y:.2f}, Z: {avg_z:.2f}"

            # LED Alert for Incorrect Form
            if not check_limit_x or not check_limit_z:
                posture_status = "🚨 Bad Posture! Adjust!"
                red_led.on()
            else:
                red_led.off()
                posture_status = "✅ Good Posture"

            # Servo & Motor Control for Resistance Adjustment
            if check_limit_y == 0:
                servo.mid()
                motor.stop()
            elif check_limit_y == 1:
                servo.max()
                motor.forward(0.7)
            elif check_limit_y == 2:
                servo.min()
                motor.backward(0.7)

            # Update the UI
            update_ui()

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")

        time.sleep(0.5)

def start_tracking():
    """
    Starts posture tracking in a separate thread.
    """
    global is_tracking
    is_tracking = True
    threading.Thread(target=tracking_loop, daemon=True).start()

def stop_tracking():
    """
    Stops posture tracking.
    """
    global is_tracking, posture_status
    is_tracking = False
    posture_status = "⏹ Stopped!"
    update_ui()

# 🔹 GUI SETUP (Tkinter)
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("400x300")
root.config(bg="#282c34")

# Title Label
title_label = tk.Label(root, text="💪 Rehab Band Tracker", font=("Arial", 16, "bold"), fg="white", bg="#282c34")
title_label.pack(pady=10)

# Status Label
status_label = tk.Label(root, text=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

# Angles Label
angles_label = tk.Label(root, text=angles_text, font=("Arial", 12), fg="white", bg="#282c34")
angles_label.pack(pady=5)

# Buttons
btn_calibrate = tk.Button(root, text="🔄 Calibrate", font=("Arial", 12), command=calibrate_sensor)
btn_calibrate.pack(pady=5)

btn_start = tk.Button(root, text="▶ Start Tracking", font=("Arial", 12), command=start_tracking)
btn_start.pack(pady=5)

btn_stop = tk.Button(root, text="⏹ Stop Tracking", font=("Arial", 12), command=stop_tracking)
btn_stop.pack(pady=5)

# Start Tkinter Main Loop
root.mainloop()
