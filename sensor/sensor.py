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


def rolling_average():
    i = 0
    x_avg = 0
    y_avg = 0
    z_avg = 0
    x_list = []
    y_list = []
    z_list = []
    for i in range(10):
        x_list.append(raw_x)
        y_list.append(raw_y)
        z_list.append(raw_z)
        i += 1

    for x in x_list:
        x_avg += x
    x_avg = x_avg/len(x_list)

    for y in y_list:
        y_avg += y
    y_avg = y_avg/len(y_list)

    for z in z_list:
        z_avg += z
    z_avg = z_avg/len(z_list)

    return x_avg, y_avg, z_avg