# -*- coding: utf-8 -*-
"""
Created on Sun Jun 13 23:02:32 2021

@author: rosebud
"""

import time
import pydirectinput_tmr as pdi
import get_land_coords as glc
import pandas as pd
import math
from copy import deepcopy


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


def empty_function():
    pass


def move_along(swg_window_region, waypoint_list, planning_mode=False, function_list=[empty_function]):
    '''
    swg_window_region: dict
        Defines a rectangular area of the screen corresponding to the swg_window.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
    waypoint_list: a list of list of integer
        A list of waypoint(s) to go to. Includes x, y, (in-game planetary 
        coordinates) time delay, and the index of function_list (allow you to
        to call the function at that index) such that each sub-list has the 
        format [x, y, t, f]
        
        t is the wait time, in seconds, AFTER reaching a particular waypoint
        and includes time spent executing the function f. 
        
        ex. #1 If you put 1 second for t and f takes 0.2 seconds, then the total 
        time that you will wait after reaching the waypoint is 1 second.
        
        ex. #2 If you put 1 second for t and f takes 3 seconds, then the total
        time that you will wait after reaching the waypoint is 3 seconds.
        
    planning_mode: bool
        True: Do not sleep as prescribed in the t of the waypoint.
        False: Sleep as prescribed in the t of the waypoint.
        
    function_list: list of callable
        List of functions where the order of the functions is such that they 
        correspond to the index number provided in the int f in [x, y, t, f].
        This function will be called once you reach the desired waypoint given
        by the x and y parts.
        
        The default value for f is 0 so the function at index 0 in function_list
        is the default function which usually should be one that simply passes.
        e.g.
        def empty_function():
            pass
        
    Returns
    -------
    None
    
    Purpose
    -------
    Move the toon from waypoint to waypoint in the provided waypoint list.
    '''
    position_actual = glc.get_land_coords(swg_window_region)
    key_df = pd.DataFrame({'should_be_down':[False]*6, 'is_down':[False]*6}, index=['w','s','q','e','a','d'])
    for position_desired in waypoint_list:
        start_time = time.time()
        prev_position = [0, 0]
        stuck_timeout = 5
        while (not (position_desired[1] == position_actual[1] and position_desired[0] == position_actual[0])) and time.time() - start_time < stuck_timeout:
            # Update position_actual by taking a new screenshot
            position_actual = glc.get_land_coords(swg_window_region)
            # w
            key_df.loc['w']['should_be_down'] = (position_desired[1] > position_actual[1])
            # s
            key_df.loc['s']['should_be_down'] = (position_desired[1] < position_actual[1])
            # q                       
            key_df.loc['q']['should_be_down'] = (position_desired[0] < position_actual[0])
            # e
            key_df.loc['e']['should_be_down'] = (position_desired[0] > position_actual[0])
            # hold down the appropriate keys
            key_df = hold_down_keys(key_df)
            if not (prev_position[0] == position_actual[0] and prev_position[1] == position_actual[1]):
                start_time = time.time()
                prev_position = deepcopy(position_actual)
        if time.time() - start_time >= stuck_timeout:
            key_df = pd.DataFrame({'should_be_down':[False]*6, 'is_down':[False]*6}, index=['w','s','q','e','a','d'])
            key_df = hold_down_keys(key_df)
            raise Exception('Toon got stuck, timed out.')
        key_df.loc['w']['should_be_down'] = False
        key_df.loc['s']['should_be_down'] = False
        key_df.loc['q']['should_be_down'] = False
        key_df.loc['e']['should_be_down'] = False
        key_df = hold_down_keys(key_df)
        
        start_time = time.time()
        # Execute the function indexed by position_desired[3]
        function_list[position_desired[3]]()
        if not planning_mode:
            # Execute wait time in position_desired[2]. It includes the time 
            # taken to run the function in function_list.
            time.sleep(max(0, position_desired[2] - (time.time() - start_time)))