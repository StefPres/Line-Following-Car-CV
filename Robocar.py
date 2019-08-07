# This program illustrates how to capture frames in a video stream and how to do further processing on them
# It uses numpy to do the calculations and OpenCV to display the frames

import picamera
import picamera.array                           # This needs to be imported explicitly
import time
import cv2
import numpy as np
import imutils
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

# set GPIO Pins
GPIO_Ain1 = 11
GPIO_Ain2 = 13
GPIO_Apwm = 15
GPIO_Bin1 = 29
GPIO_Bin2 = 31
GPIO_Bpwm = 33

# Set GPIO direction (IN / OUT)
GPIO.setup(GPIO_Ain1, GPIO.OUT)
GPIO.setup(GPIO_Ain2, GPIO.OUT)
GPIO.setup(GPIO_Apwm, GPIO.OUT)
GPIO.setup(GPIO_Bin1, GPIO.OUT)
GPIO.setup(GPIO_Bin2, GPIO.OUT)
GPIO.setup(GPIO_Bpwm, GPIO.OUT)

# Both motors are stopped 
GPIO.output(GPIO_Ain1, False)
GPIO.output(GPIO_Ain2, False)
GPIO.output(GPIO_Bin1, False)
GPIO.output(GPIO_Bin2, False)

pwm_frequency = 50

# Create the PWM instances
pwmA = GPIO.PWM(GPIO_Apwm, pwm_frequency)
pwmB = GPIO.PWM(GPIO_Bpwm, pwm_frequency)

# Set the duty cycle (between 0 and 100)
# The duty cycle determines the speed of the wheels
motor1 = 45
motor2 = 45
pwmA.start(motor1)
pwmB.start(motor2)

lowerColorThreshold = np.array([100, 115, 145])
upperColorThreshold = np.array([255,255,255])

# Initialize the camera
x = 640
y = 480
camera = picamera.PiCamera()
camera.resolution = (x, y)
camera.framerate = 24
camera.vflip = False                            # Flip upside down or not
camera.hflip = False                             # Flip left-right or not


linedetect = time.time()
detected = False

# Create a data structure to store a frame
rawframe = picamera.array.PiRGBArray(camera, size=(640, 480))


# Allow the camera to warm up
time.sleep(1)

def motorcheck(speed):
    if(speed > 70):
        speed = 70
    if(speed < 20):
        speed = 20
    return speed

def backup():
    GPIO.output(GPIO_Ain1, False)
    GPIO.output(GPIO_Bin1, False)
    GPIO.output(GPIO_Ain2, True)
    GPIO.output(GPIO_Bin2, True)
    time.sleep(1)
    GPIO.output(GPIO_Ain2, False)
    GPIO.output(GPIO_Bin2, False)
    GPIO.output(GPIO_Ain1, True)
    GPIO.output(GPIO_Bin1, True)
    
        


if __name__ == '__main__':
    try:
        
        # Continuously capture frames from the camera
        # Note that we chose the RGB format
        GPIO.output(GPIO_Ain1, True)
        GPIO.output(GPIO_Bin1, True)
        for frame in camera.capture_continuous(rawframe, format = 'rgb', use_video_port = True):

            # Clear the rawframe in preparation for the next frame
            rawframe.truncate(0)


            # Create a numpy array representing the image
            img_np = frame.array


            #-----------------------------------------------------
            # We will use numpy to do all our image manipulations
            #-----------------------------------------------------

            image_hsv = cv2.cvtColor(img_np, cv2.COLOR_BGR2HSV)

            # Threshold the HSV image to get only colors in a range
            # The colors in range are set to white (255), while the colors not in range are set to black (0)
            ourmask = cv2.inRange(image_hsv, lowerColorThreshold, upperColorThreshold)
            ourmask2 = ourmask[0:350,:]
            #eliminates noise
            ourmask2 = cv2.erode(ourmask2, None, iterations=1)
            ourmask2 = cv2.dilate(ourmask2, None, iterations=1)
            

            # Count the number of white pixels in the mask
       
            # Get the size of the array (the mask is of type 'numpy')
            # This should be 640 x 480 as defined earlier
            #numx, numy = ourmask.shape

            # Select a part of the image and count the number of white pixels

            line = cv2.findContours(ourmask2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            line = imutils.grab_contours(line)
            cX = 320
            cY = 240
            detected = False
            
            for c in line:

                c = max(line, key=cv2.contourArea)
                ((x,y),radius) = cv2.minEnclosingCircle(c)
                
                M = cv2.moments(c)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                detected = True
                
                if(radius > 4):
                    cv2.drawContours(img_np, [c], -1, (0,255,0), 2)
                    cv2.circle(img_np, (cX,cY), 5, (0,0,0), -1)
                    linedetect = time.time()
                    
                    #spacer
            if(not(cX > 295 and cX < 345) and detected):
                motor1 = motorcheck(45 - (int((cX-320)/15)))
                motor2 = motorcheck(45 + (int((cX-320)/15)))
            else:
                motor1 = 45
                motor2 = 45
            pwmA.ChangeDutyCycle(motor1)
            pwmB.ChangeDutyCycle(motor2)
            if(time.time() > linedetect + 5):
                linedetect = time.time()
                backup()
                
            
                    

                    
                          
            
            # Bitwise AND of the mask and the original image

            # Show the frames
            # Note that OpenCV assumes BRG color representation, and we therefore swapped the r and b color channels
            # The waitKey command is needed to force openCV to show the image 
            cv2.circle(img_np, (320, 395), 5, (255,0,0), -1)
            #cv2.circle(img_np, (270, 395), 5, (255,0,0), -1)
            #cv2.circle(img_np, (370, 395), 5, (255,0,0), -1)
            cv2.circle(img_np, (220, 395), 5, (255,0,0), -1)
            cv2.circle(img_np, (420, 395), 5, (255,0,0), -1)
            cv2.line(img_np,(320, 395), (cX,cY), (0,0,0),3)
            cv2.line(img_np,(320 + int((cX-320)/2), 400), (320,440),(0,0,255),4)
            #cv2.rectangle(img_np, (50,350),(120,450), (255,255,0), 2)
            #cv2.line(img_np,(50, 450 - motor1), (80, 450 - motor1),(255,0,0),4)
            #cv2.line(img_np,(90, 450 - motor2), (120, 450 - motor2),(255,0,0),4)
            cv2.putText(img_np, str(motor1) + "%  " + str(motor2) + "%", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
                      

            
            cv2.imshow("Orignal frame", img_np[:,:,::-1])
            #cv2.imshow("Mask", ourmask2)
            cv2.waitKey(1)

            




    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Program stopped by User")
        cv2.destroyAllWindows()
        # Clean up the camera resources
        GPIO.cleanup()
        camera.close()
        
