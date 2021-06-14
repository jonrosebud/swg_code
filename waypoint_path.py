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
    
    
while (not(math.isclose(position_desired[1], position_actual[1], rel_tol = 0.1) or math.isclose(position_desired[0], position_actual[0], rel_tol = 0.1))):
    
    # w
    if position_desired[1] > position_actual[1]:
        if w == True:
            if debugging == True:
                print(w)
            continue
        else:
            w = True
            if debugging == True:
                print(w)
            if debugging == False:
                pydirectinput.keyDown('w') # up
    else:
        w = False
        if debugging == True:
            print(s)
        if debugging == False:
            pydirectinput.keyUp('w')
    
    
    # s
    if position_desired[1] < position_actual[1]:
        if s == True:
            if debugging == True:
                print(s)
            continue
        else:
            s = True
            if debugging == True:
                print(s)
            if debugging == False:
                pydirectinput.keyDown('s') # down
    else:
         s = False
         if debugging == True:
             print(s)
         if debugging == False:
             pydirectinput.keyUp('s') # down
        
        
    # q                       
    if position_desired[0] < position_actual[0]:
        if q == True:
            if debugging == True:
                print(q)
            continue
        else:
            q = True
            if debugging == True:
                print(q)
            if debugging == False:
                pydirectinput.keyDown('q') # left
    else:
        q = False
        if debugging == True:
            print(q)
        if debugging == False:
            pydirectinput.keyUp('q') # left
        
    
    # e
    if position_desired[0] > position_actual[0]:
        if e == True:
            if debugging == True:
                print(e)
            continue
        else:
            e = True
            if debugging == True:
                print(e)
            if debugging == False:
                pydirectinput.keyDown('e') # right
    else:
        e = False
        if debugging == True:
            print(e)
        if debugging == False:
            pydirectinput.keyUp('e') # right
            
                               
time.sleep(1)
        