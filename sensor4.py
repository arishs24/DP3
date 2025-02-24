import time
import threading
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from gpiozero import Servo, LED, Motor
from sensor_library import *  # Your existing sensor module

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo for adjustments
motor = Motor(forward=17, backward=27)  # Motor for resistance

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 Global Variables
calibrated_x, calibrated_y, calibrated_z = 0, 0, 0
is_tracking = False
user_strength = 0
user_name, user_age, user_weight, user_gender, activity_level = "", 0, 0, "", ""

x_data, y_data, z_data, time_data = [], [], [], []

# **📊 Graph Setup**
fig, ax = plt.subplots()
ax.set_ylim(-180, 180)  # Adjust based on sensor range
ax.set_xlim(0, 50)  # Show last 50 readings
ax.set_xlabel("Time")
ax.set_ylabel("Angle (degrees)")
ax.set_title("Real-Time Posture Tracking")
ax.grid()

line_x, = ax.plot([], [], label="X-axis", color="red")
line_y, = ax.plot([], [], label="Y-axis", color="blue")
line_z, = ax.plot([], [], label="Z-axis", color="green")
ax.legend()


def update_graph(frame):
    """Live updates the graph with new sensor data"""
    if not is_tracking:
        return line_x, line_y, line_z  # Stop updating if not tracking

    angles = sensor.euler_angles()
    if angles is None or len(angles) < 3:
        return line_x, line_y, line_z  # Skip bad readings

    time_data.append(len(time_data))
    x_data.append(angles[0] - calibrated_x)
    y_data.append(angles[1] - calibrated_y)
    z_data.append(angles[2] - calibrated_z)

    # Keep only last 50 readings for smooth graphing
    if len(time_data) > 50:
        time_data.pop(0)
        x_data.pop(0)
        y_data.pop(0)
        z_data.pop(0)

    line_x.set_data(time_data, x_data)
    line_y.set_data(time_data, y_data)
    line_z.set_data(time_data, z_data)

    return line_x, line_y, line_z


def show_graph():
    """Opens the real-time graph in a new window"""
    ani = animation.FuncAnimation(fig, update_graph, interval=500)
    plt.show()


def start_tracking():
    """Starts tracking in a separate thread and launches graph"""
    global is_tracking
    is_tracking = True
    threading.Thread(target=tracking_loop, daemon=True).start()
    threading.Thread(target=show_graph, daemon=True).start()  # Open graph


def stop_tracking():
    """Stops tracking"""
    global is_tracking
    is_tracking = False
    motor.stop()
    servo.mid()


def tracking_loop():
    """Tracks sensor values and adjusts motor resistance in real-time."""
    global is_tracking

    while is_tracking:
        try:
            angles = sensor.euler_angles()
            if angles is None or len(angles) < 3:
                continue  # Skip bad readings

            adj_y = angles[1] - calibrated_y

            if -10 < adj_y < 10:
                root.after(0, lambda: posture_status.set("✅ Good Posture"))
                resistance = 0.5  # Normal resistance
            else:
                root.after(0, lambda: posture_status.set("🚨 Bad Posture - Adjusting Resistance!"))
                resistance = 1.0  # Increase resistance

            resistance = max(0, min(1, resistance))  # Ensure motor speed is between 0 and 1
            motor.forward(resistance)

            # Adjust servo position
            if -10 < adj_y < 10:
                servo.mid()
            elif adj_y < -10:
                servo.min()
            else:
                servo.max()

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")

        time.sleep(0.5)


### ✅ **Patient Info Submission & UI**
def estimate_max_bicep_curl():
    """Estimates max bicep curl weight based on user input."""
    try:
        weight = int(weight_entry.get())
        age = int(age_entry.get())
        gender = gender_var.get()
        activity = activity_var.get()

        if gender == "Male":
            base_strength = 0.5 * weight  
        else:
            base_strength = 0.35 * weight  

        if age > 40:
            base_strength *= 0.85  
        elif age < 18:
            base_strength *= 0.9  

        if activity == "Low":
            base_strength *= 0.8  
        elif activity == "High":
            base_strength *= 1.2  

        return round(base_strength, 1)
    except ValueError:
        return 0  


def submit_user_info():
    """Saves user info and starts calibration."""
    global user_name, user_age, user_weight, user_gender, activity_level, user_strength

    user_name = name_entry.get()
    user_age = age_entry.get()
    user_weight = weight_entry.get()
    user_gender = gender_var.get()
    activity_level = activity_var.get()

    if not all([user_name, user_age, user_weight, user_gender, activity_level]):
        status_label.config(text="⚠️ Please fill out all fields!", fg="red")
        return

    user_strength = estimate_max_bicep_curl()
    if user_strength == 0:
        status_label.config(text="⚠️ Invalid Input!", fg="red")
        return

    strength_label.config(text=f"💪 Estimated Max Bicep Curl: {user_strength} lbs")

    user_frame.pack_forget()
    tracking_frame.pack()
    threading.Thread(target=calibrate_sensor, daemon=True).start()


def calibrate_sensor():
    """Captures sensor baseline and completes calibration."""
    global calibrated_x, calibrated_y, calibrated_z

    root.after(0, lambda: posture_status.set("📏 Calibrating... Hold still!"))
    time.sleep(1)  

    x_list, y_list, z_list = [], [], []

    for _ in range(10):  
        angles = sensor.euler_angles()

        if angles is None or len(angles) < 3:
            continue  

        x_list.append(angles[0])
        y_list.append(angles[1])
        z_list.append(angles[2])
        time.sleep(0.5)

    if not x_list or not y_list or not z_list:
        root.after(0, lambda: posture_status.set("❌ Calibration Failed: Check Sensor!"))
        return

    calibrated_x = sum(x_list) / len(x_list)
    calibrated_y = sum(y_list) / len(y_list)
    calibrated_z = sum(z_list) / len(z_list)

    root.after(0, lambda: posture_status.set("✅ Calibration Complete! Starting Tracking..."))
    start_tracking()


# ✅ **GUI Setup**
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("600x500")
root.config(bg="#282c34")

posture_status = tk.StringVar()
posture_status.set("Waiting...")

user_frame = tk.Frame(root, bg="#282c34")
user_frame.pack()

activity_var = tk.StringVar(value="Medium")  # **🔥 FIXED - activity_var is now correctly defined!**
tk.Label(user_frame, text="Activity Level:", fg="white", bg="#282c34").pack()
activity_menu = tk.OptionMenu(user_frame, activity_var, "Low", "Medium", "High")
activity_menu.pack()

tk.Button(user_frame, text="✅ Submit & Calibrate", command=submit_user_info).pack(pady=10)

tracking_frame = tk.Frame(root, bg="#282c34")

tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

root.mainloop()
