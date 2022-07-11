import cv2
import numpy as np
import mss
from time import sleep
from pynput import mouse
from pynput.mouse import Button
# For future me this might brake pyinstaller 
from string_encoded_images import strings

def MatchTemplate(Image, template):
    res = cv2.matchTemplate(Image,template, cv2.TM_CCORR_NORMED)
    h,w = template.shape
    min_val, max_val,min_loc,max_loc =  cv2.minMaxLoc(res)
    cv2.waitKey()
    if max_val > 0.9:
        return True,max_loc,w,h
    return False,[],0,0

def FindTemplateOnImage(image,template,shouldClick = True,callback = ()):
    mouseController = mouse.Controller()
    found,loc,w,h =  MatchTemplate(image,template)
    callback
    if found:
        if shouldClick:
            mouseController.position = (loc[0] + w/2 , loc[1] + h/2)
            mouseController.press(Button.left)
            mouseController.release(Button.left)
        callback


def ScreenShot():
    with mss.mss() as sct:
        screenshot = np.array(sct.grab(sct.monitors[0]))
        screenshot = cv2.cvtColor(screenshot,cv2.COLOR_RGB2GRAY)
        return screenshot

def hello(name):
    print(f"Hello {name}")

def MatchAccept():

    Running = True
    found_match,accept,lobby = strings()
    lobby = cv2.imdecode(np.fromstring(lobby,np.uint8,sep=","), -1)
    template = cv2.imdecode(np.fromstring(accept,np.uint8,sep=","), -1)
    startGameTemplate = cv2.imdecode(np.fromstring(found_match,np.uint8,sep=","), -1)
    while Running:
        ss = ScreenShot()
        FindTemplateOnImage(ss, startGameTemplate,True,hello("XD"))
        FindTemplateOnImage(ss, template,True,hello("There"))
        in_lobby,loc1,w1,w2 = MatchTemplate(ss,lobby)
        if (in_lobby):
            Running = False
            
        sleep(1)

MatchAccept()   