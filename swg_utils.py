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
from config_utils import Instruct
import socket
config_fpath = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config = Instruct(config_fpath)
config.get_config_dct()
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils, list_utils
os = file_utils.os


def get_int_from_line_arr(line_arr, digit_dct):
    number = ''
    col = 0
    digit_found = True
    while col < line_arr.shape[1] and digit_found:
        for digit, digit_arr in digit_dct.items():
            digit_found = np.all(line_arr[:,col : col + digit_arr.shape[1]] == digit_arr)
            if digit_found:
                number += str(digit)
                col += digit_arr.shape[1] + 1
                break
    return int(number)
            

def save_to_csv(img_arr, output_dir, fname):
    '''
    img_arr: np.array, shape (>= 2, >= 1) or list of list
        Matrix of RGB or grayscale values used to represent an image. Gotten
        from the grab function in the mss library or similar screenshot function.
        
    output_dir: str
        Path of the directory that the file will be output to.
        
    fname: str
        File name (do not include extension).
        
    Returns
    -------
    None
    
    Purpose
    -------
    Save the img_arr matrix to a csv file.
    '''
    lst = list(map(list, img_arr))
    csv_path = os.path.join(output_dir, fname + '.csv')
    file_utils.write_rows_to_csv(csv_path, lst)
    
    
def save_BGR_to_csvs(img_arr, output_dir, fname):
    colors = ['B', 'G', 'R']
    for i in range(3):
        save_to_csv(img_arr[:,:,i], output_dir, fname + colors[i])


def take_screenshot(window=None, region=None, set_focus=False):
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


def take_grayscale_screenshot(window=None, region=None, sharpen_threshold=200,
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

def find_pixels_on_BGR_arr(img_arr, b=None, g=None, r=None, 
            b_lower_bound=0, b_upper_bound=255, g_lower_bound=0, 
            g_upper_bound=255, r_lower_bound=0, r_upper_bound=255, start_row=0,
            end_row=None, start_col=0, end_col=None, return_as_set=False):
    
    if end_row is None:
        end_row = img_arr[:,:,0].shape[0]
    if end_col is None:
        end_col = img_arr[:,:,0].shape[1]
    b_arr = img_arr[start_row : end_row, start_col : end_col, 0]
    g_arr = img_arr[start_row : end_row, start_col : end_col, 1]
    r_arr = img_arr[start_row : end_row, start_col : end_col, 2]
    if b is None:
        if g is None:
            if r is None:
                where_arr = np.where((b_arr >= b_lower_bound) &
                                   (b_arr <= b_upper_bound) &
                                   (g_arr >= g_lower_bound) & 
                                   (g_arr <= g_upper_bound) &
                                   (r_arr >= r_lower_bound) & 
                                   (r_arr <= r_upper_bound))
            else:
                where_arr = np.where((b_arr >= b_lower_bound) &
                                   (b_arr <= b_upper_bound) &
                                   (g_arr >= g_lower_bound) & 
                                   (g_arr <= g_upper_bound) &
                                   (r_arr == r))
        else:
            if r is None:
                where_arr = np.where((b_arr >= b_lower_bound) &
                                   (b_arr <= b_upper_bound) &
                                   (g_arr == g) &
                                   (r_arr >= r_lower_bound) & 
                                   (r_arr <= r_upper_bound))
            else:
                where_arr = np.where((b_arr >= b_lower_bound) &
                                   (b_arr <= b_upper_bound) &
                                   (g_arr == g) &
                                   (r_arr == r))
    else:
        if g is None:
            if r is None:
                where_arr = np.where((b_arr == b) &
                                   (g_arr >= g_lower_bound) & 
                                   (g_arr <= g_upper_bound) &
                                   (r_arr >= r_lower_bound) & 
                                   (r_arr <= r_upper_bound))
            else:
                where_arr = np.where((b_arr == b) &
                                   (g_arr >= g_lower_bound) & 
                                   (g_arr <= g_upper_bound) &
                                   (r_arr == r))
        else:
            if r is None:
                where_arr = np.where((b_arr == b) &
                                   (g_arr == g) &
                                   (r_arr >= r_lower_bound) & 
                                   (r_arr <= r_upper_bound))
            else:
                where_arr = np.where((b_arr == b) &
                                   (g_arr == g) &
                                   (r_arr == r))
    if return_as_set:
        return set(tuple(zip(where_arr[0], where_arr[1])))
    else:
        return where_arr


def click(coords=None, button='left', start_delay=0.5, return_delay=1, presses=1, interval_delay=0.02, move_duration=0.1, duration=0.02, window=None, region=None, coords_idx=None, activate_window=True):
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
    if coords is None:
        coords = [None, None]
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
    pdi.click_fast(x=coords[0], y=coords[1], clicks=presses, interval=interval_delay, move_duration=move_duration, duration=duration, button=button)
    time.sleep(max(0, return_delay - interval_delay * presses - move_duration))
    
    
def moveTo(coords=None, start_delay=0.0, return_delay=0.0, move_duration=0.1, window=None, region=None, coords_idx=None):
    if coords is None:
        coords = [None, None]
    time.sleep(start_delay)
    if coords_idx is not None:
        if window is not None and region is None:
            rect = window.rectangle()
            height_of_window_header = 26
            # The screen part to capture
            region = {'top': rect.top + height_of_window_header, 'left': rect.left, 'width': rect.width(), 'height': rect.height() - height_of_window_header}
        if region is not None:
            coords = [region['left'] + coords_idx[1], region['top'] + coords_idx[0]]
    pdi.moveTo_fast(x=coords[0], y=coords[1], move_duration=move_duration)
    time.sleep(max(0, return_delay - move_duration))
    
    
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
    
    
def find_arr_on_region(search_arr, region=None, img_arr=None, start_row=0, start_col=0, end_row=None, end_col=None, fail_gracefully=False, sharpen_threshold=130):
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
        Screenshot matrix of the swg_window (with top border removed) which has been Grayscaled and sharpened with the same cutoff as your search_arr
        If None, a new screenshot will be taken by this function.
        
    start_row: int
        The row to start searching from. Rows before this one will not be searched.
        
    start_col: int
        The column to start searching from. Columns before this one will not be searched.
            
    end_row: int
        The row to end searching on. Rows after this one will not be searched.
        
    end_col: int
        The column to end searching on. Columns after this one will not be searched.
        
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
    '''
    if img_arr is None:
        # sharpen_threshold of 130 is for inventory_dct
        img_arr = take_grayscale_screenshot(region=region, sharpen_threshold=sharpen_threshold,
                scale_to=255, sharpen=True, set_focus=False)

    if end_row is None:
        end_row = img_arr.shape[0] - search_arr.shape[0] - 1
    if end_col is None:
        end_col = img_arr.shape[1] - search_arr.shape[1] - 1
    end_row = min(img_arr.shape[0] - search_arr.shape[0] - 1, end_row)
    end_col = min(img_arr.shape[1] - search_arr.shape[1] - 1, end_col)
    end_row = max(end_row, 0)
    end_col = max(end_col, 0)
    search_where_mat = list_utils.where_mat(search_arr != 0)
    offset_idx = search_where_mat.sum(axis=1).argmin()
    min_row, min_col = search_where_mat[offset_idx]
        
    where_mat = list_utils.where_mat(img_arr != 0)
    where_mat[:,0] = where_mat[:,0] - min_row
    where_mat[:,1] = where_mat[:,1] - min_col
    # Negative rows or cols are invalid so remove those rows that have any negative numbers        
    where_mat = where_mat[(where_mat >= 0).all(axis=1),:]
    # remove rows and cols that are not in between start_row, end_row; start_col, end_col
    where_mat = where_mat[(
            (where_mat[:,0] >= start_row) & (where_mat[:,0] <= end_row) &
            (where_mat[:,1] >= start_col) & (where_mat[:,1] <= end_col)),:]
    # We now have a set of valid indices to start our search from.
    for i, j in where_mat:
        if np.all(img_arr[i : i + search_arr.shape[0], 
                j : j + search_arr.shape[1]] ==
                search_arr):
            
            return [i, j], img_arr
    if not fail_gracefully:
        raise Exception('Could not find search_arr in img_arr')
    return None, None


def get_search_arr(fname, dir_path='.', mask_int=None):
    '''
    Parameters
    ----------
    fname: str
        File name without extension or folder prefix
        
    dir_path: str
        Directory that the file can be found in. The default is '.'.
        
    mask_int: int or None
        Int to use in a masked array. The default is None: do not mask the array.
        e.g.
        mask_int=0 then all 0's in the search array will be masked (not included in the search).

    Returns
    -------
    search_arr: np.array or np.ma.array
        Search array or masked search array.

    Purpose
    -------
    Read in a csv file containing a search array and mask it if desired. Masking
    is useful if something could appear behind the search array and thus making 
    the match impossible without a masked search array.
    '''
    csv_fpath = os.path.join(dir_path, fname + '.csv')  
    search_arr = file_utils.read_csv(csv_fpath, dtype=int)
    if mask_int is not None:
        return np.ma.masked_where(search_arr == mask_int, search_arr)
    return search_arr


def empty_function():
    pass


def run_recorded_key_presses(recorded_key_presses, function_list=[empty_function], reverse_function_list=[empty_function], round_trip=False):
    '''
    recorded_key_presses: list
        [[key, duration, function_idx],...,[key, duration, function_idx]]

    Returns
    -------
    None

    Purpose
    -------
    Execute a list of recorded key presses. Hold each key down for as long
    as specified in duration.
    '''
    for key, duration, function_idx in recorded_key_presses:
        pdi.press_key_fast(key, duration=duration)
        function_list[function_idx]()
    if round_trip:
        reverse_dct = {'a':'d','d':'a','q':'e','e':'q','w':'s','s':'w'}
        for key, duration, function_idx in recorded_key_presses[::-1]:
            pdi.press_key_fast(reverse_dct[key], duration=duration)
            reverse_function_list[function_idx]()