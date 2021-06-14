# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 23:54:42 2021

@author: rosebud
"""

import time
import pyautogui
import pydirectinput

pressnum = 42



#time.sleep(5)

#up (jittery)
#pydirectinput.press('up',presses=20)


##up (smooth)
#pydirectinput.keyDown('up')
#time.sleep(3)
#pydirectinput.keyUp('up')


##spin
#pydirectinput.keyDown('left')
#time.sleep(3)
#pydirectinput.keyUp('left')


#up then turn then up
#pydirectinput.keyDown('up')
#time.sleep(2)
#pydirectinput.keyUp('up')
#
#pydirectinput.press('left',presses=42)
#
#pydirectinput.keyDown('up')
#time.sleep(2)
#pydirectinput.keyUp('up')

#360 spin

#pydirectinput.press('left',presses=pressnum)
#time.sleep(1)
#pydirectinput.press('left',presses=pressnum)
#time.sleep(1)
#pydirectinput.press('left',presses=pressnum)
#time.sleep(1)
#pydirectinput.press('left',presses=pressnum)
#time.sleep(1)


##there and back
#pydirectinput.press('right',presses=65)
#pydirectinput.keyDown('up')
#time.sleep(3)
#pydirectinput.keyUp('up')
#pydirectinput.press('left',presses=33)
#pydirectinput.keyDown('up')
#time.sleep(3)
#pydirectinput.keyUp('up')
#
#pydirectinput.press('right',presses=33)
#pydirectinput.keyDown('up')
#time.sleep(3)
#pydirectinput.keyUp('up')
#pydirectinput.press('left',presses=65)
#pydirectinput.keyDown('up')
#time.sleep(3)
#pydirectinput.keyUp('up')


#pydirectinput.move(100,0)

#pydirectinput.press('altleft')
#time.sleep(.5)
#pyautogui.mouseDown(button='right')
#time.sleep(1)
#pyautogui.mouseDown(button='left')
##pyautogui.mouseDown(button='left')
#time.sleep(1)
##pyautogui.move(25,25,1)
#pyautogui.dragTo(50,50,1,button='left',_pause=False,mouseDownUp=False)
#pyautogui.mouseUp(button='right')
#pyautogui.mouseUp(button='left')
#pyautogui.dragTo()


#time.sleep(3)


time.sleep(.5)
pydirectinput.keyDown('alt')
pydirectinput.press('tab')
pydirectinput.keyUp('alt')
time.sleep(4)


pydirectinput.press('i')
time.sleep(.5)
#pydirectinput.click(button='left')
#time.sleep(.5)
#pydirectinput.press('~')
#time.sleep(1.5)

pydirectinput.mouseDown(button='right')
time.sleep(.5)
pydirectinput.mouseDown(button='left')
#pyautogui.dragTo(500,500,1,button='left',_pause=False,mouseDownUp=False)
pydirectinput.move(-500,0)

time.sleep(.5)
pydirectinput.mouseUp(button='left')
pydirectinput.mouseUp(button='right')

time.sleep(3)
pydirectinput.press('esc')

time.sleep(.5)
pydirectinput.keyDown('alt')
pydirectinput.press('esc')
pydirectinput.keyUp('alt')



#time.sleep(3)

#pyautogui.alert('finished')
