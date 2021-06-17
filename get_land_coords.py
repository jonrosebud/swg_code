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
import pydirectinput as pdi
sys.path.append(r'C:\Users\trose\Documents\python_packages')
from python_utils import windows_process_utils, file_utils
from copy import deepcopy
from PIL import Image


'''
land_coords_digit_csv_dir: str
    Directory containing csv files which each represent the matrix of a 
    particular digit. e.g. '0.csv', '1.csv', 'negative_sign.csv'.
    
land_coords_digit_csvs: list of str
    List of csv fpaths for the digit files.
    
digit_arr: 2D np.array
    The matrix that is stored in the csv file for a particular digit.
    
digit_fname: str
    The filename without path information or extension. e.g. '0', '1', 
    'negative_sign'.
    
land_coords_digit_dct: dict of 2D np.array
    Keys: '-', '0', '1', etc
    Values: The digit_arr for the corresponding key
    
Notes
-----
1. This is executed here, globally, so that the files only have to be loaded
    into the dictionary one time.
    
2. The digit_arr matrices which are stored in the csv files were gotten in the
    following way:
    1. Use the calibrate_window_position function to get the windows into
        position.
    2. Use a script to get the mouse coordinates of the screen when you hover
        over the upper-left and lower-right corner of the rectangle that will 
        be screenshotted (the rectangle that will enclose the x and y 
        coordinates of the in-game position). This is used to define region.
        You will refine the region coordinates later.
    3. Use the determine_region_coords function and look at the resultant image
        and csv file to alter the constants in the function to trim and fine-
        tune the region. Make sure that the region does not contain any white
        (non-zero) pixels except for those corresponding to a digit (or, that
        these non-zero, non-digit pixels can be trimmed out as is done in
        x_coords_arr and y_coords_arr).
    4. Use the outputted csv file to get the start and end indices of each digit
        and save that slice to a csv file without an index or column labels.
'''
land_coords_digit_csv_dir='land_coords_digit_dir'
land_coords_digit_csvs = file_utils.find(land_coords_digit_csv_dir, '*.csv')
land_coords_digit_dct = {}
for digit_csv in land_coords_digit_csvs:
    digit_arr = np.array(file_utils.read_csv(digit_csv)).astype(np.int)
    digit_fname = file_utils.fname_from_fpath(digit_csv)
    if digit_fname == 'negative_sign':
        land_coords_digit_dct['-'] = digit_arr
    else:
        land_coords_digit_dct[digit_fname] = digit_arr


def north_calibrate(swg_window, arrow_rect_csv_fpath='arrow_rect.csv'):
    '''
    calibrated_north: 2D np.array
    The matrix that is stored in the csv file for when the compass is facing north
    
    Returns
    -------
    None
        
    Purpose
    -------
    Rotate charater until facing north. Needed since w,s,q,e movements expect character to be facing north
        
    Notes
    -----
    1. atol may be large enough to get a false north reading, still calibrating
    2. the location being looked at is the little green arrow on the compass when it is facing north
    3. notice that 'a' is pressed after stopping rotating. this is because response time isnt fast enough to stop exactly at the top
    '''
    
    
    calibrated_north = np.array(file_utils.read_csv(arrow_rect_csv_fpath)).astype(np.int)
    # Define the region of the matrix corresponding to the in-game 
    # coordinates as shown in the minimap.
    atol=30
    rect = swg_window.rectangle()
    top = rect.top + 37
    left = rect.left + 940
    width = 7
    height = 3
    region = {'top': top, 'left': left, 'width': width, 'height': height}
    img_arr = take_screenshot_and_sharpen(swg_window, region=region, 
            sharpen_threshold=200, scale_to=255, sharpen=False)
    
    if np.allclose(img_arr, calibrated_north, atol=atol):
        return
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.press('s')
    pdi.keyUp('shift')
    pdi.keyUp('ctrl')
    start_time = time.time()
    while time.time() - start_time < 20 and not np.allclose(img_arr, calibrated_north, atol=atol):
        img_arr = take_screenshot_and_sharpen(swg_window, region=region, 
            sharpen_threshold=200, scale_to=255, sharpen=False)
        
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.press('s')
    pdi.keyUp('shift')
    pdi.keyUp('ctrl')
    pdi.press('a', presses=1)

def take_screenshot_and_sharpen(window, region, sharpen_threshold=200,
        scale_to=1, set_focus=True, sharpen=True):
    '''
    window: pywinauto.application.WindowSpecification
        A window object for a particular application.
        
    region: dict
        Defines the area of the screen that will be screenshotted.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
    sharpen_threshold: int
        Grayscale pictures have each pixel range from 0 to 255. However, we
        want to sharpen the image so there is no noise. Thus we only want 
        black and white (0 and 255 only) or 0 and 1 only. sharpen_threshold
        is the cutoff level above which, everything will be given the value
        of scale_to, and below which, everything will be given the value of 0.
        
    scale_to: int
        Grayscale pictures have each pixel range from 0 to 255. However, we
        want to sharpen the image so there is no noise. Thus we only want 
        black and white (0 and 255 only) or 0 and 1 only. Set scale_to to 255
        or 1 to accomplish this. Use 255 if you want to view the matrix as
        an image, or 1 if you want the math to be easier but dont need to
        look at the matrix.
        
    set_focus: bool
        True: Make sure the window has focus (is activated) before taking the
        screenshot.
        False: Take the screenshot without assuring focus because by some other
            means, I know the window is visible.
            
    sharpen: bool
        Whether to apply sharpen_threshold and scale_to.

    Returns
    -------
    img_arr: 2D np.array
        Matrix containing only values equal to 0 or scale_to which are the
        "sharpened" pixel values in matrix form of the screenshot taken in the
        given region.

    Purpose
    -------
    Take a screenshot of the provided region in the provided window, convert
    to a numpy array, grayscale it, and sharpen according to the threshold and
    scale_to provided.
    '''
    if set_focus and not window.has_focus():
        # Activate the window
        window.set_focus()
        time.sleep(0.02)
    with mss.mss() as sct:
        # Take the screenshot of just the in-game coordinates
        screenshot = sct.grab(region)
        # Convert to numpy array
        img_arr = deepcopy(np.asarray(screenshot))
    # Convert to Grayscale
    img_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGRA2GRAY)
    if sharpen:
        # Sharpen image
        img_arr[img_arr < sharpen_threshold] = 0
        img_arr[img_arr >= sharpen_threshold] = scale_to
    return img_arr


def determine_region_coords(swg_window, region_fpath='region.png', 
        csv_fpath='region.csv'):
    '''
    swg_window: pywinauto.application.WindowSpecification
        A window object for a particular swg instance.
        
    region_fpath: str
        Path where the screenshot of region will be saved as a picture file.
        
    csv_fpath: str
        Path where the matrix of the screenshot of region will be saved as a 
        csv file.

    Returns
    -------
    None.

    Purpose
    -------
    This is a helper function to use to help determine the coordinates of 
    bounding regions that you are interested in getting screenshots of. It
    takes a screenshot and saves the sharpened black/white image to a file
    as well as to a csv file. You can see the pixels and their values quite 
    clearly in the csv file.
    '''
    # Define the region of the matrix corresponding to the in-game 
    # coordinates as shown in the minimap.
    rect = swg_window.rectangle()
    top = rect.top + 37 # 29
    left = rect.left + 940
    width = 7
    height = 3
    region = {'top': top, 'left': left, 'width': width, 'height': height}
    img_arr = take_screenshot_and_sharpen(swg_window, region=region, 
            sharpen_threshold=200, scale_to=255, sharpen=False)
    
    img = Image.fromarray(img_arr)
    img.save(region_fpath)
    df = pd.DataFrame(img_arr)
    df.to_csv(csv_fpath)


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
        swg_process_df.sort_values(by='cpu_seconds', ascending=False, inplace=True)
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
            
        
def get_number_from_arr(line_arr):
    '''
    line_arr: 2D np.array
        This matrix must be the same height (number of rows) as the stored
        digit matrices in land_coords_digit_dct. line_arr contains some of the
        digit matrices in land_coords_digit_dct which will be read sequentially
        to get the overall (single) number.
        
    Returns
    -------
    digits: int
        The number as read from the line_arr.
    
    Purpose
    -------
    Given a matrix that contains digit matrices separated by columns of all
    0's, concatenate the digits (possibly including negative sign) in the
    order they appear to return the overall number represented by line_arr.
    
    Method
    ------
    Iterate through each column of line_arr until there's a column of not all 
    zeros. A non-zero summed column means we have found the column index, i,
    of the beginning of a new digit. Continue iterating through the columns
    with j until you find the first column after i that is all zeros. The
    slice in between is the matrix of one of the digits. Try each digit matrix
    until one of them matches. Append the digit to the overall digits string.
    Convert to a number at the end.
    
    Notes
    -----
    1. See docs for land_coords_digit_dct for more info on digit matrices.
    2. An alternative algorithm could be to use hard-coded slices as the
        target digits if they are the same every time regardless of which
        number occupies a particular position.
    '''
    digits = ''
    i = 0
    # Iterate through the columns of line_arr
    while i < line_arr.shape[1]:
        # If the ith col is not all zeros then we've found the beginning of
        # a digit.
        if np.sum(line_arr[:, i]) != 0:
            j = deepcopy(i)
            # Continue iterating through the columns of line_arr until you
            # find a column of all zeros which represents the space in between
            # digits and thus marks the end of the digit.
            while np.sum(line_arr[:, j]) != 0:
                j += 1
            # The digit we want to find a match to, target_digit, is the slice
            # from col i to col j.
            target_digit = line_arr[:, i : j].astype(np.int)
            # Increase i so it is starting on a column of all zeros and thus
            # ready to find the next digit.
            i += j - i
            # Iterate through all the stored digit matrices to see if one
            # matches.
            for digit_key, digit_arr in land_coords_digit_dct.items():
                # If the digit_arr doesn't have the same shape as target_digit,
                # it can't be the target digit so skip it.
                if digit_arr.shape != target_digit.shape:
                    continue
                # If it's a perfect match, then we know which digit the
                # target_digit is so append the digit string to the overall
                # string.
                if np.all(digit_arr == target_digit):
                   digits += digit_key
        i += 1
    # Convert the digit string into a number.
    return int(digits)
    
        
def get_land_coords(swg_window):
    '''
    swg_window: pywinauto.application.WindowSpecification
        A window object for a particular swg instance.
        
    Returns
    -------
    coords: list of int with length 2
        The first and second elements correspond to the x and y coordinates
        that your toon is in-game.
        
    Purpose
    -------
    Get the x and y coordinates that your toon is in-game which is displayed
    in the minimap on the screen.
    
    Method
    ------
    Take a screenshot of the small region of the screen showing the in-game
    coordinates. Parse this image for the numerical values using digit
    matrices (see get_number_from_arr docs)
    '''
    # Define the region of the matrix corresponding to the in-game 
    # coordinates as shown in the minimap.
    rect = swg_window.rectangle()
    top = rect.top + 166
    left = rect.left + 867
    width = 150
    height = 8
    region = {'top': top, 'left': left, 'width': width, 'height': height}
    img_arr = take_screenshot_and_sharpen(swg_window, region=region, 
            sharpen_threshold=200, scale_to=1)
    # Get the region of the coordinate matrix that just corresponds to the first
    # (x) number.
    x_coord_arr = img_arr[:, 6:44]
    # Get the region of the coordinate matrix that just corresponds to the
    # second (y) number.
    y_coord_arr = img_arr[:, 106:144]
    # Parse the matrices for the numbers.
    x_coord = get_number_from_arr(x_coord_arr)
    y_coord = get_number_from_arr(y_coord_arr)
    return [x_coord, y_coord]
        
        
def main():
    swg_windows = get_swg_windows()
    calibrate_window_position(swg_windows)
    coords = get_land_coords(swg_windows[0])
    print(coords)
    
    

if __name__ == '__main__':
    #main()
    swg_windows = get_swg_windows()
    #determine_region_coords(swg_windows[0], region_fpath='arrow_region.png', 
    #    csv_fpath='arrow_region.csv')
    north_calibrate(swg_windows[0], arrow_rect_csv_fpath='arrow_rect.csv')
