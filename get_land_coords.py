# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 10:30:21 2021

@author: trose
"""
import sys
import time
import mss
import cv2
import numpy as np
import pandas as pd
import pywinauto as pwa
sys.path.append(r'C:\Users\trose\Documents\python_packages')
from python_utils import windows_process_utils
from copy import deepcopy
from PIL import Image


def get_swg_windows(swg_process_df):
    '''
    swg_process_df: pd.DataFrame
        Dataframe only containing rows of swg instances. The important column
        is 'process_id' which contains the Windows PID of the particular 
        instance. This df is gotten by windows_process_utils.get_passing_df
        so see that function for more info.
        
    Returns
    -------
    swg_windows: list of pywinauto.application.WindowSpecification
        Each element is a window object for a particular swg instance.
        
    Purpose
    -------
    Get the window object for each swg instance which can be used to manipulate
    and give focus to the window.
    '''
    swg_windows = []
    for i, process_id in enumerate(swg_process_df['process_id']):
        # Initialize an Application object to be connected to the process_id
        # of this swg instance.
        app = pwa.application.Application().connect(process=int(process_id))
        # Find the handle of the window for this swg instance.
        handle = pwa.findwindows.find_windows(
                title='Star Wars Galaxies', 
                process=int(process_id))[0]
        
        # Finally, we have the window object.
        window = app.window(handle=handle)
        swg_windows.append(window)
    return swg_windows
    

def calibrate_window_position(swg_windows, 
        desired_position_of_windows=None,
        desired_size_of_windows=None):
    
    '''
    swg_windows: list of pywinauto.application.WindowSpecification
        Each element is a window object for a particular swg instance.
    
    desired_position_of_windows: list of list of int with shape (n,2) or None
        n is the number of simultaneous instances of swg. The position refers
        to the top left corner of the window. Each row corresponds to a 
        different window. The first element of each row is the desired x 
        coordinate and the second element is the desired y coordinate.
        
        e.g. [[0, 0], [1030, 0], [2060, 0]]
        would put them next to each other along the top of the screen.
        
        If None is passed, then the default scheme is used which is putting one
        of the windows at (0,0) and then putting the next window's left side 
        adjacent to the first window's right side and then putting the next
        window adjacent to the right side of the second window.
        
    desired_size_of_windows: list of int with length 2, or None
        The desired width and height that the window should be scaled to is
        given by the first and second elements of desired_size_of_windows, 
        respectively.
        
        e.g. [1030, 797]
        would scale each swg window to be 1030 wide and 797 tall
        
        If None is passed then no change to the window's dimensions will be
        made.
        
    Returns
    -------
    None
        
    Purpose
    -------
    Move and/or resize the swg windows so that their position is the same every
    time so that constants passed into functions such as regions to get a
    screenshot are correct.
        
    Notes
    -----
    1. Windowed instances of swg should already be running.
    2. This function does not yet check for whether there is enough room to
        carry out the default window positioning scheme.
    '''
    if desired_size_of_windows is None:
        # By default, use the width and height of the first instance
        rect = swg_windows[0].rectangle()
        desired_size_of_windows = [rect.width(), rect.height()]
    if desired_position_of_windows is None:
        # By default, align the windows along the top of the screen and 
        # adjacent to the previous window.
        desired_position_of_windows = []
        for i, swg_window in enumerate(swg_windows):
            if i == 0:
                desired_position_of_windows.append([0, 0])
            else:
                rect = swg_windows[i - 1].rectangle()
                desired_position_of_windows.append([rect.right, rect.top])
    # Move and resize the windows.
    for i, swg_window in enumerate(swg_windows):
        swg_window.move_window(
                x=desired_position_of_windows[i][0], 
                y=desired_position_of_windows[i][1], 
                width=desired_size_of_windows[0],
                height=desired_size_of_windows[1])
            

def take_screenshot(swg_windows):
    for i, swg_window in enumerate(swg_windows):
        with mss.mss() as sct:
            # Activate the window
            swg_window.set_focus()
            time.sleep(1)
            # The screen part to capture
            rect = swg_window.rectangle()
            top = rect.top + 166
            left = rect.left + 867
            width = 150
            height = 8
            region = {'top': top, 'left': left, 'width': width, 'height': height}
            # Grab the data
            start_time = time.time()
            screenshot = sct.grab(region)
            img_arr = deepcopy(np.asarray(screenshot))
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGRA2GRAY)
        img_arr[img_arr < 200] = 0
        img_arr[img_arr >= 200] = 1
        x_coord_arr = img_arr[:, 6:44]
        y_coord_arr = img_arr[:, 106:144]
        
        break

        
def main():
    vars_df = windows_process_utils.get_vars_df(image_name='SwgClient_r.exe')
    swg_process_df = windows_process_utils.get_passing_df(vars_df)
    swg_process_df.sort_values(by='cpu_seconds', ascending=False, inplace=True)
    swg_windows = get_swg_windows(swg_process_df)
    #calibrate_window_position(swg_windows)
    take_screenshot(swg_windows)
    
    

if __name__ == '__main__':
    main()