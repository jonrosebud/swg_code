# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 21:09:28 2021

@author: trose
"""
import pydirectinput as pdi
import time
import pyautogui as pag
import mss
import cv2
import numpy as np
from copy import deepcopy


def take_screenshot(window, region, set_focus=True):
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
        
    set_focus: bool
        True: Make sure the window has focus (is activated) before taking the
            screenshot.
        False: Take the screenshot without assuring focus because by some other
            means, I know the window is visible.

    Returns
    -------
    img_arr: 3D np.array
        Matrix containing pixel values in matrix form of the screenshot taken 
        in the given region. Dimensions are B,G,R -> 0,1,2 index.

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
    return img_arr


def take_grayscale_screenshot(window, region, sharpen_threshold=200,
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
    img_arr = take_screenshot(window, region, set_focus=set_focus)
    # Convert to Grayscale
    img_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGRA2GRAY)
    if sharpen:
        # Sharpen image
        img_arr[img_arr < sharpen_threshold] = 0
        img_arr[img_arr >= sharpen_threshold] = scale_to
    return img_arr


def click(coords=None, button='left', start_delay=0.5, return_delay=1, presses=1, interval_delay=0.0, window=None, region=None, coords_idx=None, activate_window=True):
    '''
    Parameters
    ----------
    coords: list of int or None
        [x,y] coordinates on the screen to click on.
        If None, use current coordinates (unless coords_idx is not None, then use coords_idx for relative coordinates)
        
    button: str
        A string telling pdi.mouseDown which mouse button to click. The default is 'left'.
        
    start_delay: float
        An amount of time to sleep before clicking.
        
    return_delay: float
        An amount of time to sleep after clicking.
        
    presses: int
        Number of times to click the button.
        
    interval_delay: float
        Time to delay in between clicks
        
    window: pywinauto.application.WindowSpecification
        A window object. Use it in combination with coords_idx to click on.
        
    region: dict
        Defines the area of the screen that will be screenshotted if img_arr is None.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
    coords_idx: list of int or None
        [row, col] swg_window img_arr matrix indices of the location to click.
        
    activate_window: bool
        True: if window is not None, call window.set_focus()
        False: do nothing

    Returns
    -------
    None

    Purpose
    -------
    Simulate a mouse click on the provided coordinates. This function builds in an ability to sleep a certain amount of time before and after the click.
    If window and coords_idx are provided, then the row, col of window will be used to determine the coords.
    '''
    time.sleep(start_delay)
    if window is not None and activate_window:
        window.set_focus()
    if coords_idx is not None:
        if window is not None and region is None:
            rect = window.rectangle()
            height_of_window_header = 26
            # The screen part to capture
            region = {'top': rect.top + height_of_window_header, 'left': rect.left, 'width': rect.width(), 'height': rect.height() - height_of_window_header}
        if region is not None:
            coords = [region['left'] + coords_idx[1], region['top'] + coords_idx[0]]
    if coords is not None:
        pdi.moveTo(coords[0], coords[1])
    for _ in presses:
        pdi.mouseDown(button=button)
        pdi.mouseUp(button=button)
        time.sleep(interval_delay)
    time.sleep(max(0, return_delay - interval_delay))
    
    
def press(keys, presses=1, start_delay=0.0, return_delay=0.0):
    '''
    Parameters
    ----------
    keys: list of str
        List of keys.
        e.g.
        ['shift', 'a']

    Returns
    -------
    None

    Purpose
    -------
    This function enables you to press any number of keys in combination. i.e. you can hold down alt, ctrl, shift and then press a key using this function.
    '''
    time.sleep(start_delay)
    for _ in range(presses):
        for key in keys:
            pdi.keyDown(key)
        for key in keys[::-1]:
            pdi.keyUp(key)
    time.sleep(return_delay)
    
    
def chat(string, start_delay=0.2, return_delay=0.1, interval_delay=0.1):
    '''
    Parameters
    ----------
    string: str
        String to type into the swg chat box.

    Returns
    -------
    None

    Purpose
    -------
    Type a string into the swg chat box and press enter.
    '''
    time.sleep(start_delay)
    pdi.press('enter')
    time.sleep(interval_delay)
    pag.write(string, interval=0.02)
    time.sleep(interval_delay)
    pdi.press('enter')
    time.sleep(return_delay)
    
    
def find_arr_on_region(search_arr, region=None, img_arr=None, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False):
    '''
    Parameters
    ----------
    search_arr: np.array, shape (n, m)
        Matrix that you are looking for within img_arr.
        
    region: dict
        Defines the area of the screen that will be screenshotted if img_arr is None.
        Keys: 'top', 'left', 'width', 'height'
        Values: int
        'top': topmost (y) coordinate
        'left': leftmost (x) coordinate
        'width': number of pixels wide
        'height': number of pixels tall
        
    img_arr: np.array, shape: (1030, 771) or None
        Screenshot matrix of the swg_window (with top border removed) which has been Grayscaled and sharpened with the same cutoff as used in arr_dct.
        If None, a new screenshot will be taken by this function.
        
    iterate_row_then_col: bool
        True: Search through img_arr for search_arr by doing the following: for each row, sweep over all columns
        False: Search through img_arr for search_arr by doing the following: for each column, sweep over all rows
        
    start_row: int
        The row to start searching from. Rows before this one will not be searched.
        
    start_col: int
        The column to start searching from. Columns before this one will not be searched.
        
    iterate_row_forwards: bool
        True: Search by iterating over rows sequentially ascending.
        False: Search by iterating over rows sequentially descending.
        
    iterate_col_forwards: bool
        True: Search by iterating over cols sequentially ascending.
        False: Search by iterating over cols sequentially descending.
        
    fail_gracefully: bool
        True: If the desired matrix is not found, return None, None
        False: If the desired matrix is not found, raise an Exception stating this.

    Returns
    -------
    found_idx, img_arr
    
    found_idx: list of int or None
        [row, col] giving the location in img_arr of the top left corner of the found array matching that for search_arr.
        If None, this function could not find the item on the screen.
        
    img_arr: np.array, shape: (1030, 771)
        Screenshot matrix of the swg_window (with top border removed) which if gotten by this function has been Grayscaled and sharpened with the same cutoff as used in inventory_dct.
        
        
    Purpose
    -------
    Take a screenshot and find the matrix given by search_arr on that screenshot matrix (after grayscaling and sharpening using the same threshold).

    Notes
    -----
    1. Inventory must be open already, and the description section must be visible.
    '''
    if img_arr is None:
        # sharpen_threshold of 130 is for inventory_dct
        img_arr = take_grayscale_screenshot(region, sharpen_threshold=130,
                scale_to=255, sharpen=True)

    if iterate_row_forwards:
        row_direction = 1
    else:
        row_direction = -1
    if iterate_col_forwards:
        col_direction = 1
    else:
        col_direction = -1
    if iterate_row_then_col:
        for i in range(start_row, img_arr.shape[0] - search_arr.shape[0])[::row_direction]:
            for j in range(start_col, img_arr.shape[1] - search_arr.shape[1])[::col_direction]:
                if np.all(img_arr[i : i + search_arr.shape[0], 
                        j : j + search_arr.shape[1]] ==
                        search_arr):
                    
                    return [i, j], img_arr
        if not fail_gracefully:
            raise Exception('Could not find search_arr in img_arr')
        return None, None
    else:
        for j in range(start_col, img_arr.shape[1] - search_arr.shape[1])[::col_direction]:
            for i in range(start_row, img_arr.shape[0] + search_arr.shape[0])[::row_direction]:
                if np.all(img_arr[i : i + search_arr.shape[0], 
                        j : j + search_arr.shape[1]] ==
                        search_arr):
                    
                    return [i, j], img_arr
        if not fail_gracefully:
            raise Exception('Could not find search_arr in img_arr')
        return None, None
