import time
import threading
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gpiozero import Servo, Buzzer
from sensor_library import *

MAX_VELOCITY_THRESHOLD = 2.5  
ROLLING_WINDOW = 10  

servo = Servo(8)
buzzer = Buzzer(6)
buzzer.off()
sensor = Orientation_Sensor()

def rolling_average(data_buffer):
    if len(data_buffer) < ROLLING_WINDOW:
        return None  
    return round(sum(data_buffer[-ROLLING_WINDOW:]) / len(data_buffer), 2)

def collect_user_bicep_curl_range(sensor):
    print("📢 Perform a few bicep curls to determine range of motion.")
    time.sleep(2)

    collected_y_angles = []
    for _ in range(10):
        angles = sensor.euler_angles()
        if angles is not None and len(angles) >= 3:
            collected_y_angles.append(angles[1])
        time.sleep(0.5)

    if len(collected_y_angles) < 5:
        print("⚠️ Calibration failed: Not enough movement data detected. Try again.")
        return None, None  

    return min(collected_y_angles), max(collected_y_angles)

def adjust_servo_resistance(y_avg, angular_velocity, min_flexion, max_flexion, servo):
    if min_flexion is None or max_flexion is None:
        print("⚠️ Error: Flexion range not set. Skipping resistance adjustment.")
        return 0  

    if abs(angular_velocity) > MAX_VELOCITY_THRESHOLD:
        print("⚠️ TOO FAST! Restricting movement.")
        servo.mid()  
        return 0  

    resistance = (y_avg - min_flexion) / (max_flexion - min_flexion)
    resistance = max(0, min(1, resistance))  

    if resistance < 0.3:
        servo.min()
    elif resistance > 0.7:
        servo.max()
    else:
        servo.mid()

    return resistance

def update_graph(time_stamps, y_angle_values, servo_positions, angular_velocity_values, acceleration_values):
    ax.clear()
    ax.plot(time_stamps, y_angle_values, label="Y-Angle (Posture)", color="blue")
    ax.plot(time_stamps, angular_velocity_values, label="Angular Velocity", color="green")
    ax.plot(time_stamps, acceleration_values, label="Acceleration", color="purple")
    ax.plot(time_stamps, servo_positions, label="Servo Position", color="red")

    ax.set_title("Posture & Motion Tracking")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(True)

    canvas.draw()

def tracking_loop(min_flexion, max_flexion, sensor, servo):
    time_stamps = []
    y_angle_values = []
    servo_positions = []
    angular_velocity_values = []
    acceleration_values = []
    data_buffer_y = []
    rep_count = 0
    start_time = time.time()
    rep_in_progress = False

    print("\nY-Angle (raw)\tY-Angle (avg)\tSlope\tMotor")
    
    while True:
        angles = sensor.euler_angles()
        angular_velocity = sensor.gyroscope()
        linear_accel = sensor.lin_acceleration()

        if angles is None or len(angles) < 3 or angular_velocity is None or linear_accel is None:
            continue  

        raw_y = angles[1]
        raw_x = angles[0]

        if raw_x > 280 or raw_x < 80:
            buzzer.off()
        else:
            buzzer.on()

        data_buffer_y.append(raw_y)

        y_avg = rolling_average(data_buffer_y)
        if y_avg is None:
            continue  

        slope = 0 if len(data_buffer_y) < 2 else data_buffer_y[-1] - data_buffer_y[-2]

        resistance = adjust_servo_resistance(y_avg, angular_velocity[1], min_flexion, max_flexion, servo)

        motor_state = "Rotating" if abs(slope) > 5 else "Off"
        if slope > 5.0:
            servo.max()
        elif slope < -5.0:
            servo.min()
        else:
            servo.mid()

        if angular_velocity[1] > 0.5 and not rep_in_progress:  
            rep_in_progress = True
        elif angular_velocity[1] < 0.1 and rep_in_progress:
            rep_count += 1
            print(f"✅ Rep {rep_count} Completed!")
            rep_in_progress = False  

        elapsed_time = round(time.time() - start_time, 1)
        time_stamps.append(elapsed_time)
        y_angle_values.append(y_avg)
        servo_positions.append(resistance)
        angular_velocity_values.append(angular_velocity[1])
        acceleration_values.append(linear_accel[1])

        if len(time_stamps) > 50:
            time_stamps.pop(0)
            y_angle_values.pop(0)
            servo_positions.pop(0)
            angular_velocity_values.pop(0)
            acceleration_values.pop(0)

        print(f"{raw_y:.1f}\t{y_avg:.1f}\t{slope:.1f}\t{motor_state}")

        root.after(0, lambda: update_graph(time_stamps, y_angle_values, servo_positions, angular_velocity_values, acceleration_values))
        root.after(0, lambda: posture_status.set(f"📏 Y: {y_avg:.2f}° | 🎛️ Servo: {resistance:.2f} | 🔄 Reps: {rep_count}"))

        time.sleep(0.5)

def start_tracking(sensor, servo):
    min_flexion, max_flexion = collect_user_bicep_curl_range(sensor)
    if min_flexion is None or max_flexion is None:
        print("⚠️ Cannot start tracking. Calibration failed.")
        return  

    threading.Thread(target=tracking_loop, args=(min_flexion, max_flexion, sensor, servo), daemon=True).start()
    root.after(0, lambda: posture_status.set("✅ Tracking Started!"))

def save_user_info():
    user_info["name"] = name_entry.get()
    user_info["age"] = age_entry.get()
    user_info["weight"] = weight_entry.get()
    user_info["gender"] = gender_var.get()

    user_frame.pack_forget()
    tracking_frame.pack()

user_info = {}

root = tk.Tk()
root.title("Smart Rehab Band UI")
root.geometry("800x700")
root.config(bg="#282c34")

posture_status = tk.StringVar()
posture_status.set("Waiting...")

user_frame = tk.Frame(root, bg="#282c34")
user_frame.pack()

tk.Label(user_frame, text="User Information", font=("Arial", 16), fg="white", bg="#282c34").pack()

tk.Label(user_frame, text="Name:", fg="white", bg="#282c34").pack()
name_entry = tk.Entry(user_frame)
name_entry.pack()

tk.Label(user_frame, text="Age:", fg="white", bg="#282c34").pack()
age_entry = tk.Entry(user_frame)
age_entry.pack()

tk.Label(user_frame, text="Weight (lbs):", fg="white", bg="#282c34").pack()
weight_entry = tk.Entry(user_frame)
weight_entry.pack()

gender_var = tk.StringVar(value="Male")
tk.Label(user_frame, text="Gender:", fg="white", bg="#282c34").pack()
tk.OptionMenu(user_frame, gender_var, "Male", "Female").pack()

tk.Button(user_frame, text="Submit & Continue", command=save_user_info).pack(pady=10)

tracking_frame = tk.Frame(root, bg="#282c34")

tk.Button(tracking_frame, text="📝 Perform Calibration (Do 10 Reps)", command=lambda: start_tracking(sensor, servo)).pack(pady=5)
status_label = tk.Label(tracking_frame, textvariable=posture_status, font=("Arial", 14), fg="white", bg="#282c34")
status_label.pack(pady=5)

fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=tracking_frame)
canvas.get_tk_widget().pack()

root.mainloop()
