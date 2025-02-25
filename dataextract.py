import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sensor_library import Orientation_Sensor  # Your existing sensor module

# Initialize Sensor
sensor = Orientation_Sensor()

# Data Storage
time_stamps = []
y_angle_values = []
start_time = time.time()
min_angle = float('inf')  # Start with a very high number
max_angle = float('-inf')  # Start with a very low number

# Live Graph Setup
fig, ax = plt.subplots(figsize=(6, 4))
ax.set_title("Bicep Curl Motion Tracking")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Y-Angle (Degrees)")
line, = ax.plot([], [], label="Arm Angle")
ax.legend()

def update_graph(frame):
    global min_angle, max_angle

    # Get sensor data
    angles = sensor.euler_angles()
    if angles is None or len(angles) < 3:
        return

    y_angle = angles[1]  # Assuming Y-axis tracks the bicep curl motion
    elapsed_time = round(time.time() - start_time, 1)

    # Update min/max angles
    if y_angle < min_angle:
        min_angle = y_angle
    if y_angle > max_angle:
        max_angle = y_angle

    # Store values
    time_stamps.append(elapsed_time)
    y_angle_values.append(y_angle)

    # Keep last 50 points
    if len(time_stamps) > 50:
        time_stamps.pop(0)
        y_angle_values.pop(0)

    # Update Graph
    line.set_data(time_stamps, y_angle_values)
    ax.set_xlim(max(0, elapsed_time - 5), elapsed_time + 1)
    ax.set_ylim(min(y_angle_values) - 5, max(y_angle_values) + 5)

def stop_tracking():
    """Stops tracking and prints results."""
    print("\n✅ Bicep Curl Data Collection Complete!")
    print(f"📏 Min Flexion Angle (Fully Extended): {min_angle:.2f}°")
    print(f"📏 Max Flexion Angle (Fully Curled): {max_angle:.2f}°")
    print("\n📩 Send me these values so we can integrate them!")

    plt.ioff()
    plt.show()

# Start Graph Animation
ani = FuncAnimation(fig, update_graph, interval=500)

try:
    print("\n🎥 Start performing bicep curls...")
    print("🚀 Move your arm through a full range of motion!")
    print("📊 Watch the graph update in real-time!")
    print("❌ Press Ctrl+C when done to stop tracking and get results.")

    plt.show()
except KeyboardInterrupt:
    stop_tracking()
