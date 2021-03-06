# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 14:32:22 2021
@author: trose
"""
from config_utils import Instruct
import socket, os
config_fpath = os.path.join('..', 'swg_config_file_for_' + socket.gethostname() + '.conf')
config = Instruct(config_fpath)
config.get_config_dct()
import socket
import sys
python_utils_path = config.get_value('main', 'python_utils_path', desired_type=str, required_to_be_in_conf=False, default_value='.')
sys.path.append(r"" + python_utils_path)
try:
    import pywinauto as pwa
except:
    import pywinauto as pwa
from python_utils import windows_process_utils, file_utils, list_utils
import mss
from copy import deepcopy
import numpy as np
import subprocess
git_path = config.get_value('main', 'git_path', desired_type=str, required_to_be_in_conf=False, default_value='.')
sys.path.append(r"" + git_path)
top_border_height = config.get_value('main', 'top_border_height', desired_type=int, required_to_be_in_conf=False, default_value=26)
side_border_width = config.get_value('main', 'side_border_width', desired_type=int, required_to_be_in_conf=False, default_value=0)
import time


def wait_until_window_active(window, interval=3.5, return_delay=3.5):
    '''
    Parameters
    ----------
    window: pywinauto.application.WindowSpecification
        Window object
        
    interval: float
        Amount of time to sleep in between checks of whether window is active yet.
        
    return_delay: float
        Amount of time to sleep after window is active and before returning.

    Purpose    
    -------
    Wait until a window becomes active to continue.
    '''
    while not window.is_active():
        time.sleep(interval)
    time.sleep(return_delay)
        

def get_swg_windows(swg_process_df=None):
    '''
    swg_process_df: pd.DataFrame or None
        Dataframe only containing rows of swg instances. The important column
        is 'process_id' which contains the Windows PID of the particular 
        instance. This df is gotten by windows_process_utils.get_passing_df
        so see that function for more info.
        
        If None, then swg_process_df is gotten automatically for you.
        
    Returns
    -------
    swg_windows: list of pywinauto.application.WindowSpecification
        Each element is a window object for a particular swg instance.
        
    Purpose
    -------
    Get the window object for each swg instance which can be used to manipulate
    and give focus to the window.
    
    Notes
    -----
    1. Windowed instances of swg should already be running.
    '''
    if swg_process_df is None:
        vars_df = windows_process_utils.get_vars_df(image_name='SwgClient_r.exe')
        swg_process_df = windows_process_utils.get_passing_df(vars_df)
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
        swg_windows.append([window, window.rectangle().left])
    swg_windows = list_utils.sort_list_by_col(swg_windows, 1)
    swg_windows = [swg_window for swg_window, left in swg_windows]
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
        
        e.g. [[5, 5], [1040, 5], [2075, 5]]
        would put them next to each other along the top of the screen.
        
        If None is passed, then the default scheme is used which is putting one
        of the windows at (5,5) and then putting the next window's left side 
        adjacent to the first window's right side (offset by 5 pixels to the 
        right) and then putting the next window adjacent to the right side of 
        the second window (again offest by 5 pixels to the right).
        
    desired_size_of_windows: list of int with length 2, or None
        The desired width and height that the window should be scaled to is
        given by the first and second elements of desired_size_of_windows, 
        respectively. See Notes for caveat.
        
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
    3. While the size of the window will be made equal to the desired size,
        the actual size did not change such that the original rectangle will
        be the only interactable area.
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
                desired_position_of_windows.append([5, 5])
            else:
                desired_position_of_windows.append([desired_position_of_windows[-1][0] + desired_size_of_windows[0] + 5, desired_position_of_windows[-1][1]])
    # Move and resize the windows.
    for i, swg_window in enumerate(swg_windows):
        swg_window.move_window(
                x=desired_position_of_windows[i][0], 
                y=desired_position_of_windows[i][1], 
                width=desired_size_of_windows[0],
                height=desired_size_of_windows[1])
        
        
def take_screenshot(region):
    '''
    region: dict
        Defines the area of the screen that will be screenshotted.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
    Returns
    -------
    img_arr: 3D np.array
        Matrices containing BGR data. img_arr[:,:,0] is the matrix B, 
        img_arr[:,:,1] is the matrix G, and img_arr[:,:,2] is the matrix R.
    Purpose
    -------
    Take a screenshot of the provided region in the provided window, convert
    to a numpy array, and return this array.
    '''
    with mss.mss() as sct:
        # Take the screenshot of just the in-game coordinates
        screenshot = sct.grab(region)
        # Convert to numpy array
        img_arr = deepcopy(np.asarray(screenshot))
    return img_arr


def get_swg_window_regions(swg_windows):
    swg_window_regions = []
    for swg_window_i in range(len(swg_windows)):
        rect = swg_windows[swg_window_i].rectangle()
        # The screen part to capture
        region = {'top': rect.top + top_border_height, 'left': rect.left + side_border_width, 'width': rect.width() - 2 * side_border_width, 'height': rect.height() - top_border_height}
        swg_window_regions.append(region)
    return swg_window_regions

        
def main():
    calibrate_window_position(swg_windows)
    
swg_windows = get_swg_windows()
swg_window_regions = get_swg_window_regions(swg_windows)
if __name__ == '__main__':
    main()