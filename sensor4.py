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
activity_level = ""
rehab_goal = ""
pdf_file_path = ""

# Live Graph Data
x_vals, y_vals = [], []  # Stores time & Y angle values for live graph


def rolling_average(x_list, y_list, z_list):
    """Computes rolling averages for X, Y, and Z angles."""
    if not x_list or not y_list or not z_list:
        return 0, 0, 0  # Prevent division errors
    return sum(x_list) / len(x_list), sum(y_list) / len(y_list), sum(z_list) / len(z_list)


def upload_pdf():
    """Allows user to upload a PDF (MRI report) and displays its text."""
    global pdf_file_path
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        pdf_file_path = file_path
        pdf_label.config(text=f"📂 PDF Uploaded: {file_path.split('/')[-1]}")
        display_pdf_text(file_path)


def display_pdf_text(file_path):
    """Extracts and displays text from a PDF report."""
    try:
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])

        # Show PDF text inside the UI
        pdf_text_box.config(state=tk.NORMAL)
        pdf_text_box.delete(1.0, tk.END)  # Clear previous text
        pdf_text_box.insert(tk.END, text)
        pdf_text_box.config(state=tk.DISABLED)  # Make read-only

    except Exception as e:
        pdf_label.config(text=f"⚠️ Error: {e}", fg="red")


def estimate_max_bicep_curl():
    """Estimates max bicep curl weight based on user age, weight, gender, and activity level."""
    global user_age, user_weight, user_gender, activity_level
    try:
        age = int(user_age)
        weight = int(user_weight)

        # Base strength estimate
        if user_gender == "Male":
            base_strength = 0.5 * weight  # Males generally curl ~50% of body weight
        else:
            base_strength = 0.35 * weight  # Females curl ~35% of body weight

        # Adjust for age
        if age > 40:
            base_strength *= 0.85  # Reduce by 15% for older users
        elif age < 18:
            base_strength *= 0.9  # Reduce by 10% for younger users

        # Adjust for activity level
        if activity_level == "Low":
            base_strength *= 0.8  # Reduce by 20% for inactive users
        elif activity_level == "High":
            base_strength *= 1.2  # Increase by 20% for very active users

        return round(base_strength, 1)

    except ValueError:
        return "Invalid Input"


def submit_user_info():
    """Saves user info and moves to calibration screen."""
    global user_name, user_age, user_weight, user_gender, injury_type, severity_level, activity_level, rehab_goal
    user_name = name_entry.get()
    user_age = age_entry.get()
    user_weight = weight_entry.get()
    user_gender = gender_var.get()
    injury_type = injury_entry.get()
    severity_level = severity_var.get()
    activity_level = activity_var.get()
    rehab_goal = rehab_goal_entry.get()

    if not all([user_name, user_age, user_weight, user_gender, injury_type, severity_level, activity_level, rehab_goal]):
        status_label.config(text="⚠️ Please complete all fields!", fg="red")
        return

    # Estimate strength
    estimated_strength = estimate_max_bicep_curl()
    strength_label.config(text=f"💪 Estimated Max Bicep Curl: {estimated_strength} lbs")

    status_label.config(text=f"✅ User {user_name} saved! Starting Calibration...", fg="green")

    # Switch to Calibration Screen
    user_frame.pack_forget()
    tracking_frame.pack()


# GUI Setup
root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("600x500")
root.config(bg="#282c34")

# User Info Page
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

tk.Label(user_frame, text="Activity Level:", fg="white", bg="#282c34").pack()
activity_var = tk.StringVar()
activity_var.set("Medium")
activity_menu = tk.OptionMenu(user_frame, activity_var, "Low", "Medium", "High")
activity_menu.pack()

tk.Label(user_frame, text="Rehab Goal:", fg="white", bg="#282c34").pack()
rehab_goal_entry = tk.Entry(user_frame)
rehab_goal_entry.pack()

tk.Button(user_frame, text="✅ Submit & Start Calibration", command=submit_user_info).pack(pady=10)
strength_label = tk.Label(user_frame, text="", fg="white", bg="#282c34")
strength_label.pack()

# PDF Upload (MRI Report)
pdf_label = tk.Label(user_frame, text="No PDF Uploaded", fg="white", bg="#282c34")
pdf_label.pack()
tk.Button(user_frame, text="📂 Upload MRI Report (PDF)", command=upload_pdf).pack()

# PDF Text Display Box
pdf_text_box = scrolledtext.ScrolledText(user_frame, wrap=tk.WORD, width=60, height=6, state=tk.DISABLED)
pdf_text_box.pack(pady=5)

# Tracking Page
tracking_frame = tk.Frame(root, bg="#282c34")

status_label = tk.Label(tracking_frame, text="Waiting...", font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

root.mainloop()
