# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 15:55:17 2021

@author: trose
"""

import time
import pyautogui as pag
import swg_window_management as swm
import os
import pydirectinput as pdi


def press_destroy(coords, j):
    pdi.press('esc', presses=2)
    pdi.press('i')
    for destroy_key in ['6', '4', '5', '3']:
        pdi.moveTo(coords[j][0], coords[j][1])
        pdi.mouseDown(button='right')
        pdi.mouseUp(button='right')
        time.sleep(1)
        pdi.press(destroy_key)
    pdi.press('d', presses=2)
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.press('s')
    pdi.keyUp('shift')
    pdi.keyUp('ctrl')
    

def main():
    # If running the auto invite macro, then sometimes it can put '5' in the 
    # chat bar instead of sending the destroy command and then end up pressing
    # 3 which is the equip appearance for backpacks. This is a problem but
    # happens rarely. Also, if something was destroyed by 5 and then the 
    # next item is a backpack, then pressing 3 will equip appearance.
    # If this program is running continuously then the latter problem won't
    # occur except very rarely.
    coords = [[652, 572], [1883, 507], [2655, 572]]
    i = 0
    while True:
        for j, swg_window in enumerate(swm.swg_windows):
            swg_window.set_focus()
            time.sleep(1)
            press_destroy(coords, j)
            time.sleep(1)
        i += 1
        
if __name__ == '__main__':
    swm.calibrate_window_position(swm.swg_windows)
    main()
    