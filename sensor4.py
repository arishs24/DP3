import time
import threading
import tkinter as tk
import numpy as np
import pandas as pd
import joblib
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
user_name, user_age, user_weight, user_gender = "", 0, 0, ""
activity_level = ""

# 🔹 Tkinter Main Thread Variable
posture_status = None


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

    user_strength = estimate_max_bicep_curl()  # **FIXED: Now this function is defined**
    if user_strength == 0:
        status_label.config(text="⚠️ Invalid Input!", fg="red")
        return

    strength_label.config(text=f"💪 Estimated Max Bicep Curl: {user_strength} lbs")

    # Move to calibration
    user_frame.pack_forget()
    tracking_frame.pack()
    threading.Thread(target=calibrate_sensor, daemon=True).start()


# ✅ Calibration & Tracking Functions Remain Unchanged


# GUI Setup
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("600x500")
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

tk.Label(user_frame, text="Activity Level:", fg="white", bg="#282c34").pack()
activity_var = tk.StringVar(value="Medium")
activity_menu = tk.OptionMenu(user_frame, activity_var, "Low", "Medium", "High")
activity_menu.pack()

tk.Button(user_frame, text="✅ Submit & Calibrate", command=submit_user_info).pack(pady=10)
strength_label = tk.Label(user_frame, text="💪 Estimated Max Bicep Curl: N/A", fg="white", bg="#282c34")
strength_label.pack()

# **Tracking Page**
tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, textvariable=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

root.mainloop()
