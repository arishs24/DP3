import time
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
import fitz  # PyMuPDF for PDF handling
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from gpiozero import Servo, LED, Motor
from sensor_library import *  # Your existing sensor module

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo motor for adjustments
motor = Motor(forward=17, backward=27)  # Main motor for resistance

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 Global Variables
calibrated_x, calibrated_y, calibrated_z = 0, 0, 0
is_tracking = False
user_strength = 0

# Live Graph Data
x_vals, y_vals = [], []  # Stores time & Y angle values for live graph


def rolling_average(x_list, y_list, z_list):
    """Computes rolling averages for X, Y, and Z angles."""
    if not x_list or not y_list or not z_list:
        return 0, 0, 0  # Prevent division errors
    return sum(x_list) / len(x_list), sum(y_list) / len(y_list), sum(z_list) / len(z_list)


def calibrate_sensor():
    """Calibrates the sensor by capturing a stable baseline."""
    global calibrated_x, calibrated_y, calibrated_z

    posture_status.set("📏 Calibrating... Hold still!")

    x_list, y_list, z_list = [], [], []

    for _ in range(10):  # Collect stable baseline data
        angles = sensor.euler_angles()
        x_list.append(angles[0])
        y_list.append(angles[1])
        z_list.append(angles[2])
        time.sleep(0.5)

    # Compute stable average values as the reference
    calibrated_x = sum(x_list) / len(x_list)
    calibrated_y = sum(y_list) / len(y_list)
    calibrated_z = sum(z_list) / len(z_list)

    posture_status.set("✅ Calibration Complete! Starting Tracking...")


def estimate_max_bicep_curl():
    """Estimates max bicep curl weight based on user input."""
    try:
        weight = int(weight_entry.get())
        age = int(age_entry.get())
        gender = gender_var.get()
        activity_level = activity_var.get()

        if gender == "Male":
            base_strength = 0.5 * weight  # Male average: 50% of body weight
        else:
            base_strength = 0.35 * weight  # Female average: 35%

        # Adjust for age
        if age > 40:
            base_strength *= 0.85  # Reduce 15% for older users
        elif age < 18:
            base_strength *= 0.9  # Reduce 10% for teens

        # Adjust for activity level
        if activity_level == "Low":
            base_strength *= 0.8  # Reduce 20%
        elif activity_level == "High":
            base_strength *= 1.2  # Increase 20%

        return round(base_strength, 1)
    except ValueError:
        return 0  # Default value if invalid input


def tracking_loop():
    """Tracks sensor values and adjusts motor resistance in real-time."""
    global is_tracking, user_strength

    user_strength = estimate_max_bicep_curl()
    if user_strength == 0:
        return  # Don't start tracking if strength estimation failed

    x_list, y_list, z_list = [], [], []

    while is_tracking:
        try:
            angles = sensor.euler_angles()
            adj_x = angles[0] - calibrated_x
            adj_y = angles[1] - calibrated_y
            adj_z = angles[2] - calibrated_z

            x_list.append(adj_x)
            y_list.append(adj_y)
            z_list.append(adj_z)

            if len(x_list) > 10:
                x_list.pop(0)
                y_list.pop(0)
                z_list.pop(0)

            avg_x, avg_y, avg_z = rolling_average(x_list, y_list, z_list)

            x_vals.append(time.time())  # Time for graph
            y_vals.append(avg_y)

            # Determine posture status
            if -10 < avg_y < 10:
                posture_status.set("✅ Good Posture")
                resistance = user_strength / 50  # Scale between 0-1
            else:
                posture_status.set("🚨 Bad Posture - Adjusting Resistance!")
                resistance = (user_strength / 50) * 1.2  # Increase resistance for correction

            # Apply resistance to motor
            motor.forward(resistance)
            update_ui()

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")

        time.sleep(0.5)


def start_tracking():
    """Starts tracking in a separate thread."""
    global is_tracking
    is_tracking = True
    threading.Thread(target=tracking_loop, daemon=True).start()


def stop_tracking():
    """Stops tracking."""
    global is_tracking
    is_tracking = False
    motor.stop()


def update_ui():
    """Updates the GUI labels with the latest sensor data."""
    root.update_idletasks()


# GUI Setup
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("600x500")
root.config(bg="#282c34")

posture_status = tk.StringVar()
posture_status.set("Waiting...")

# Patient Info Page
user_frame = tk.Frame(root, bg="#282c34")
user_frame.pack()

tk.Label(user_frame, text="📝 Patient Information", font=("Arial", 16), fg="white", bg="#282c34").pack()

tk.Label(user_frame, text="Name:", fg="white", bg="#282c34").pack()
name_entry = tk.Entry(user_frame)
name_entry.pack()

tk.Label(user_frame, text="Age:", fg="white", bg="#282c34").pack()
age_entry = tk.Entry(user_frame)
age_entry.pack()

tk.Label(user_frame, text="Weight (lbs):", fg="white", bg="#282c34").pack()
weight_entry = tk.Entry(user_frame)
weight_entry.pack()

tk.Label(user_frame, text="Gender:", fg="white", bg="#282c34").pack()
gender_var = tk.StringVar(value="Male")
gender_menu = tk.OptionMenu(user_frame, gender_var, "Male", "Female")
gender_menu.pack()

tk.Label(user_frame, text="Activity Level:", fg="white", bg="#282c34").pack()
activity_var = tk.StringVar(value="Medium")
activity_menu = tk.OptionMenu(user_frame, activity_var, "Low", "Medium", "High")
activity_menu.pack()

tk.Button(user_frame, text="✅ Submit & Calibrate", command=lambda: [calibrate_sensor(), start_tracking()]).pack(pady=10)
strength_label = tk.Label(user_frame, text="💪 Strength: N/A", fg="white", bg="#282c34")
strength_label.pack()

# PDF Upload (MRI Report)
pdf_label = tk.Label(user_frame, text="No PDF Uploaded", fg="white", bg="#282c34")
pdf_label.pack()
tk.Button(user_frame, text="📂 Upload MRI Report (PDF)", command=upload_pdf).pack()

pdf_text_box = scrolledtext.ScrolledText(user_frame, wrap=tk.WORD, width=60, height=6, state=tk.DISABLED)
pdf_text_box.pack(pady=5)

# Tracking Page
tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, textvariable=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

root.mainloop()
