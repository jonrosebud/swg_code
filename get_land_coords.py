# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 10:30:21 2021

@author: trose
"""
import time
import mss
import cv2
import numpy as np
import pandas as pd
import pywinauto as pwa
from config_utils import Instruct
import socket
config_fpath = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config = Instruct(config_fpath)
config.get_config_dct()
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
sys.path.append(r"" + python_utils_path)
import pydirectinput_tmr as pdi
from python_utils import windows_process_utils, file_utils
os = file_utils.os
from copy import deepcopy
from PIL import Image
import swg_window_management as swm
import swg_utils

top_north = config.config_dct['main']['top_north']
left_north = config.config_dct['main']['left_north']
ground_coords_top = config.config_dct['main']['ground_coords_top'] 
ground_coords_left = config.config_dct['main']['ground_coords_left'] 
use_generic_arrow = config.get_value('main', 'use_generic_north_arrow', desired_type=bool, default_value=True)

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
    digit_arr = file_utils.read_csv(digit_csv, dtype=int)
    digit_fname = file_utils.fname_from_fpath(digit_csv)
    if digit_fname == 'negative_sign':
        land_coords_digit_dct['-'] = digit_arr
    else:
        land_coords_digit_dct[digit_fname] = digit_arr
        
        
def north_calibrate(swg_window_region, arrow_rect_csv_fpath='arrow_rect.csv'):
    '''
    Parameters
    ----------
    swg_window_region: dict
        Defines a rectangular area of the screen corresponding to the swg_window.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
    arrow_rect_csv_fpath: str
        File containing array of a portion of the arrow that is pointing north on
        your in-game radar. It should be gotten with take_screenshot_and_sharpen with 
        sharpen_threshold and scale_to set to what those settings are when getting
        img_arr below.

    Returns
    -------
    None
    
    Purpose
    -------
    Rotate the toon to be facing North in-game. This allows the functions to work
    that rely on knowing that strafing left means going west, for instance.
    '''
    if use_generic_arrow is not True:
        arrow_rect_csv_fpath = os.path.abspath(arrow_rect_csv_fpath)
        arrow_dir = os.path.dirname(arrow_rect_csv_fpath)
        arrow_fname = socket.gethostname() + '_' + file_utils.fname_from_fpath(arrow_rect_csv_fpath)
        arrow_rect_csv_fpath = os.path.join(arrow_dir, arrow_fname + '.csv')
    calibrated_north = file_utils.read_csv(arrow_rect_csv_fpath, dtype=int)
    # Define the region of the matrix corresponding to the in-game 
    # coordinates as shown in the minimap.
    atol=30
    top = swg_window_region['top'] + top_north
    left = swg_window_region['left'] + left_north
    width = 7
    height = 3
    region = {'top': top, 'left': left, 'width': width, 'height': height}
    img_arr = swg_utils.take_grayscale_screenshot(window=None, region=region, sharpen_threshold=200,
            scale_to=255, set_focus=False, sharpen=False)
    
    if np.allclose(img_arr, calibrated_north, atol=atol):
        return
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.press('s')
    pdi.keyUp('shift')
    pdi.keyUp('ctrl')
    while not np.allclose(img_arr, calibrated_north, atol=atol):
        img_arr = swg_utils.take_grayscale_screenshot(window=None, region=region, sharpen_threshold=200,
                scale_to=255, set_focus=False, sharpen=False)
        
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.press('s')
    pdi.keyUp('shift')
    pdi.keyUp('ctrl')
    pdi.press('a', presses=1)


def determine_region_coords(swg_window_region, region_fpath='region.png', 
        csv_fpath='region.csv'):
    '''
    swg_window_region: dict
        Defines a rectangular area of the screen corresponding to the swg_window.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
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
    top = swg_window_region['top'] + ground_coords_top
    left = swg_window_region['left'] + ground_coords_left
    width = 150
    height = 8
    region = {'top': top, 'left': left, 'width': width, 'height': height}
    img_arr = swg_utils.take_grayscale_screenshot(window=None, region=region, sharpen_threshold=200,
            scale_to=255, set_focus=False, sharpen=True)
    
    img = Image.fromarray(img_arr)
    img.save(region_fpath)
    df = pd.DataFrame(img_arr)
    df.to_csv(csv_fpath, index=False, index_label=None, header=False)


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
    
        
def get_land_coords(swg_window_region):
    '''
    swg_window_region: dict
        Defines a rectangular area of the screen corresponding to the swg_window.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
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
    top = swg_window_region['top'] + ground_coords_top
    left = swg_window_region['left'] + ground_coords_left
    width = 150
    height = 8
    region = {'top': top, 'left': left, 'width': width, 'height': height}
    img_arr = swg_utils.take_grayscale_screenshot(window=None, region=region, sharpen_threshold=200,
            scale_to=1, set_focus=False, sharpen=True)
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
    swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
    swg_window = swm.swg_windows[swg_window_i]
    swg_window_region = swm.swg_window_regions[swg_window_i]
    coords = get_land_coords(swg_window_region)
    print(coords)
    
    

if __name__ == '__main__':
    #main()
    #swm.calibrate_window_position(swm.swg_windows)
    swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
    swg_window = swm.swg_windows[swg_window_i]
    swg_window_region = swm.swg_window_regions[swg_window_i]
    swg_window.set_focus()
    time.sleep(0.5)
    #determine_region_coords(swg_window_region, region_fpath='region.png', 
    #    csv_fpath='region.csv')
    north_calibrate(swg_window_region, arrow_rect_csv_fpath='arrow_rect.csv')
