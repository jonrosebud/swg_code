# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 21:09:28 2021

@author: trose
"""

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
import autoit as ait
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import pydirectinput_tmr as pdi
top_border_height = config.get_value('main', 'top_border_height', desired_type=int, required_to_be_in_conf=False, default_value=26)
side_border_width = config.get_value('main', 'side_border_width', desired_type=int, required_to_be_in_conf=False, default_value=0)


def get_int_from_line_arr(line_arr, digit_dct, fail_gracefully=False):
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
    try:
        return int(number)
    except Exception as e:
        if fail_gracefully:
            return None
        else:
            raise e
            

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
            end_row=None, start_col=0, end_col=None, return_as_set=False,
            return_as_rect_arr=False, fail_gracefully=False):
    
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
    if len(where_arr[0]) == 0:
        if fail_gracefully:
            return None
        else:
            raise Exception('Could not find pixels on img_arr.')
    if return_as_set:
        return set(tuple(zip(where_arr[0], where_arr[1])))
    elif return_as_rect_arr:
        return np.array(tuple(zip(where_arr[0], where_arr[1])))
    else:
        return where_arr


def click(coords=None, button='left', start_delay=0.5, return_delay=1, presses=1, interval_delay=0.02, move_speed=5, duration=0.02, window=None, region=None, coords_idx=None, activate_window=True):
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
            # The screen part to capture
            region = {'top': rect.top + top_border_height, 'left': rect.left + side_border_width, 'width': rect.width() - 2 * side_border_width, 'height': rect.height() - top_border_height}
        if region is not None:
            coords = [region['left'] + coords_idx[1], region['top'] + coords_idx[0]]
    pdi.click_fast(x=coords[0], y=coords[1], clicks=presses, interval=interval_delay, move_speed=move_speed, duration=duration, button=button)
    time.sleep(return_delay)
    
    
def moveTo(coords=None, start_delay=0.0, return_delay=0.0, move_speed=5, window=None, region=None, coords_idx=None):
    if coords is None:
        coords = [None, None]
    time.sleep(start_delay)
    if coords_idx is not None:
        if window is not None and region is None:
            rect = window.rectangle()
            # The screen part to capture
            region = {'top': rect.top + top_border_height, 'left': rect.left + side_border_width, 'width': rect.width() - 2 * side_border_width, 'height': rect.height() - top_border_height}
        if region is not None:
            coords = [region['left'] + coords_idx[1], region['top'] + coords_idx[0]]
    ait.mouse_move(x=coords[0], y=coords[1], speed=move_speed)
    time.sleep(return_delay)
    
    
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
    
    
def find_arr_on_region(search_arr, region=None, img_arr=None, start_row=0, start_col=0, end_row=None, end_col=None, fail_gracefully=False, sharpen_threshold=130, return_as_tuple=False, n_matches=None):
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
        
    sharpen_threshold: int or list of int or None
        Value, below which all pixels values will be converted to 0, otherwise converted to scale_to.
        If list, see if you can find the arr using the first value as sharpen_threshold, if not, try the next value in the list and so on.
        If None, the img_arr will not be sharpened.
        
    return_as_tuple: bool
        True: return row, col, img_arr
        False: return [row, col], img_arr
        
    n_matches: int, str, or None
        None: default. Return the first match, if any, otherwise, return None
        int: Return the first n_matches number of matches, if any, in a list. If none, return [].
        str: 'all'. This means return all found matches, if any, in a list. If none, return [].
        
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
    found_idxs = []
    if not hasattr(sharpen_threshold, '__iter__'):
        sharpen_threshold = [sharpen_threshold]
    for k,st in enumerate(sharpen_threshold):
        if img_arr is None:
            # sharpen_threshold of 130 is for inventory_dct
            img_arr = take_grayscale_screenshot(region=region, sharpen_threshold=st,
                    scale_to=255, sharpen=st is not None, set_focus=False)
    
        start_row = min(max(start_row, 0), img_arr.shape[0] - 1)
        start_col = min(max(start_col, 0), img_arr.shape[1] - 1)
        if end_row is None:
            end_row = img_arr.shape[0] - search_arr.shape[0] - 1
        if end_col is None:
            end_col = img_arr.shape[1] - search_arr.shape[1] - 1
        end_row = min(img_arr.shape[0] - search_arr.shape[0] - 1, end_row)
        end_col = min(img_arr.shape[1] - search_arr.shape[1] - 1, end_col)
        end_row = max(end_row, 0)
        end_col = max(end_col, 0)
        search_where_mat = list_utils.where_mat(search_arr > 0)
        offset_idx = search_where_mat.sum(axis=1).argmin()
        min_row, min_col = search_where_mat[offset_idx]
            
        where_mat = list_utils.where_mat(img_arr > 0)
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
                
                # Check to make sure mask isn't completely ruining the search.
                # e.g. if less than 50% of masked pixels match the data (usually 0), then
                # it is probably just a white block
                if hasattr(search_arr, 'mask') and st is not None:
                    reversed_ma = np.ma.array(search_arr.data, mask=~search_arr.mask)
                    if (len(np.where(img_arr[i : i + reversed_ma.shape[0], 
                            j : j + reversed_ma.shape[1]] ==
                            reversed_ma)[0])
                            / reversed_ma.mask.sum()
                            ) < 0.5:
                        continue
                
                if return_as_tuple:
                    return i, j, img_arr
                elif n_matches is None:
                    return [i,j], img_arr
                elif n_matches != 'all' and len(found_idxs) + 1 == n_matches:
                    found_idxs.append([i,j])
                    return found_idxs, img_arr
                else:
                    found_idxs.append([i,j])
        if n_matches is None or n_matches == 'all' or len(found_idxs) != n_matches:
            # We did not find the search_arr in img_arr. Try the next st value unless this is the last st value.
            if k != len(sharpen_threshold) - 1:
                continue
        if len(found_idxs) == 0:
            if not fail_gracefully:
                raise Exception('Could not find search_arr in img_arr')
            if return_as_tuple:
                return None, None, img_arr
            else:
                return None, img_arr
    return found_idxs, img_arr
        

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
            
            
def click_drag(start_coords=None, end_coords=None, start_idx=None, end_idx=None, region=None, num_drags=1, start_delay=0.0, return_delay=0.0):
    if region is not None:
        if start_idx is not None:
            start_coords = [start_idx[1] + region['left'], start_idx[0] + region['top']]
        if end_idx is not None:
            end_coords = [end_idx[1] + region['left'], end_idx[0] + region['top']]
    time.sleep(start_delay)
    for i in range(num_drags):
        if i != 0:
            time.sleep(0.1)
        ait.mouse_move(start_coords[0], start_coords[1], speed=-1)
        ait.mouse_down()
        time.sleep(0.1)
        ait.mouse_move(end_coords[0], end_coords[1], speed=-1)
        ait.mouse_up()
    time.sleep(return_delay)
    
    
def find_via_moving_mouse(search_arr_csv_fname, dir_path, swg_region, sharpen_threshold=255, start_row=0, start_col=0, end_row=None, end_col=None, row_chunk_size='search_arr', col_chunk_size='search_arr', fast_move_speed=10, slow_move_speed=40, fail_gracefully=False):
    # You must have Show All Object Names option turned off.
    search_arr = get_search_arr(search_arr_csv_fname, dir_path=dir_path, mask_int=0)
    if row_chunk_size == 'search_arr':
        row_chunk_size = search_arr.shape[0]
    if col_chunk_size == 'search_arr':
        col_chunk_size = search_arr.shape[1]
    # Get into free-moving mouse mode
    pdi.press('alt')
    found_idx = None
    row_buffer = 10 + search_arr.shape[0]
    col_buffer = 10 + search_arr.shape[1]
    start_row = max(row_buffer, start_row)
    start_col = max(col_buffer, start_col)
    if end_row is None:
        end_row = swg_region['height'] - row_buffer
    end_row = min(end_row, swg_region['height'] - row_buffer)
    if end_col is None:
        end_col = swg_region['width'] - col_buffer
    end_col = min(end_col, swg_region['width'] - col_buffer)
    for row in range(start_row, end_row, row_chunk_size):
        moveTo(coords_idx=[row, start_col], region=swg_region, return_delay=0.02, move_speed=0)
        moveTo(coords_idx=[row, end_col], region=swg_region, return_delay=0.02, move_speed=fast_move_speed)
        found_idx, _ = find_arr_on_region(search_arr, region=swg_region, fail_gracefully=True, sharpen_threshold=sharpen_threshold)
        if found_idx is not None:
            # The object title will disappear after 1 second if the cursor is no longer over the object.
            time.sleep(1)
            found_idx, _ = find_arr_on_region(search_arr, region=swg_region, fail_gracefully=True, sharpen_threshold=sharpen_threshold)
            if found_idx is not None:
                return found_idx
            # Move along this row more slowly/carefully to see when it pops up again
            moveTo(coords_idx=[row, start_col], region=swg_region, return_delay=0.02, move_speed=0)
            for col in range(start_col, end_col, col_chunk_size):
                moveTo(coords_idx=[row, col], region=swg_region, return_delay=0.15, move_speed=slow_move_speed)
                found_idx, _ = find_arr_on_region(search_arr, region=swg_region, fail_gracefully=True, sharpen_threshold=sharpen_threshold)
                if found_idx is not None:
                    return found_idx
    if fail_gracefully:
        return None
    else:
        raise Exception('Could not find', search_arr_csv_fname)
    
        
def zoom(direction='in'):
    '''
    Parameters
    ----------
    direction: str
        Zoom in if 'in' or out if 'out'

    Purpose
    -------
    Zoom in or out by scrolling the mouse wheel
    '''
    direction_dct = {'in': 1, 'out': -1}
    for _ in range(50):
        pag.scroll(direction_dct[direction] * 100)
        
        
def idx_checks(region=None, idx=None, fail_gracefully=False):
    if idx[0] < 0:
        if fail_gracefully:
            return False
        else:
            raise Exception('idx is too far up. (row less than 0). idx:', idx)
    if idx[1] < 0:
        if fail_gracefully:
            return False
        else:
            raise Exception('idx is too far left. (col less than 0). idx:', idx)
    if idx[0] >= region['height']:
        if fail_gracefully:
            return False
        else:
            raise Exception('idx is too far down. (row greater than region height). idx:', idx, 'region:', region)
    if idx[1] >= region['width']:
        if fail_gracefully:
            return False
        else:
            raise Exception('idx is too far right. (col greater than region width). idx:', idx, 'region:', region)
    return True


def filter_img_arr(img_arr, BGR_dct, exclude=[]):
    '''
    

    Parameters
    ----------
    img_arr : TYPE
        DESCRIPTION.
    BGR_dct : TYPE
        DESCRIPTION.

    Returns
    -------
    img_arr : TYPE
        DESCRIPTION.

    Purpose
    -------
    Return a matrix of the same shape as img_arr[:,:,0] which has all 0s except for 1s where 
    img_arr[:,:,0] has values btwn (and including) the B min and max, AND
    img_arr[:,:,1] has values btwn (and including) the G min and max, AND
    img_arr[:,:,2] has values btwn (and including) the R min and max
    '''
    for exclude_dct in exclude:
        img_arr[exclude_dct['top']:exclude_dct['bottom'],exclude_dct['left']:exclude_dct['right']] = 0
        
    where_arr = find_pixels_on_BGR_arr(img_arr,
                b_lower_bound=BGR_dct['B']['min'], b_upper_bound=BGR_dct['B']['max'], g_lower_bound=BGR_dct['G']['min'], 
                g_upper_bound=BGR_dct['G']['max'], r_lower_bound=BGR_dct['R']['min'], r_upper_bound=BGR_dct['R']['max'])
    
    img_arr = np.zeros(img_arr[:,:,0].shape)
    img_arr[where_arr] = 1
    return img_arr
    
    
def destroy_item(item_coords, swg_window, region):
    destroy_arr = file_utils.read_csv(os.path.join('words_dir', 'Destroy.csv'), dtype=int)
    radial_option_delta_dct = {'6': [52, -106], '5': [70, -12], '4': [52, 81], '3': [-3, 104], '2': [-59, 81]}
    click(coords=item_coords, button='right', start_delay=0.1, return_delay=0.3)
    img_arr = take_grayscale_screenshot(window=swg_window, region=region, sharpen_threshold=230,
            scale_to=255, set_focus=False, sharpen=True)
    
    mouse_idx = [item_coords[1] - region['top'], item_coords[0] - region['left']]
    for radial_option in radial_option_delta_dct:
        potential_destroy_idx = [radial_option_delta_dct[radial_option][0] + mouse_idx[0], radial_option_delta_dct[radial_option][1] + mouse_idx[1]]
        if np.all(img_arr[potential_destroy_idx[0] : potential_destroy_idx[0] + destroy_arr.shape[0], potential_destroy_idx[1] : potential_destroy_idx[1] + destroy_arr.shape[1]] == destroy_arr):
            pdi.press(radial_option)
    time.sleep(0.7)