import time 

from sensor_library import *

from gpiozero import Servo
from gpiozero import LED

red_led = LED(6)

sensor = Orientation_Sensor()
servo = Servo(8)


def main():
    while True:
        global angles, raw_x, raw_y, raw_z
        angles = sensor.euler_angles()
        lin_accel = sensor.lin_acceleration()
        accel = sensor.accelerometer()

        time.sleep(0.5)
        
        avg = rolling_average()

        check_limit_x = within_limit_x(avg[0], 200, 400)
        check_limit_y = within_limit_y(avg[1], -0.1, -78)
        check_limit_z = within_limit_z(avg[2], 0, 120)

        if check_limit_x == False or check_limit_z == False:
            print("ITS OFFFFFFFFFF FOR X AND Y")
            red_led.on()
        else:
            red_led.off()

        if check_limit_y == 0:
            print("goooooooooooood")
        elif check_limit_y == 1:
            print("UNDEEERRRRR")
            servo.max()
        elif check_limit_y == 2:
            print("OVVEEERR")
            servo.min()

        


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


    if x_avg < 130:
        x_avg = 360 + x_avg

    if z_avg < 180:
        z_avg = 60 + z_avg
        
    angles = [x_avg, y_avg, z_avg]
    print("ROLLING AVERAGE: ", x_avg, y_avg, z_avg)
    return angles


def within_limit_x(x_angles, lower_limitx, upper_limitx):
    if lower_limitx < x_angles < upper_limitx:
        return True
    else:
        return False

def within_limit_z(z_angles, lower_limitz, upper_limitz):
    if lower_limitz < z_angles < upper_limitz:
        return True
    else:
        return False

def within_limit_y(y_angles, lower_limity, upper_limity):
    if lower_limity < y_angles < upper_limity:
        return 0
    elif y_angles < lower_limity:
        return 1
    elif y_angles > upper_limity:
        return 2
