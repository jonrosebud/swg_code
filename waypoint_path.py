# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 23:02:32 2021

@author: rosebud
"""

import time
#import pyautogui
import pydirectinput
import math


position_desired = [10,10] #x,y
position_actual = [1,1]
tolerance = 1
debugging = True

w = False
s = False
q = False
e = False

#
# update position_desired
#position_desired = [1,1]
if debugging == True:
    print(position_desired)
    
    
while (not(math.isclose(position_desired[1], position_actual[1], abs_tol = tolerance) and math.isclose(position_desired[0], position_actual[0], abs_tol = tolerance))):
    
    position_actual[0] = int(input('position_actual[0] '))
    position_actual[1] = int(input('position_actual[1] '))
    
    # w
    if position_desired[1] > position_actual[1] and not math.isclose(position_desired[1], position_actual[1], abs_tol = tolerance):
        if w == True:
            if debugging == True:
                print('w ',w)
            pass # do nothing
        else:
            w = True
            if debugging == True:
                print('w ',w)
            if debugging == False:
                pydirectinput.keyDown('w') # up
    else:
        w = False
        if debugging == True:
            print('w ',w)
        if debugging == False:
            pydirectinput.keyUp('w')
    
    
    # s
    if position_desired[1] < position_actual[1] and not math.isclose(position_desired[1], position_actual[1], abs_tol = tolerance):
        if s == True:
            if debugging == True:
                print('s ',s)
            pass # do nothing
        else:
            s = True
            if debugging == True:
                print('s ',s)
            if debugging == False:
                pydirectinput.keyDown('s') # down
    else:
         s = False
         if debugging == True:
             print('s ',s)
         if debugging == False:
             pydirectinput.keyUp('s') # down
        
        
    # q                       
    if position_desired[0] < position_actual[0] and not math.isclose(position_desired[0], position_actual[0], abs_tol = tolerance):
        if q == True:
            if debugging == True:
                print('q ',q)
            pass # do nothing
        else:
            q = True
            if debugging == True:
                print('q ',q)
            if debugging == False:
                pydirectinput.keyDown('q') # left
    else:
        q = False
        if debugging == True:
            print('q ',q)
        if debugging == False:
            pydirectinput.keyUp('q') # left
        
    
    # e
    if position_desired[0] > position_actual[0] and not math.isclose(position_desired[0], position_actual[0], abs_tol = tolerance):
        if e == True:
            if debugging == True:
                print('e ',e)
            pass # do nothing
        else:
            e = True
            if debugging == True:
                print('e ',e)
            if debugging == False:
                pydirectinput.keyDown('e') # right
    else:
        e = False
        if debugging == True:
            print('e ',e)
        if debugging == False:
            pydirectinput.keyUp('e') # right
            
                               
time.sleep(1)
        