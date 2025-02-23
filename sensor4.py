import time
import threading
import tkinter as tk
from tkinter import filedialog
from sensor_library import *  # Your existing sensor module
from gpiozero import Servo, LED, Motor

# 🔹 GPIO Setup
red_led = LED(6)  # Alert LED
servo = Servo(8)  # Servo motor on GPIO8
motor = Motor(forward=17, backward=27)  # Motor Control (L298N Driver)

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 User Data Variables
user_name = ""
injury_type = ""
severity_level = ""
mri_file_path = ""

# 🔹 Calibration Values
calibrated_x = 0
calibrated_y = 0
calibrated_z = 0

# Global Variables for UI
posture_status = "Waiting for user input..."
angles_text = "X: 0.00, Y: 0.00, Z: 0.00"
is_tracking = False

def upload_mri():
    """Opens file dialog to upload MRI and saves path"""
    global mri_file_path
    file_path = filedialog.askopenfilename(filetypes=[("MRI Scans", "*.jpg;*.png;*.dcm;*.jpeg")])
    if file_path:
        mri_file_path = file_path
        mri_label.config(text=f"📂 MRI Uploaded: {file_path.split('/')[-1]}")

def submit_user_info():
    """Saves user info and moves to calibration screen"""
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

def rolling_average(x_list, y_list, z_list):
    """Computes rolling averages for X, Y, and Z angles."""
    if not x_list or not y_list or not z_list:
        return 0, 0, 0  # Prevent division errors

    return sum(x_list) / len(x_list), sum(y_list) / len(y_list), sum(z_list) / len(z_list)

def update_ui():
    """Updates the GUI labels with the latest sensor data."""
    status_label.config(text=posture_status)
    angles_label.config(text=angles_text)
    root.update_idletasks()

def tracking_loop():
    """Runs posture tracking in a loop and updates the GUI."""
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

            check_limit_x = within_limit(avg_x, -50, 50)
            check_limit_y = within_limit_y(avg_y, -10, 10)
            check_limit_z = within_limit(avg_z, -30, 30)

            angles_text = f"X: {avg_x:.2f}, Y: {avg_y:.2f}, Z: {avg_z:.2f}"

            if not check_limit_x or not check_limit_z:
                posture_status = "🚨 Bad Posture! Adjust!"
                red_led.on()
            else:
                red_led.off()
                posture_status = "✅ Good Posture"

            if check_limit_y == 0:
                servo.mid()
                motor.stop()
            elif check_limit_y == 1:
                servo.max()
                motor.forward(0.7)
            elif check_limit_y == 2:
                servo.min()
                motor.backward(0.7)

            update_ui()

        except Exception as e:
            print(f"⚠️ Sensor Read Error: {e}")

        time.sleep(0.5)

def start_tracking():
    """Starts posture tracking in a separate thread."""
    global is_tracking
    is_tracking = True
    threading.Thread(target=tracking_loop, daemon=True).start()

def stop_tracking():
    """Stops posture tracking."""
    global is_tracking, posture_status
    is_tracking = False
    posture_status = "⏹ Stopped!"
    update_ui()

# 🔹 GUI SETUP (Tkinter)
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("450x400")
root.config(bg="#282c34")

### **USER INFO PAGE**
user_frame = tk.Frame(root, bg="#282c34")
user_frame.pack()

tk.Label(user_frame, text="📝 User Information", font=("Arial", 16, "bold"), fg="white", bg="#282c34").pack(pady=5)

tk.Label(user_frame, text="Name:", fg="white", bg="#282c34").pack()
name_entry = tk.Entry(user_frame)
name_entry.pack(pady=5)

tk.Label(user_frame, text="Injury Type:", fg="white", bg="#282c34").pack()
injury_entry = tk.Entry(user_frame)
injury_entry.pack(pady=5)

tk.Label(user_frame, text="Severity:", fg="white", bg="#282c34").pack()
severity_var = tk.StringVar()
severity_var.set("Mild")
severity_menu = tk.OptionMenu(user_frame, severity_var, "Mild", "Moderate", "Severe")
severity_menu.pack(pady=5)

mri_label = tk.Label(user_frame, text="No MRI Uploaded", fg="white", bg="#282c34")
mri_label.pack()
tk.Button(user_frame, text="📂 Upload MRI", command=upload_mri).pack(pady=5)

tk.Button(user_frame, text="✅ Submit & Start Calibration", command=submit_user_info).pack(pady=10)

### **CALIBRATION & TRACKING PAGE**
tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, text=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

angles_label = tk.Label(tracking_frame, text=angles_text, font=("Arial", 12), fg="white", bg="#282c34")
angles_label.pack(pady=5)

tk.Button(tracking_frame, text="▶ Start Tracking", command=start_tracking).pack(pady=5)
tk.Button(tracking_frame, text="⏹ Stop Tracking", command=stop_tracking).pack(pady=5)

root.mainloop()
