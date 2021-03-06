import cv2
import numpy as np
from collections import deque
from datetime import datetime
from time import time
from math import sin
import configparser

class VideoCamera(object):

    BUFFER_SIZE = 64
    pts = deque(maxlen=BUFFER_SIZE)


    def __init__(self):
         self.video = cv2.VideoCapture(0)
         self.ballLower = (5, 140, 140)
         self.ballUpper = (30, 255, 255)
         # Resize camera feed to 320x240,
         # note that cameras typically support only a subset of resolutions
         # self.video.set(3, 320)
         # self.video.set(4, 240)
         self.timestamp = datetime.now()
         self.frames = 0
         self.fps = 50

         self.lastPos = (0,0)

    def __del__(self):
        
        self.video.release()
        config = configparser.ConfigParser()
        config['LowerRange'] = {'Hue': '5' , 'Saturtation' : '130', 'Value' : '130'}
        config['UpperRange'] = {'Hue': '30' , 'Saturtation' : '255', 'Value' : '255'}
        with open('value.ini', 'w') as configfile:
            config.write(configfile)
       
 
    def get_frame(self):
            image = self.editFrame()
            self.frames -= 1
            if self.frames < 0:
                now = datetime.now()
                self.fps = 50 / (now - self.timestamp).total_seconds()
                self.timestamp = now
                self.frames = max(min(self.fps, 5), 50)

            ret, jpeg = cv2.imencode('.jpg', image)

            self.cache = jpeg.tobytes()
            return jpeg.tobytes()
    @staticmethod
    def funColor():
        r,g,b = abs(sin(time()))*255,abs(sin(time()*2))*255,abs(sin(time()*3))*255
        r,g,b = int(r),int(g),int(b)
        return r,g,b    

    def getDelta(self):
        return self.lastPos

    def getWidthHeight(self, frame):
         width   = np.size(frame, 1)
         height  = np.size(frame, 0)
         return width, height

    def editFrame(self):
        success, initialFrame = self.video.read()
        original = initialFrame
        flippedFrame = cv2.flip(initialFrame, 1)
        original = cv2.flip(original, 1)

        blurredFrame = cv2.GaussianBlur(flippedFrame, (11, 11), 0)
        hsvFrame = cv2.cvtColor(blurredFrame, cv2.COLOR_BGR2HSV)
        #print(hsvFrame)
        mask = cv2.inRange(hsvFrame, self.ballLower, self.ballUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        kernel = np.ones((5,5),np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        #find contours from mask
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        if len(cnts) > 0:

            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            if radius > 5:

                cv2.circle(flippedFrame, (int(x), int(y)), int(radius),
                    (0, 255, 255), 2)
                cv2.circle(flippedFrame, center, 5, (0, 0, 255), -1)
                radius = 1/radius
                radius = round(radius*100*11.35, 2)
                cv2.putText(flippedFrame,str(radius),(int(x),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(255,255,255),1,cv2.LINE_AA)
                cv2.putText(flippedFrame,str(radius),(int(x+3),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.59,(0,0,0),1,cv2.LINE_AA)

                width, height = self.getWidthHeight(hsvFrame)

                loc = (center[0]/width - 0.5)*2,-(center[1]/height-0.5)*2
                self.lastPos = loc

                loc = self.getDelta()
                r,g,b = VideoCamera.funColor()
                #distance from midposition
                cv2.putText(flippedFrame,"DFC: " + str(list(round(i,2) for i in loc)),(int(width*0.007),int(height*0.97)), cv2.FONT_HERSHEY_SIMPLEX, 0.60,(r,g,b),1,cv2.LINE_AA)
        #show fps
        cv2.putText(hsvFrame,"%.01f fps" % self.fps, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.3,(255,255,255),1,cv2.LINE_AA)


        cutout = cv2.bitwise_and(original,original, mask= mask)


        finalFrame = np.hstack([flippedFrame, cutout])
        return finalFrame
