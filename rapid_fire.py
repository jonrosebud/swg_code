# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 14:57:48 2021

@author: trose
"""
import time
import pyautogui as pag
import pydirectinput_tmr as pdi
import pygame
pygame.init()
import sys
sys.path.append(r'D:\python_scripts\pdi_tmr')
import pdi_tmr
def rapid_fire():
    running = True
    joystick = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())][1]
    joystick.init()
    weapon_groups = '123'
    rapid_fire_mode = True
    is_pressed = {'B1': False, 'B7': False}
    events = pygame.event.get()
    
    while running:
        events = pygame.event.get()
        if joystick.get_button(0) != 0:
            if rapid_fire_mode:
                pdi_tmr.typewrite_fast(weapon_groups, loops=2, interval=0.08)
            else:
                pdi_tmr.press_fast('6')
        #if joystick.get_button(6) != 0:
        #    # Toggle button for whether to do rapid fire or not.
        #    rapid_fire_mode = not rapid_fire_mode
        '''
            
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                is_pressed['B1'] = True
            elif event.type == pygame.JOYBUTTONUP and event.button == 0:
                is_pressed['B1'] = False
            elif event.type == pygame.JOYBUTTONDOWN and event.button == 6:
                # Toggle button for whether to do rapid fire or not.
                is_pressed['B7'] = not is_pressed['B7']
            if is_pressed['B1']:
                if is_pressed['B7']:
                    pdi_tmr.typewrite_fast(weapon_groups, loops=1, interval=0.06)
                    #time.sleep(0.1)
                else:
                    pdi_tmr.press_fast('6')
        if joystick.get_button(0) != 0:
            print(joystick.get_button(0))
            return              
        '''
            
def main():
    #time.sleep(5)
    rapid_fire()
    pygame.quit()
    
if __name__ == '__main__':
    main()