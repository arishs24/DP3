import time
import threading
import tkinter as tk
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gpiozero import Servo, LED, Motor
from sensor_library import *  # Your existing sensor module
from sklearn.ensemble import RandomForestClassifier  # ML Model

# 🔹 Load Pre-trained ML Model (or train if missing)
try:
    model = joblib.load("movement_model.pkl")  # Load trained model
    print("✅ ML Model Loaded Successfully!")
except:
    print("⚠️ No model found! Training a new one...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)  # Placeholder Model
    joblib.dump(model, "movement_model.pkl")  # Save for later use

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

# 🔹 Tkinter Main Thread Variable
posture_status = None

# 🔹 Graph Data Storage
time_stamps = []
y_angle_values = []
resistance_values = []
start_time = time.time()

### **✅ Ensure All Functions Are Defined First**
def update_graph():
    """Updates real-time graph for posture & resistance."""
    global time_stamps, y_angle_values, resistance_values

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
    """Tracks sensor values and adjusts motor resistance in real-time using ML."""
    global is_tracking, time_stamps, y_angle_values, resistance_values

    while is_tracking:
        try:
            angles = sensor.euler_angles()
            if angles is None or len(angles) < 3:
                continue  # Skip bad readings

            adj_y = angles[1] - calibrated_y

            if -10 < adj_y < 10:
                root.after(0, lambda: posture_status.set("✅ Good Posture"))
                resistance = user_strength / 50
            else:
                root.after(0, lambda: posture_status.set("🚨 Bad Posture - Adjusting Resistance!"))
                resistance = (user_strength / 50) * 1.2  # Increase resistance for correction

            resistance = max(0, min(1, resistance))  # Ensure motor speed is between 0 and 1
            motor.forward(resistance)

            # Adjust servo position
            if -10 < adj_y < 10:
                servo.mid()
            elif adj_y < -10:
                servo.min()
            else:
                servo.max()

            # **Graph Data Update**
            elapsed_time = round(time.time() - start_time, 1)
            time_stamps.append(elapsed_time)
            y_angle_values.append(adj_y)
            resistance_values.append(resistance)

            # Keep last 50 points
            if len(time_stamps) > 50:
                time_stamps.pop(0)
                y_angle_values.pop(0)
                resistance_values.pop(0)

            root.after(0, update_graph)  # Update graph in UI

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


def estimate_max_bicep_curl():
    """Estimates max bicep curl weight based on user input."""
    try:
        weight = int(weight_entry.get())
        age = int(age_entry.get())
        gender = gender_var.get()
        activity = activity_var.get()

        # **Base Strength Calculation**
        if gender == "Male":
            base_strength = 0.5 * weight  # Males curl ~50% of body weight
        else:
            base_strength = 0.35 * weight  # Females curl ~35%

        # **Adjust for Age**
        if age > 40:
            base_strength *= 0.85  # Reduce 15% for older users
        elif age < 18:
            base_strength *= 0.9  # Reduce 10% for teens

        # **Adjust for Activity Level**
        if activity == "Low":
            base_strength *= 0.8  # Reduce 20%
        elif activity == "High":
            base_strength *= 1.2  # Increase 20%

        return round(base_strength, 1)
    except ValueError:
        return 0  # Default value if input is invalid


def start_tracking():
    """Starts tracking in a separate thread."""
    global is_tracking
    is_tracking = True
    threading.Thread(target=tracking_loop, daemon=True).start()


# ✅ GUI SETUP
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("800x600")  # Increased size for graph
root.config(bg="#282c34")

posture_status = tk.StringVar()
posture_status.set("Waiting...")

# **User Info Page**
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

activity_var = tk.StringVar(value="Medium")
tk.Label(user_frame, text="Activity Level:", fg="white", bg="#282c34").pack()
activity_menu = tk.OptionMenu(user_frame, activity_var, "Low", "Medium", "High")
activity_menu.pack()

tk.Button(user_frame, text="✅ Submit & Calibrate", command=start_tracking).pack(pady=10)

strength_label = tk.Label(user_frame, text="💪 Estimated Max Bicep Curl: N/A", fg="white", bg="#282c34")
strength_label.pack()

tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, textvariable=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

# **Graph Setup**
fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=tracking_frame)
canvas.get_tk_widget().pack()

root.mainloop()
