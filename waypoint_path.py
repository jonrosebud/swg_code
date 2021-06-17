# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 23:02:32 2021

@author: rosebud
"""

import time
#import pyautogui
import pydirectinput as pdi
import get_land_coords as glc
import pandas as pd
import math


def hold_down_keys(key_df):
    '''
    key_df: pd.DataFrame
        Used to keep track of which keys are held down or not and which keys
        need to be held down and not.
        
        Index: list of str of keys that can be held down
            e.g. ['w','s','q','e','a','d']
        
        Columns: 'should_be_down', 'is_down'
        
        'should_be_down': bool
            True: the key should be held down
            False: the key should be in the up (unpressed) position
            
        'is_down': bool
            True: the key is being held down right now
            False: o/w
            
    Returns
    -------
    key_df: pd.DataFrame
        key_df is now updated.
    
    Purpose
    -------
    Hold down the keys that need to be held down by using pdi.keyDown(key) (if 
    it is not already held down) and lift up the keys that are currently down 
    but that do not need to be held down (as dictated by the given key_df).
    '''
    for key in key_df.index:
        if key_df.loc[key]['should_be_down']:
            if not key_df.loc[key]['is_down']:
                pdi.keyDown(key)
                key_df.loc[key]['is_down'] = True
        elif key_df.loc[key]['is_down']:
            pdi.keyUp(key)
            key_df.loc[key]['is_down'] = False
    return key_df


def main():
    '''
    1. Calibrate window positions
    2. Figure out initial orientation and position
    3. Iterate through the waypoints
    4. Mission specifics things (including Junk Dealer or house)
    5. Sorting inventory
    
    Initialize toon in an open area
    Calibrate the direction you're facing (if the code assumes initially North)
    Iterate through the waypoints, travelling from one to the next, to the next...
    Mission specifics things
    Sorting inventory
    Travelling to Junk Dealer or house (this is like a mission)
    '''
    #wp_lst = [[-3028, 10], [-2912, -90], [-2823, -119], [-3019, -181], [-2927, -239]]
    #wp_lst = [[-2800, 1600], [-2800, 1700]]
    starport_to_near_terminal = [
        [-5400, -2202], [-5405, -2210], [-5395, -2215], [-5383, -2217], 
        [-5375,-2222], [-5359,-2222], [-5350, -2226], [-5339, -2213]]

    near_terminal_to_starport_entrance = [
        [-5326, -2226], [-5321, -2222], [-5322, -2215], [-5319, -2212], [-5303, -2223]]
    wp_lst = starport_to_near_terminal + near_terminal_to_starport_entrance
    swg_windows = glc.get_swg_windows()
    glc.calibrate_window_position(swg_windows)
    glc.north_calibrate(swg_windows[0], arrow_rect_csv_fpath='arrow_rect.csv')
    position_actual = glc.get_land_coords(swg_windows[0])
    key_df = pd.DataFrame({'should_be_down':[False]*6, 'is_down':[False]*6}, index=['w','s','q','e','a','d'])
    tolerance = 0
    debugging = False
    for position_desired in wp_lst:
        if debugging:
            print(position_actual)
            
        while (not(math.isclose(position_desired[1], position_actual[1], abs_tol = tolerance) and math.isclose(position_desired[0], position_actual[0], abs_tol = tolerance))):
            # Update position_actual by taking a new screenshot
            position_actual = glc.get_land_coords(swg_windows[0])
            # w
            key_df.loc['w']['should_be_down'] = (position_desired[1] > position_actual[1] and not math.isclose(position_desired[1], position_actual[1], abs_tol = tolerance))
            # s
            key_df.loc['s']['should_be_down'] = (position_desired[1] < position_actual[1] and not math.isclose(position_desired[1], position_actual[1], abs_tol = tolerance))
            # q                       
            key_df.loc['q']['should_be_down'] = (position_desired[0] < position_actual[0] and not math.isclose(position_desired[0], position_actual[0], abs_tol = tolerance))
            # e
            key_df.loc['e']['should_be_down'] = (position_desired[0] > position_actual[0] and not math.isclose(position_desired[0], position_actual[0], abs_tol = tolerance))
            # hold down the appropriate keys
            key_df = hold_down_keys(key_df)


if __name__ == '__main__':
    main()