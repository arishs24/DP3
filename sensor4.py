import time
import threading
import tkinter as tk
from gpiozero import Servo, LED, Motor
from sensor_library import *  # Your existing sensor module
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo motor
motor = Motor(forward=17, backward=27)  # Motor for resistance adjustment

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 User Data Variables
user_name = ""
user_age = 0
user_weight = 0
user_gender = ""
injury_type = ""
severity_level = ""

# Live Graph Data
x_vals, y_vals = [], []  # Stores time & Y angle values for live graph


def rolling_average(x_list, y_list, z_list):
    """Computes rolling averages for X, Y, and Z angles."""
    if not x_list or not y_list or not z_list:
        return 0, 0, 0  # Prevent division errors
    return sum(x_list) / len(x_list), sum(y_list) / len(y_list), sum(z_list) / len(z_list)


def estimate_max_bicep_curl():
    """Estimates max bicep curl weight based on user age, weight, and gender."""
    global user_age, user_weight, user_gender
    try:
        age = int(user_age)
        weight = int(user_weight)

        if user_gender == "Male":
            base_strength = 0.5 * weight  # Males generally curl ~50% of body weight
        else:
            base_strength = 0.35 * weight  # Females curl ~35% of body weight

        # Adjust for age
        if age > 40:
            base_strength *= 0.85  # Reduce by 15% for older users
        elif age < 18:
            base_strength *= 0.9  # Reduce by 10% for younger users

        return round(base_strength, 1)

    except ValueError:
        return "Invalid Input"


def submit_user_info():
    """Saves user info and moves to calibration screen."""
    global user_name, user_age, user_weight, user_gender, injury_type, severity_level
    user_name = name_entry.get()
    user_age = age_entry.get()
    user_weight = weight_entry.get()
    user_gender = gender_var.get()
    injury_type = injury_entry.get()
    severity_level = severity_var.get()

    if not user_name or not user_age or not user_weight or not user_gender or not injury_type or not severity_level:
        status_label.config(text="⚠️ Please complete all fields!", fg="red")
        return

    # Estimate strength
    estimated_strength = estimate_max_bicep_curl()
    strength_label.config(text=f"💪 Estimated Max Bicep Curl: {estimated_strength} lbs")

    status_label.config(text=f"✅ User {user_name} saved! Starting Calibration...", fg="green")

    # Switch to Calibration Screen
    user_frame.pack_forget()
    tracking_frame.pack()


def calibrate_sensor():
    """Captures initial sensor values as the neutral reference."""
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

    calibrated_x = sum(x_list) / len(x_list)
    calibrated_y = sum(y_list) / len(y_list)
    calibrated_z = sum(z_list) / len(z_list)

    posture_status = "✅ Calibration Complete! Starting..."
    update_ui()
    time.sleep(1)


def update_ui():
    """Updates the GUI labels with the latest sensor data."""
    status_label.config(text=posture_status)
    angles_label.config(text=angles_text)
    root.update_idletasks()


def tracking_loop():
    """Runs posture tracking & adjusts motor resistance dynamically."""
    global posture_status, angles_text, is_tracking
    x_list, y_list, z_list = [], [], []

    estimated_strength = estimate_max_bicep_curl()
    if isinstance(estimated_strength, str):
        return  # Don't start tracking if strength estimation failed

    while is_tracking:
        try:
            angles = sensor.euler_angles()
            raw_x, raw_y, raw_z = angles

            adj_x = raw_x - calibrated_x
            adj_y = raw_y - calibrated_y
            adj_z = raw_z - calibrated_z

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

            angles_text = f"X: {avg_x:.2f}, Y: {avg_y:.2f}, Z: {avg_z:.2f}"
            posture_status = "✅ Good Posture" if -10 < avg_y < 10 else "🚨 Bad Posture"

            # Adjust motor resistance based on estimated strength
            resistance = estimated_strength / 50  # Scale between 0 and 1
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


# GUI Setup
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("500x400")
root.config(bg="#282c34")

# User Info Page
user_frame = tk.Frame(root, bg="#282c34")
user_frame.pack()

tk.Label(user_frame, text="📝 User Information", font=("Arial", 16), fg="white", bg="#282c34").pack()

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
gender_var = tk.StringVar()
gender_var.set("Male")
gender_menu = tk.OptionMenu(user_frame, gender_var, "Male", "Female")
gender_menu.pack()

tk.Label(user_frame, text="Injury Type:", fg="white", bg="#282c34").pack()
injury_entry = tk.Entry(user_frame)
injury_entry.pack()

tk.Label(user_frame, text="Severity:", fg="white", bg="#282c34").pack()
severity_var = tk.StringVar()
severity_var.set("Mild")
severity_menu = tk.OptionMenu(user_frame, severity_var, "Mild", "Moderate", "Severe")
severity_menu.pack()

tk.Button(user_frame, text="✅ Submit & Start Calibration", command=submit_user_info).pack(pady=10)
strength_label = tk.Label(user_frame, text="", fg="white", bg="#282c34")
strength_label.pack()

# Tracking Page
tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, text="Waiting...", font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

root.mainloop()
