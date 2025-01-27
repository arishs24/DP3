import time 
from sensor_library import *

sensor = Orientation_sensor()

while True:
    angles = sensor.euler_angles()
    lin_accel = sensor.lin_acceleration()
    accel - sensor.accelerometer()

    raw_x = angles[0]
    raw_y = angles[1]
    raw_z = angles[2]

    print("raw_x: " raw_x)
    print("raw_y: " raw_y)
    print("raw_z: " raw_z)

    