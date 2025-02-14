import time 
from sensor_library import *
from gpiozero import Servo

red_led = LED(6)
sensor = Orientation_sensor()
servo = Servo(8)
rolling_avg = rolling_average()

def main():
    while True:
        angles = sensor.euler_angles()
        lin_accel = sensor.lin_acceleration()
        accel = sensor.accelerometer()

        raw_x = angles[0]
        raw_y = angles[1]
        raw_z = angles[2]

        print("raw_x: " raw_x)
        print("raw_y: " raw_y)
        print("raw_z: " raw_z)

        # CALIBRATION TO SET THE LIMITS
        # I WILL TEST OUT THE RATIOS
        # calibration() this will return "default" coordinates 
        # the limits for x, y, and z for both upper and below will be established in the FRONT END
        # z ratio = 
        # z limit under = default limit under * ratio
        # z limit above = default limit above * ratio
        
        check_limit_x = within_limit_x(rolling_avg[0],)
        check_limit_y = within_limit_y()
        check_limit_z = within_limit_z()

        if check_limit_x == False or limit_z == False:
            red_led.on()
            
        if check_limit_y == 1:

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

    coord_list = [x_avg, y_avg, z_avg]
    return coord_list



def within_limit_x(x_angles, lower_limitx, upper_limitx):
    if lower_limitx < x_angles < upper_limitx:
        return True
    else:
        return False
        
def within_limit_y(y_angles, lower_limit, upper_limit):
    if lower_limity < y_angles < upper_limity:
        return True
    else:
        return False

def within_limit_z(z_angles, lower_limitz, upper_limitz):
    if lower_limitz < z_angles < upper_limitz:
        return 0
    elif z_angles < lower_limitz:
        return 1
    elif z_angles > upper_limitz:
        return 2



# We have rolling input
# Now we need limits on the input 
# Breaking the limits wiill result in:
# 1: LED on
# 2: SERVO - max direction maybe not all the way
# 3: SERVO - min direction maybe not all the way