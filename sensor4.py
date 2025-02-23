import time
import threading
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PIL import Image, ImageTk
from pydicom import dcmread
from sensor_library import *  # Your existing sensor module
from gpiozero import Servo, LED, Motor

# 🔹 GPIO Setup
red_led = LED(6)
servo = Servo(8)
motor = Motor(forward=17, backward=27)

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 User Data Variables
user_name = ""
injury_type = ""
severity_level = ""
mri_file_path = ""

# Live Graph Data
x_vals, y_vals = [], []  # Stores time & Y angle values for live graph


def rolling_average(x_list, y_list, z_list):
    """Computes rolling averages for X, Y, and Z angles."""
    if not x_list or not y_list or not z_list:
        return 0, 0, 0
    return sum(x_list) / len(x_list), sum(y_list) / len(y_list), sum(z_list) / len(z_list)


def upload_mri():
    """Opens file dialog to upload MRI and displays it."""
    global mri_file_path
    file_path = filedialog.askopenfilename(filetypes=[("MRI Scans", "*.jpg;*.png;*.dcm;*.jpeg")])
    if file_path:
        mri_file_path = file_path
        mri_label.config(text=f"📂 MRI Uploaded: {file_path.split('/')[-1]}")
        display_mri(file_path)


def display_mri(file_path):
    """Loads and displays MRI image in GUI."""
    global mri_image
    try:
        if file_path.endswith(".dcm"):
            dicom_data = dcmread(file_path)
            img = dicom_data.pixel_array
        else:
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

        img = cv2.resize(img, (150, 150))  # Resize for display

        # Convert to Tkinter Image
        img = Image.fromarray(img)
        img = ImageTk.PhotoImage(img)
        mri_canvas.create_image(0, 0, anchor=tk.NW, image=img)
        mri_canvas.image = img  # Prevent garbage collection

    except Exception as e:
        mri_label.config(text=f"⚠️ Error: {e}", fg="red")


def submit_user_info():
    """Saves user info and moves to calibration screen."""
    global user_name, injury_type, severity_level
    user_name = name_entry.get()
    injury_type = injury_entry.get()
    severity_level = severity_var.get()

    if not user_name or not injury_type or not severity_level:
        status_label.config(text="⚠️ Please complete all fields!", fg="red")
        return

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
    """Runs posture tracking & updates graph."""
    global posture_status, angles_text, is_tracking
    x_list, y_list, z_list = [], [], []

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


def update_graph(frame):
    """Updates the graph in real-time."""
    ax.clear()
    ax.plot(x_vals, y_vals, label="Y Angle (Posture)")
    ax.set_title("Real-Time Posture Tracking")
    ax.set_xlabel("Time")
    ax.set_ylabel("Posture Angle (Y)")
    ax.legend()


# GUI Setup
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("600x500")
root.config(bg="#282c34")

# User Page
user_frame = tk.Frame(root, bg="#282c34")
user_frame.pack()

tk.Label(user_frame, text="📝 User Information", font=("Arial", 16), fg="white", bg="#282c34").pack()

# MRI Upload
mri_canvas = tk.Canvas(user_frame, width=150, height=150)
mri_canvas.pack()
mri_label = tk.Label(user_frame, text="No MRI Uploaded", fg="white", bg="#282c34")
mri_label.pack()
tk.Button(user_frame, text="📂 Upload MRI", command=upload_mri).pack()

# Tracking Page
tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, text="Waiting...", font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

angles_label = tk.Label(tracking_frame, text="X: 0.00, Y: 0.00, Z: 0.00", font=("Arial", 12), fg="white", bg="#282c34")
angles_label.pack(pady=5)

tk.Button(tracking_frame, text="▶ Start Tracking", command=start_tracking).pack(pady=5)
tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

# Live Graph
fig, ax = plt.subplots()
ani = FuncAnimation(fig, update_graph, interval=1000)
plt.show(block=False)

root.mainloop()
