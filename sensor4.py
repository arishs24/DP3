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
servo = Servo(8)  # Servo for adjustments
motor = Motor(forward=17, backward=27)  # Motor for resistance

# 🔹 Initialize Sensor
sensor = Orientation_Sensor()

# 🔹 Global Variables
calibrated_x, calibrated_y, calibrated_z = 0, 0, 0
is_tracking = False
user_strength = 0

# 🔹 Tkinter Main Thread Variable
posture_status = None


def rolling_average(x_list, y_list, z_list):
    """Computes rolling averages for X, Y, and Z angles."""
    if not x_list or not y_list or not z_list:
        return 0, 0, 0  # Prevent division errors
    return sum(x_list) / len(x_list), sum(y_list) / len(y_list), sum(z_list) / len(z_list)


def upload_pdf():
    """Allows user to upload a PDF (MRI report) and displays its text."""
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        pdf_label.config(text=f"📂 PDF Uploaded: {file_path.split('/')[-1]}")
        display_pdf_text(file_path)


def display_pdf_text(file_path):
    """Extracts and displays text from a PDF report."""
    try:
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])

        # Update text in the main thread
        root.after(0, lambda: pdf_text_box.config(state=tk.NORMAL))
        root.after(0, lambda: pdf_text_box.delete(1.0, tk.END))
        root.after(0, lambda: pdf_text_box.insert(tk.END, text))
        root.after(0, lambda: pdf_text_box.config(state=tk.DISABLED))

    except Exception as e:
        pdf_label.config(text=f"⚠️ Error: {e}", fg="red")


def calibrate_sensor():
    """Runs calibration in a separate thread to prevent UI freeze."""
    threading.Thread(target=run_calibration, daemon=True).start()


def run_calibration():
    """Captures sensor baseline and completes calibration."""
    global calibrated_x, calibrated_y, calibrated_z

    # Ensure UI updates happen on the main thread
    root.after(0, lambda: posture_status.set("📏 Calibrating... Hold still!"))
    time.sleep(1)  # Pause before starting

    x_list, y_list, z_list = [], [], []

    for _ in range(10):  # Collect stable baseline data
        angles = sensor.euler_angles()

        if angles is None or len(angles) < 3:
            continue  # Skip bad readings

        x_list.append(angles[0])
        y_list.append(angles[1])
        z_list.append(angles[2])
        time.sleep(0.5)

    if not x_list or not y_list or not z_list:
        root.after(0, lambda: posture_status.set("❌ Calibration Failed: Check Sensor!"))
        return

    # Compute stable average values as the reference
    calibrated_x = sum(x_list) / len(x_list)
    calibrated_y = sum(y_list) / len(y_list)
    calibrated_z = sum(z_list) / len(z_list)

    root.after(0, lambda: posture_status.set("✅ Calibration Complete! Starting Tracking..."))
    start_tracking()  # Auto-start tracking after calibration


def tracking_loop():
    """Tracks sensor values and adjusts motor resistance in real-time."""
    global is_tracking, user_strength

    while is_tracking:
        try:
            angles = sensor.euler_angles()
            if angles is None or len(angles) < 3:
                continue  # Skip bad readings

            adj_x = angles[0] - calibrated_x
            adj_y = angles[1] - calibrated_y
            adj_z = angles[2] - calibrated_z

            # Determine posture status
            if -10 < adj_y < 10:
                root.after(0, lambda: posture_status.set("✅ Good Posture"))
                resistance = user_strength / 50  # Scale between 0-1
            else:
                root.after(0, lambda: posture_status.set("🚨 Bad Posture - Adjusting Resistance!"))
                resistance = (user_strength / 50) * 1.2  # Increase resistance for correction

            # Apply resistance to motor
            motor.forward(resistance)

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

tk.Button(user_frame, text="✅ Submit & Calibrate", command=calibrate_sensor).pack(pady=10)

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
