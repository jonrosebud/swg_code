# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 17:41:08 2021

@author: trose
"""
from copy import deepcopy
import string
from pprint import pprint
import pandas as pd
import numpy as np
import math
import pyautogui as pag
import pydirectinput_tmr as pdi
from drag_mouse import drag_mouse
import time
from config_utils import Instruct
import socket
config_fpath = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config = Instruct(config_fpath)
config.get_config_dct()
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils
os = file_utils.os
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import swg_utils
import swg_window_management as swm
import go_to_chassis_dealer

'''
inventory_arr_dir: str
    Path of directory which contains matrices of various strings that appear in the inventory description section.
    
inventory_dct: dict
    Keys: strings that appear in the inventory description section that we want to find.
    Values: grayscaled (and sharpened) screenshot matrices of each of the strings we want to find. The shape is just enough to encapsulate the string.
    
character_arr_dir: str
    Path of directory which contains matrices of alphanumeric characters and certain special characters too which will be used to decipher the name of each component as it appears on the top bar of the inventory widdow.

character_names_dct: dict
    Keys: strings of the character names that you want to find. e.g. 'A', 'B', ..., 'Z', '0', '1', ..., 'slash', 'dash', ...
    Values: grayscaled (and sharpened) screenshot matrices of each of the characters we want to find. The shape is just enough to encapsulate the character.
    
swg_window: pywinauto.application.WindowSpecification
    A window object for a particular swg instance.
    
rect: object
    Attributes are top, left, width(), height() which are ints and describe the coordinates and size of the swg_window
    
height_of_window_header: int
     Number of pixels that the window header is tall. The window header is the thing that says "Star Wars Galaxies" and that you can click and drag to move the window.
     
region: dict
    Keys: top, left, width, height
    Values: ints describing the y coord, x coord of the top left corner of the img_arr matrix (which is the screenshot and will not include the window header).
    
'''
inventory_arr_dir = 'inventory_dir'
inventory_dct = {
         fname : file_utils.read_csv(os.path.join(inventory_arr_dir, fname + '.csv'), dtype=int)
        for fname in ['armor_name', 'booster_name', 'capacitor_name', 'droid_interface_name',
        'engine_name', 'reactor_name', 'shield_name', 'weapon_name', 'cargo_crate_name',
        'military_crate_name', 'collection_name',
        'Armor', 'Mass', 'Reverse_Engineering_Level', 'Reactor_Energy_Drain', 'Reactor_Generation_Rate',
        'Booster_Energy', 'Booster_Recharge_Rate', 'Booster_Energy_Consumption_Rate',
        'Acceleration', 'Top_Booster_Speed', 'Capacitor_Energy', 'Recharge_Rate',
        'Droid_Command_Speed', 'Pitch_Rate_Maximum', 'Yaw_Rate_Maximum', 
        'Roll_Rate_Maximum', 'Engine_Top_Speed', 'Front_Shield_Hitpoints', 
        'Back_Shield_Hitpoints', 'Shield_Recharge_Rate', 'Min_Damage', 'Max_Damage', 'Vs_Shields',
        'Vs_Armor', 'Energy_Per_Shot', 'Refire_Rate', 'Contents', 'period', 'slash', 'dash',
        'top_left_corner_of_description_section_130_threshold', 'lower_right_corner'] +
        list(map(str, range(10)))
        }

character_arr_dir = 'character_dir'
character_names_dct = {
    fname : file_utils.read_csv(os.path.join(character_arr_dir, fname + '.csv'), dtype=int)
        for fname in list(string.ascii_uppercase) + list(map(str, range(10))) 
        + ['and', 'open_parenthesis', 'close_parenthesis', 'dash', 'period', 'slash']
    }

swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
swg_window = swm.swg_windows[swg_window_i]
region = swm.swg_window_regions[swg_window_i]


def click(coords, button='left', start_delay=0.5, return_delay=1):
    '''
    Parameters
    ----------
    coords: list of int
        [x,y] coordinates on the screen to click on.
        
    button: str
        A string telling pdi.mouseDown which mouse button to click. The default is 'left'.
        
    start_delay: float
        An amount of time to sleep before clicking.
        
    return_delay: float
        An amount of time to sleep after clicking.

    Returns
    -------
    None

    Purpose
    -------
    Simulate a mouse click on the provided coordinates. This function builds in an ability to sleep a certain amount of time before and after the click.
    '''
    time.sleep(start_delay)
    pdi.moveTo(coords[0], coords[1])
    pdi.mouseDown(button=button)
    pdi.mouseUp(button=button)
    time.sleep(return_delay)
    
    
def press(keys):
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
    for key in keys:
        pdi.keyDown(key)
    for key in keys[::-1]:
        pdi.keyUp(key)
    
    
def chat(string):
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
    time.sleep(0.2)
    pdi.press('enter')
    time.sleep(0.1)
    pag.write(string)
    time.sleep(0.1)
    pdi.press('enter')
    time.sleep(0.1)


def find_inventory_dct_item_on_region(swg_window_region, inventory_dct_key, img_arr=None, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False):
    '''
    Parameters
    ----------
    swg_window_region: dict
        See region docs
        
    inventory_dct_key: str
        Key of the dictionary inventory_dct.
        
    img_arr: np.array, shape: (1030, 771) or None
        Screenshot matrix of the swg_window (with top border removed) which has been Grayscaled and sharpened with the same cutoff as used in inventory_dct.
        If None, a new screenshot will be taken by this function.
        
    iterate_row_then_col: bool
        True: Search through img_arr for inventory_dct[inventory_dct_key] by doing the following: for each row, sweep over all columns
        False: Search through img_arr for inventory_dct[inventory_dct_key] by doing the following: for each column, sweep over all rows
        
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
    inventory_dct_item_idx, img_arr
    
    inventory_dct_item_idx: list of int or None
        [row, col] giving the location in img_arr of the top left corner of the found array matching that for inventory_dct_key.
        If None, this function could not find the item on the screen.
        
    img_arr: np.array, shape: (1030, 771)
        Screenshot matrix of the swg_window (with top border removed) which has been Grayscaled and sharpened with the same cutoff as used in inventory_dct.
        
        
    Purpose
    -------
    Take a screenshot and find the matrix given by inventory_dct[inventory_dct_key] on that screenshot matrix (after grayscaling and sharpening using the same threshold).

    Notes
    -----
    1. Inventory must be open already, and the description section must be visible.
    '''
    if img_arr is None:
        img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                scale_to=255, sharpen=True, set_focus=False)

    if iterate_row_forwards:
        row_direction = 1
    else:
        row_direction = -1
    if iterate_col_forwards:
        col_direction = 1
    else:
        col_direction = -1
    if iterate_row_then_col:
        for i in range(start_row, img_arr.shape[0] - inventory_dct[inventory_dct_key].shape[0])[::row_direction]:
            for j in range(start_col, img_arr.shape[1] - inventory_dct[inventory_dct_key].shape[1])[::col_direction]:
                if np.all(img_arr[i : i + inventory_dct[inventory_dct_key].shape[0], 
                        j : j + inventory_dct[inventory_dct_key].shape[1]] ==
                        inventory_dct[inventory_dct_key]):
                    
                    return [i, j], img_arr
        if not fail_gracefully:
            raise Exception('Could not find', inventory_dct_key)
        return None, None
    else:
        for j in range(start_col, img_arr.shape[1] - inventory_dct[inventory_dct_key].shape[1])[::col_direction]:
            for i in range(start_row, img_arr.shape[0] + inventory_dct[inventory_dct_key].shape[0])[::row_direction]:
                if np.all(img_arr[i : i + inventory_dct[inventory_dct_key].shape[0], 
                        j : j + inventory_dct[inventory_dct_key].shape[1]] ==
                        inventory_dct[inventory_dct_key]):
                    
                    return [i, j], img_arr
        if not fail_gracefully:
            raise Exception('Could not find', inventory_dct_key)
        return None, None


def get_item_coords(corner_description_idx, swg_window_region, item_inventory_position):
    '''
    Parameters
    ----------
    corner_description_idx: list of int
        [row, col] index of the img_arr of the swg_window for the top of the leftmost line bounding the item description area in the inventory.
    
    swg_window_region: dict
        region of the monitor used when getting the img_arr.
        Keys: 'left', 'top', 'width', 'height'
        
    item_inventory_position: int
        The index of the position of the item in the inventory to delete.
        e.g. 0 means delete the first item in the inventory.
        
    num_inventory_cols: int
        Number of columns of items in the visible, open inventory.

    Returns
    -------
    item_coords: list of int
    top_of_item: int
        [x, y] coordinate on monitor of the item located at item_inventory_position

    Purpose
    -------
    Find the x and y coordinates on the monitor of the item located at item_inventory_position
    in the visible, open inventory.
    '''
    item_width = 64
    item_height = 65
    # top and left of the center of the item in row 0, column 0 in the inventory
    first_item_coords = [corner_description_idx[1] + swg_window_region['left'] + 305,
            corner_description_idx[0] + swg_window_region['top'] + 8 + int(item_width / 2)]
    
    row_num = int(item_inventory_position / num_inventory_cols)
    col_num = item_inventory_position % num_inventory_cols
    item_coords = [first_item_coords[0] + item_width * col_num,
            first_item_coords[1] + item_height * row_num]
    
    return item_coords


def find_str_on_image_given_col(str_arr, img_arr, col, row_start=0):
    '''
    Parameters
    ----------
    str_arr: np.array, variable shape
         Grayscaled (and sharpened) screenshot matrices the string you want to find. The shape is just enough to encapsulate the string.
        
    img_arr: np.array, shape: (1030, 771)
        Screenshot matrix of the swg_window (with top border removed) which has been Grayscaled and sharpened with the same cutoff as used in str_arr when it was made.
        
    col: int
        The column that you believe str_arr should be found on img_arr
        
    row_start: int
        The row to start traversing img_arr from.

    Returns
    -------
    row: int or None
        The row index that str_arr was found within img_arr
        None: str_arr was not found withi img_arr

    Purpose
    -------
    Search for str_arr in img_arr given the col that should be str_arr's left edge within img_arr.
    
    Method
    ------
    Put str_arr's left column aligned with col in img_arr and shift str_arr down through the rows of img_arr -one at a time - until one of the rows (or none) provide a full match of all elements in str_arr.
    '''
    for row in range(row_start, img_arr.shape[0] - str_arr.shape[0]):
        if np.all(img_arr[row : row + str_arr.shape[0], col : col + str_arr.shape[1]] == str_arr):
            return row
    return None


def get_number_from_arr(line_arr, numeric_type=int):
        '''
        line_arr: 2D np.array
            This matrix must be the same height (number of rows) as the stored
            digit matrices in digit_dct. line_arr contains some of the
            digit matrices in digit_dct which will be read sequentially
            to get the overall (single) number.
            
        Returns
        -------
        digits: int
            The number as read from the line_arr.
        
        Purpose
        -------
        Given a matrix that contains digit matrices separated by columns of all
        0's (or all are 0's except one), concatenate the digits in the order they 
        appear to return the overall number represented by line_arr.
        
        Method
        ------
        Iterate through each column of line_arr until there's a column of not all 
        zeros or all but one is zero. If the sum of the column is greater than 255 
        (assuming there are only 255 and 0 entries), this means we have found the 
        column index, i, of the beginning of a new digit. Continue iterating 
        through the columns with j until you find the first column after i that is 
        all zeros (or all but one is zeros). The slice in between is the matrix of 
        one of the digits. Try each digit matrix until one of them matches. Append 
        the digit to the overall digits string. Convert to a number at the end.
    
        Notes
        -----
        1. The reason we are splitting by all zeros or all but one being 0 is 
            because '4' has a non-zero value sticking out to the right, such that
            the next digit begins on the very next column without a break (no
            all-zero column).
            
        2. The reason we do not make each digit a common width and use a step
            size of this width is because there could be other terms like
            a decimal point or a negative sign.
        '''
        # First, check for whether there is a slash or a dash because these are
        # treated differently. i.e. a slash means just get the value after the
        # slash, and a dash means return a list or 2 values (one before the dash
        # and one after).
        dash_position = False
        slash_position = False
        for key in ['slash', 'dash']:
            i = 0
            # Iterate through the columns of line_arr
            while i < line_arr.shape[1] - inventory_dct[key].shape[1]:
                target_arr = line_arr[:, i : i + inventory_dct[key].shape[1]]
                if np.all(inventory_dct[key] == target_arr):
                    if key == 'dash':
                        dash_position = deepcopy(i)
                    else:
                        slash_position = deepcopy(i)
                    break
                i += 1
            if slash_position is not False or dash_position is not False:
                break
        i = 0
        result = []
        digits = ''
        # Iterate through the columns of line_arr
        while i < line_arr.shape[1]:
            # If the ith col is not all zeros then we've found the beginning of
            # a digit.
            if np.sum(line_arr[:, i]) > 255:
                j = deepcopy(i)
                # Continue iterating through the columns of line_arr until you
                # find a column of all zeros (or all but one being 0) which 
                # represents the space in between digits and thus marks the end of 
                # the digit.
                while np.sum(line_arr[:, j]) > 255:
                    j += 1
                # The digit we want to find a match to, target_digit, is the slice
                # from col i to col j.
                target_arr = line_arr[:, i : j].astype(int)
                # Increase i so it is starting on a column of all zeros and thus
                # ready to find the next digit.
                i += j - i
                # Iterate through all the stored digit matrices to see if one
                # matches.
                for key, arr in inventory_dct.items():
                    if key not in ['period'] + list(map(str, range(10))):
                        continue
                    # If the digit_arr doesn't have the same shape as target_arr,
                    # it can't be the target digit so skip it.
                    if arr.shape != target_arr.shape:
                        continue
                    # If it's a perfect match, then we know which digit the
                    # target_arr is so append the digit string to the overall
                    # string.
                    if np.all(arr == target_arr):
                        if key == 'period':
                            digits += '.'
                        else:
                            digits += key
            if dash_position is not False and i == dash_position:
                result.append(numeric_type(digits))
                digits = ''
            if slash_position is not False and i == slash_position:
                result.append(numeric_type(digits))
                digits = ''
            i += 1
        if dash_position is not False or slash_position is not False:
            result.append(numeric_type(digits))
        else:
            # Convert the digit string into a number.
            result = numeric_type(digits)
        return result
    
    
def get_str_from_arr(line_arr):
        '''
        line_arr: 2D np.array
            This matrix must be the same height (number of rows) as the stored
            digit matrices in digit_dct. line_arr contains some of the
            digit matrices in digit_dct which will be read sequentially
            to get the overall (single) number.
            
        Returns
        -------
        digits: int
            The number as read from the line_arr.
        
        Purpose
        -------
        Given a matrix that contains digit matrices separated by columns of all
        0's (or all are 0's except one), concatenate the digits in the order they 
        appear to return the overall number represented by line_arr.
        
        Method
        ------
        Iterate through each column of line_arr until there's a column of not all 
        zeros or all but one is zero. If the sum of the column is greater than 255 
        (assuming there are only 255 and 0 entries), this means we have found the 
        column index, i, of the beginning of a new digit. Continue iterating 
        through the columns with j until you find the first column after i that is 
        all zeros (or all but one is zeros). The slice in between is the matrix of 
        one of the digits. Try each digit matrix until one of them matches. Append 
        the digit to the overall digits string. Convert to a number at the end.
    
        Notes
        -----
        1. The reason we are splitting by all zeros or all but one being 0 is 
            because '4' has a non-zero value sticking out to the right, such that
            the next digit begins on the very next column without a break (no
            all-zero column).
            
        2. The reason we do not make each digit a common width and use a step
            size of this width is because there could be other terms like
            a decimal point or a negative sign.
        '''
        i = 0
        char_start_col = 0
        char_end_col = 0
        result = ''
        # Iterate through the columns of line_arr
        while i < line_arr.shape[1]:
            # If the ith col has at least one 0 then we've found the beginning of
            # a character.
            if len(np.where(line_arr[:, i] == 0)[0]) > 0:
                char_start_col = deepcopy(i)
                if  char_start_col - char_end_col > 4:
                    # space character
                    result += ' '
                j = deepcopy(i)
                # Continue iterating through the columns of line_arr until you
                # find a column with no zeros which 
                # represents the space in between characters and thus marks the end of 
                # the character.
                while j < line_arr.shape[1] and len(np.where(line_arr[:, j] == 0)[0]) > 0:
                    j += 1
                char_end_col = j - 1
                # The character we want to find a match to, target_characte_arrr, is the slice
                # from col i to col j.
                target_arr = line_arr[:, i : j].astype(int)
                # Increase i so it is starting on a column of all zeros and thus
                # ready to find the next character.
                i += j - i
                # Iterate through all the stored character matrices to see if one
                # matches.
                for key, arr in character_names_dct.items():
                    # If the character_arr doesn't have the same shape as target_character_arr,
                    # it can't be the target character so skip it.
                    if arr.shape != target_arr.shape:
                        continue
                    # If it's a perfect match, then we know which character the
                    # target_arr is so append the character string to the overall
                    # string.
                    if np.all(arr == target_arr):
                        if key == 'period':
                            result += '.'
                        elif key == 'slash':
                            result += '/'
                        elif key == 'dash':
                            result += '-'
                        elif key == 'and':
                            result += '&'
                        elif key == 'open_parenthesis':
                            result += '('
                        elif key == 'close_parenthesis':
                            result += ')'
                        else:
                            result += key
            i += 1
        return result
    
    
def get_item_count_and_capacity(region, img_arr=None, start_row=600, start_col=600):
    '''
    Parameters
    ----------
    region: dict
        See region docs above.
        
    img_arr: np.array
        See img_arr docs above.
        None: This function will take a new screenshot to use.
        
    start_row: int
        The row to start searching for the item count and capacity. The default is 600 because it's usually in the lower right corner.
        
    start_col: int
        The col to start searching for the item count and capacity. The default is 600 because it's usually in the lower right corner.

    Returns
    -------
    item_count: int
        The number of items currently in this container.
        
    item_capacity: int
        The max number of items that this container can hold.

    Purpose
    -------
    Get item_count and item_capacity for a given selected container.
    '''
    time.sleep(0.5)
    if img_arr is None:
        img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                scale_to=255, sharpen=True, set_focus=False)

    # Get lower right corner indices of container window in img_arr
    lower_right_corner_idx, img_arr = find_inventory_dct_item_on_region(region, 'lower_right_corner', img_arr=img_arr, start_row=start_row, start_col=start_col)
    # Get the container item count.
    line_arr = img_arr[lower_right_corner_idx[0] + num_rows_from_right_corner_row_to_start_of_item_count : digit_height + lower_right_corner_idx[0] + num_rows_from_right_corner_row_to_start_of_item_count, 
            lower_right_corner_idx[1] - num_cols_from_right_corner_col_to_start_of_item_count : lower_right_corner_idx[1]]
    
    item_count, item_capacity = get_number_from_arr(line_arr, numeric_type=int)
    return item_count, item_capacity
    
    
def get_extreme_avg_and_modifier_combo_for_stats(extreme_avg_and_modifier_json_dir, loot_table_dir):
        '''
        extreme_avg_and_modifier_json_dir: str
            Directory to output the resulting .json file which will have the component type in the name.
            If None, then self.extreme_avg_and_modifier_json_dir must not be None.
            
        loot_table_dir: str
            Directory which contains the loot tables .tab files. (Usually found in dsrc\sku.0\sys.server\compiled\game\datatables\ship\components
            where dsrc is gotten by git clone https://github.com/SWG-Source/dsrc.git
            
        Returns
        -------
        extreme_avg_and_modifier_dct: dict
        {
        'armor':{
            1:{
              'Armor':{
                  'Avg_min': number0, 'Modifier_min': number1, 'named_component_min': name0, 'Avg_max': number2, 'Modifier_max': number3, 'named_component_max: name1'
                  },
              'Mass':{
                  'Avg_min': number4, 'Modifier_min': number5, 'named_component_min': name2, 'Avg_max': number6, 'Modifier_max': number7, 'named_component_max: name3'
                  }
                },
            2: ...
            },
        'booster': ...
        }
            
        Purpose
        -------
        For each component type, find the Avg and Modifier combo of values that give the max and the combo that give the min value possible to loot for each stat for each RE level on a particular component type according to the loot tables.
        The max value is Avg * (1 + 13.0135 * Modifier) where Avg and Modifier are stored in the loot table.
        The min value is Avg * (1 - 13.0135 * Modifier). These will be used to calculate the best and worst values, as well as the noramlized z score of a piece of loot.
        Note, for booster energy, the max value is Avg + Modifier and the min value is Avg - Modifier.
        
        Put these Avg and Modifier values into a dictionary: The keys will be integers 1-10 inclusive, which represent the RE level. Each value will be a dictionary with keys being the stats available to a 
        component (e.g. Armor, Mass, and Reactor Generation Rate for a Reactor). The values will be 'Avg_min', 'Modifier_min', 'named_component_min', 'Avg_max', 'Modifier_max', 'named_component_max'. 
        Remember that Avg_max and Modifier_max are the Avg, Modifier combo (the same row) in the loot table that yielded the highest value for Avg * (1 + 13.0135 * Modifier), and this row is the one used
        to get named_component_max (which is the fname of the value under strType in the loot table e.g. wpn_armek_advanced).
        
        Output this overall dictionary as a .json file for future reference. If this .json file already exists, then just read that file and no need to do anything else.
        '''
        output_fpath = os.path.join(extreme_avg_and_modifier_json_dir, 'extreme_avg_and_modifier.json')
        if os.path.exists(output_fpath):
            extreme_avg_and_modifier_dct = file_utils.get_dct_from_json(output_fpath)
            return extreme_avg_and_modifier_dct
        extreme_avg_and_modifier_dct = {}
        for component in [Armor(), Booster(), Capacitor(), Droid_Interface(), Engine(), Reactor(), Shield(), Weapon()]:
            loot_table_fpath = os.path.join(loot_table_dir, component.component_type + '.tab')
            component.read_loot_table(loot_table_fpath)
            re_lvl_dct = {}
            for re_lvl in range(1,11):
                component_stat_dct = {}
                for stat_key in component.stats:
                    if 'Mod' in stat_key or stat_key == 'Reverse_Engineering_Level' or stat_key == 'named_component':
                        continue
                    avg_modifier_dct = {}
                    modifier_name, modifier_suffix = component.get_modifier_name(stat_key)
                    re_lvl_df = component.loot_table_df[component.loot_table_df.Reverse_Engineering_Level == int(re_lvl)]
                    re_lvl_df['mean'] = component.get_mean_value(re_lvl_df[stat_key], re_lvl_df[modifier_name], stat_key)
                    #re_lvl_df['stdev'] = component.get_stdev_value(re_lvl_df[stat_key], re_lvl_df[modifier_name], stat_key)
                    
                    if component.higher_is_better_dct[stat_key]:
                        argxtreme = re_lvl_df[stat_key].argmax()
                    else:
                        argxtreme = re_lvl_df[stat_key].argmin()
                    
                    avg_modifier_dct['Avg'] = re_lvl_df[stat_key].values[argxtreme]
                    avg_modifier_dct['Modifier'] = re_lvl_df[modifier_name].values[argxtreme]
                    avg_modifier_dct['mean'] = component.get_mean_value(avg_modifier_dct['Avg'], avg_modifier_dct['Modifier'], stat_key)
                    avg_modifier_dct['stdev'] = component.get_stdev_value(avg_modifier_dct['Avg'], avg_modifier_dct['Modifier'], stat_key)
                    component_stat_dct[stat_key] = deepcopy(avg_modifier_dct)
                re_lvl_dct[str(re_lvl)] = deepcopy(component_stat_dct)
            extreme_avg_and_modifier_dct[component.component_type] = deepcopy(re_lvl_dct)
        file_utils.write_dct_to_json(output_fpath, extreme_avg_and_modifier_dct)
        return extreme_avg_and_modifier_dct


def get_name_header(corner_description_idx, img_arr=None):
    '''
    Parameters
    ----------
    corner_description_idx: list of int
        [row, col] index of the img_arr of the swg_window for the top of the leftmost line bounding the item description area in the inventory.
        
    img_arr: np.array or None
        See docs above.
        None: This function will get a new screenshot to use.

    Returns
    -------
    result: str
        The name header (name of the selected item).
        
    Purpose
    -------
    Get the name header (name of the selected item).
    
    Method
    ------
    Use get_str_from_arr to get the string corresponding to the name of the item.
    '''
    if img_arr is None:
        img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                scale_to=255, sharpen=True, set_focus=False)
    # Offset to [row, col]
    named_component_offset = [-33, -2]
    named_component_idx = [named_component_offset[0] + corner_description_idx[0], named_component_offset[1] + corner_description_idx[1]]
    named_component_row_length = 800
    named_component_height = 10
    line_arr = img_arr[named_component_idx[0] : named_component_idx[0] + named_component_height, named_component_idx[1] : named_component_idx[1] + named_component_row_length]
    result = get_str_from_arr(line_arr)
    return result


class Ship_Component:
    '''
    A class which has methods applicable to all component types. Ship_Component is a super class of sub-classes such as Armor(), Booster(), etc.
    '''
    def __init__(self):
        '''
        stats: dict
            Stores all the stats listed for a given selected, looted component as floats. Also stores Reverse_Engineering_Level (int) and named_component (str) which is the name of the component such as
            'Qualdex Capacitor'.
            
        loot_table_translation: dict
            Enables converting the naming scheme for stat names in the loot tables to more readable stat names.
            
        higher_is_better_dct: dict
            The keys are stat keys and the values are bools.
            True: Higher stat value is better (e.g. Front_Shield_Hitpoints)
            False: Lower stat value is better (e.g. Mass)
            
        component_type: str
            Lower case string of the component type
            e.g.
            booster
            
        stc_df: pd.DataFrame
            This is the loot table for a particular component_type.
        
        recorded_stats_fpath: str
            Path to a .csv file where I'll store the stats on each component sorted so that eventually I'll have enough components to have a good empirical distribution of stat distributions according to how I
            sample.
            
        recorded_stats_df: pd.DataFrame
            The current list of all looted components of this type.
            
        recorded_stats_names: list of str
            List of names of stats
            e.g.
            ['Mass', 'Armor']
        
        Notes
        -----
        1. Some variables such as stats, higher_is_better, will be filled in when a particular sub-class is instantiated. i.e. Reactor() will add 'Reactor_Generation_Rate'.
        '''
        self.stats = {
                'Armor': None,
                'Mass': None,
                'Reverse_Engineering_Level': None,
                'named_component': None
                }
        
        self.loot_table_translation = {
                'fltMaximumArmorHitpoints': 'Armor',
                'fltMass': 'Mass',
                'reverseEngineeringLevel': 'Reverse_Engineering_Level'
                }
        
        self.higher_is_better_dct = {
                'Armor': True,
                'Mass': False,
                }
        
        self.add_modifier_name_to_translation_dct()
        self.component_type = self.__class__.__name__.lower()
        if self.component_type != 'ship_component':
            # Use the STC file for now.
            stc_fpath = os.path.join('STC', self.component_type + '_stc.csv')
            self.stc_df = pd.read_csv(stc_fpath, dtype=float)
            self.stc_df = self.stc_df.astype({'Reverse_Engineering_Level': int})
        
        # Once enough of my own data has been collected, I'll use my own percentiles.
        # Collect data by keeping track of component stats
        self.recorded_stats_fpath = os.path.join('STC', self.component_type + '_recorded_stats.csv')
        if os.path.exists(self.recorded_stats_fpath):
            self.recorded_stats_df = pd.read_csv(self.recorded_stats_fpath)
            if len(self.recorded_stats_df) > 0:
                type_dct = {col_name:float for col_name in self.recorded_stats_df.columns if col_name != 'named_component'}
                type_dct['Reverse_Engineering_Level'] = int
                self.recorded_stats_df = self.recorded_stats_df.astype(type_dct)
        else:
            # The sub-classes will take care of instantiating it.
            self.recorded_stats_df = None
        self.recorded_stats_names = list(self.stats.keys())
            
        
    def stats_dct_init(self):
        for stat_name in self.recorded_stats_names:
            self.stats[stat_name] = None
            
    def worth_keeping(self):
        '''
        Returns
        -------
        is_worth_keeping: bool
            True: You should store this loot piece into a hopper other than the junk hopper
            False: You should store this loot piece into a junk hopper
            
        Purpose
        -------
        Determine whether the current loot piece is worth keeping or, instead, is only suitable for the chassis dealer. There are two thresholds, one for desirable component type and RE level combinations, and
        another for a component type and RE level combo that is usually not desirable such as boosters, lvl 9 engines, etc. These latter components have a much higher requirement of quality in order to keep them
        because usually the stats for those components are inferior.
        '''
        return self.max_loot_percentile_value >= 0.969999999999998 and (self.stats['Reverse_Engineering_Level'] not in self.usually_bad_re_lvls or self.max_loot_percentile_value >= 0.999998999999998)
        
        
    def store_loot_in_hopper(self, item_coords, hopper_type):
        '''
        Parameters
        ----------
        item_coords: list of int
            Monitor coordinates [x, y] of the item that is in the inventory.
            
        hopper_type: str
            Options are 'junk_loot', 'good_loot', 'crate'
            Determines where the item in the inventory gets placed.

        Purpose
        -------
        Store the loot item in the appropriate input hopper.
        '''
        global junk_hopper_i
        global droid_interface_hopper_i
        global non_components_hopper_i
        global collection_hopper_i
        global currently_open_hopper
        # Determine which intput hopper to open
        # Deal with multiple good loot hoppers (the index like _0, _1, etc) later.
        opened_new_hopper = False
        if hopper_type == 'good_loot':
            hopper_name = self.component_type[0].upper() + str(self.stats['Reverse_Engineering_Level'])[-1] + '_0'
        elif hopper_type == 'junk_loot':
            hopper_name = 'Loot_' + str(junk_hopper_i)
        elif hopper_type == 'crate':
            # Temporary name
            hopper_name = 'clothing'
        elif hopper_type == 'junk_droid_interface':
            hopper_name = 'DIs_' + str(droid_interface_hopper_i)
        elif hopper_type == 'non_components':
            hopper_name = 'non_components_' + str(non_components_hopper_i)
        elif hopper_type == 'collection':
            hopper_name = 'collections_' + str(collection_hopper_i)
        if currently_open_hopper != hopper_name:
            close_hopper()
            # Open desired hopper
            chat('/open ' + hopper_name)
            time.sleep(0.2)
            opened_new_hopper = True
            currently_open_hopper = deepcopy(hopper_name)
        # Currently only incrementing junk loot, junk DIs, and non_components
        if hopper_type == 'junk_loot' or hopper_type == 'junk_droid_interface' or hopper_type == 'non_components':
            # Check to see if we filled it up.
            item_count, item_capacity = get_item_count_and_capacity(region, img_arr=None, start_row=100, start_col=880)
            while item_count == item_capacity:
                # Close hopper
                close_hopper()
                if hopper_type == 'junk_loot':
                    junk_hopper_i += 1
                    hopper_name = 'Loot_' + str(junk_hopper_i)
                elif hopper_type == 'junk_droid_interface':
                    droid_interface_hopper_i += 1
                    hopper_name = 'DIs_' + str(droid_interface_hopper_i)
                elif hopper_type == 'non_components':
                    non_components_hopper_i += 1
                    hopper_name = 'non_components_' + str(non_components_hopper_i)
                elif hopper_type == 'collection':
                    collection_hopper_i += 1
                    hopper_name = 'collections_' + str(collection_hopper_i)
                # Open new hopper
                chat('/open ' + hopper_name)
                time.sleep(0.2)
                opened_new_hopper = True
                currently_open_hopper = deepcopy(hopper_name)
                item_count, item_capacity = get_item_count_and_capacity(region, img_arr=None, start_row=100, start_col=880)
        if opened_new_hopper:
            # activate inventory window
            click(inventory_activation_coords, button='left', start_delay=0.1, return_delay=0.1)
        # Drag item from inventory to the hopper.
        drag_mouse(autoit_dir, start_coords=item_coords, end_coords=into_hopper_coords, num_drags=1, delay_return=0.75)
        
        
    def get_max_loot_percentile_value_stc(self):
        '''
        Purpose
        -------
        Of all the stats on a particular loot piece, find the one with the highest percentile and store the highest percentile into self.max_loot_percentile_value. The percentiles are based off of the STC file instead
        of the distribution from the loot tables because it is unclear how to combine the distributions of a given component type and RE level into one distribution. However, eventually I'll have enough loot recorded
        that I can use the empirical percentiles. For now, use the STC file as an approximation.
        '''
        self.max_loot_percentile_value = 0
        re_lvl_df = deepcopy(self.stc_df[self.stc_df.Reverse_Engineering_Level == self.stats['Reverse_Engineering_Level']])
        for stat_key, stat_value in self.stats.items():
            if stat_key == 'Reverse_Engineering_Level' or stat_key == 'named_component' or stat_key == 'Booster_Energy':
                continue
            diff_arr = re_lvl_df[stat_key].values - self.stats[stat_key]
            if self.higher_is_better_dct[stat_key]:
                # Only keep values with lesser stat value in the percentile arrary
                percentile_arr = re_lvl_df['stc_percentile'].values[np.where(diff_arr <= 0)[0]]
            else:
                # Only keep values with higher stat value in the percentile arrary
                percentile_arr = re_lvl_df['stc_percentile'].values[np.where(diff_arr >= 0)[0]]
            if len(percentile_arr) == 0:
                # Set to some low percentile value
                percentile = 0.1
            else:
                # The percentile is the highest of these so it's the last element of percentile_arr
                percentile = percentile_arr[-1]
            self.max_loot_percentile_value = max(self.max_loot_percentile_value, percentile)
        
        
    def get_mean_value(self, avg, modifier, stat_key):
        '''
        Parameters
        ----------
        avg: float
            Value provided in the loot table
            
        modifier: float
            Modifier value provided in the loot table.
            
        stat_key: str
            name of the stat.
            e.g.
            'Mass'

        Returns
        -------
        mean_value: float
            Mean of the normal distribution of the stat given the loot table values.

        Purpose
        -------
        Get mean_value
        '''
        if stat_key == 'Booster_Energy':
            return avg
        else:
            return avg * (1 + 0.5 * modifier)
        
        
    def get_stdev_value(self, avg, modifier, stat_key):
        '''
        Parameters
        ----------
        avg: float
            Value provided in the loot table
            
        modifier: float
            Modifier value provided in the loot table.
            
        stat_key: str
            name of the stat.
            e.g.
            'Mass'

        Returns
        -------
        stdev_value: float
            Standard deviation of the normal distribution of the stat given the loot table values.

        Purpose
        -------
        Get stdev_value
        '''
        if stat_key == 'Booster_Energy':
            return modifier / np.sqrt(3.0)
        else:
            return 0.5 * modifier * avg
        
        
    def get_max_value(self, avg, modifier, stat_key):
        '''
        Parameters
        ----------
        avg: float
            Value provided in the loot table
            
        modifier: float
            Modifier value provided in the loot table.
            
        stat_key: str
            name of the stat.
            e.g.
            'Mass'

        Returns
        -------
        max_value: float
            Maximum possible value given the distribution of the stat and the code. The code only limits it by limiting the precision of floating point numbers for v1, v2, and their propagation.

        Purpose
        -------
        Get the maximum possible value to loot for this stat given the avg and modifier and Reverse Engineering Level (avg and modifier are gotten on the loot table and thus reflect a given RE lvl).
        '''
        if stat_key == 'Booster_Energy':
            return avg + modifier
        else:
            return avg * (1 + 13.30135 * modifier)
        
        
    def get_min_value(self, avg, modifier, stat_key):
        '''
        Parameters
        ----------
        avg: float
            Value provided in the loot table
            
        modifier: float
            Modifier value provided in the loot table.
            
        stat_key: str
            name of the stat.
            e.g.
            'Mass'

        Returns
        -------
        min_value: float
            Minimum possible value given the distribution of the stat and the code. The code only limits it by limiting the precision of floating point numbers for v1, v2, and their propagation. The code doesn't
            allow for negative numbers.

        Purpose
        -------
        Get the minimum possible value to loot for this stat given the avg and modifier and Reverse Engineering Level (avg and modifier are gotten on the loot table and thus reflect a given RE lvl).
        '''
        if stat_key == 'Booster_Energy':
            return max(0, avg - modifier)
        else:
            return max(0, avg * (1 - 13.30135 * modifier))
        
        
    def get_cdf_value(self, x, mean, stdev, avg, modifier, stat_key):
        '''
        Parameters
        ----------
        x: float
            Stat value on the loot piece.
            
        mean: float
            Mean of the normal distribution for this stat
            
        stdev: flaot
             Standard deviation of the normal distribution for this stat
             
        avg: float
            Value provided in the loot table
            
        modifier: float
            Modifier value provided in the loot table.
            
        stat_key: str
            name of the stat.
            e.g.
            'Mass'

        Returns
        -------
        cdf_value: flat
            Normal CDF or percentile value of the stat

        Purpose
        -------
        From the normal distribution of this component stat as defined in the loot tables (avg, modifier) and the get bell function, calculate the Cumulative Distribution Function (CDF) value (percentile)
        of the stat value, x.
        '''
        if stat_key == 'Booster_Energy':
            # The variance is so low that they're bascially all the same.
            return 0.0
            #return (x - avg + modifier) / (2.0 * modifier)
        else:
            return 0.5 * (1.0 + math.erf((x - mean) / (np.sqrt(2) * stdev)))
        
    
    def get_modifier_name(self, stat_key):
        '''
        Purpose
        -------
        The Modifier value of a particular stat (which is related to the variance) as listed in the loot tables is the stat name with either Mod or Modifier tacked on the end. This function appends the correct suffix
        to the loot table name.
        '''
        if stat_key == 'Armor':
            modifier_suffix = 'Mod'
        else:
            modifier_suffix = 'Modifier'
        modifier_name = stat_key + modifier_suffix
        return modifier_name, modifier_suffix
    
    
    def add_modifier_name_to_translation_dct(self):
        '''
        Purpose
        -------
        The stat keys are already added to loot table translaction dict manually. But the corresponding Modifier (related to variance) name can be added programatically to the dict with this function.
        '''        
        for loot_table_name, stat_key in list(self.loot_table_translation.items()):
            modifier_name, modifier_suffix = self.get_modifier_name(stat_key)
            self.loot_table_translation[loot_table_name + modifier_suffix] = modifier_name


    def get_stats(self, img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col):
        '''
        Parameters
        ----------
        img_arr: np.array, shape: (1030, 771)
            Screenshot matrix (with top border removed) which has been Grayscaled with the same cutoff (sharpenening) value as the image matrix it will be compared to.
            
        corner_description_idx: list of int
            [row, col] index of the img_arr of the swg_window for the top of the leftmost line bounding the item description area in the inventory.
            
        first_indentation_level_col: int
            The leftmost column (pixel) index of a character (in the img_arr matrix). This usually applies to the component type and reverse engineering level.
            
        second_indentation_level_col: int
            The leftmost column (pixel) index of a character (in the img_arr matrix). This usually applies to a component stat name.

        Purpose
        -------
        Get the stats from a component that is selected in an inventory and visible.
        '''
        self.cdf_value_dct = {}
        for stat_key in self.stats:
            if 'Mod' in stat_key:
                continue
            if stat_key == 'named_component':
                self.stats[stat_key] = get_name_header(corner_description_idx, img_arr=img_arr)
                continue
            if stat_key == 'Reverse_Engineering_Level':
                col = first_indentation_level_col
            else:
                col = second_indentation_level_col
            row = find_str_on_image_given_col(inventory_dct[stat_key], img_arr, col, row_start=corner_description_idx[0])
            if row is None:
                raise Exception('Could not find', stat_key)
            # Now that the row of the stat is found, we need to get the stat value.
            # The stat value will be somewhere to the right of the right edge of inventory_dct[stat_key] and will be to the
            # left of width_of_description_pane. Note that Droid_Command_speed is actually on the next line below inventory_dct['Droid_Command_Speed'].
            if stat_key == 'Droid_Command_Speed':
                row += 13
                col += 3
            else:
                col += inventory_dct[stat_key].shape[1]
            line_arr = img_arr[row : row + inventory_dct['period'].shape[0], col : width_of_description_pane + corner_description_idx[1]]
            digits = get_number_from_arr(line_arr, numeric_type=float)
            if type(digits) is list:
                # This usually happens when a slash is encountered. We're only interested in the number after the slash in this case so take the 1th element.
                self.stats[stat_key] = digits[1]
            elif stat_key == 'Reverse_Engineering_Level':
                self.stats[stat_key] = int(digits)
            else:
                self.stats[stat_key] = digits
                
                
    def read_loot_table(self, loot_table_fpath):
        '''
        Parameters
        ----------
        loot_table_fpath: str
            Path of the loot table tsv file (tab separated).

        Purpose
        -------
        The loot tables (one for each component type) have been downloaded from the swg github. This function reads a desired one into self.loot_talbe_df
        and names the columns something more viable.
        '''
        self.loot_table_df = pd.read_csv(loot_table_fpath, delimiter='\t')
        # Remove first line because there's nothing useful on it.
        self.loot_table_df = self.loot_table_df.iloc[1: , :]
        # Get just the component name in each row as opposed to its path
        self.loot_table_df.loc[:, 'strType'] = [file_utils.fname_from_fpath(self.loot_table_df.strType.iloc[f]) for f in range(len(self.loot_table_df.loc[:, 'strType']))]
        self.loot_table_df.rename(columns={'strType': 'named_component'}, inplace=True)
        # Convert numeric columns to float
        for i in range(2, len(self.loot_table_df.columns)):
            self.loot_table_df.iloc[:, i] = self.loot_table_df.iloc[:, i].astype(float)
        self.loot_table_df.rename(columns=self.loot_table_translation, inplace=True)
        
        
    def recorded_stats_df_init(self):
        if self.recorded_stats_df is None:
            recorded_stats_init = {recorded_stats_name: [] for recorded_stats_name in self.recorded_stats_names}
            self.recorded_stats_df = pd.DataFrame(recorded_stats_init)


    def update_recorded_stats_df(self):
        '''
        Purpose
        -------
        Append a new row to recorded_stats_df which contains the values of the stats on the current loot piece. Delete any duplicate rows in the dataframe. A duplicate row is most likely due to running the program
        on the same loot piece more than once, because every stat value and name would have to match for the row to be a duplicate.
        '''
        self.recorded_stats_df = self.recorded_stats_df.append(self.stats, ignore_index=True)
        self.recorded_stats_df.drop_duplicates(subset=None, keep='first', inplace=True)
        
        
class Armor(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = []
        
        
class Booster(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Energy_Drain', 'Booster_Energy', 'Booster_Recharge_Rate', 'Booster_Energy_Consumption_Rate', 'Acceleration', 'Top_Booster_Speed']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyMaintenance'] = 'Reactor_Energy_Drain'
        self.loot_table_translation['fltMaximumEnergy'] = 'Booster_Energy'
        self.loot_table_translation['fltRechargeRate'] = 'Booster_Recharge_Rate'
        self.loot_table_translation['fltConsumptionRate'] = 'Booster_Energy_Consumption_Rate'
        self.loot_table_translation['fltAcceleration'] = 'Acceleration'
        self.loot_table_translation['fltMaxSpeed'] = 'Top_Booster_Speed'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Energy_Drain'] = False
        self.higher_is_better_dct['Booster_Energy'] = True
        self.higher_is_better_dct['Booster_Recharge_Rate'] = True
        self.higher_is_better_dct['Booster_Energy_Consumption_Rate'] = False
        self.higher_is_better_dct['Acceleration'] = True
        self.higher_is_better_dct['Top_Booster_Speed'] = True
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,4,5,6,7,8,9,10]
        

class Capacitor(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Energy_Drain', 'Capacitor_Energy', 'Recharge_Rate']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyMaintenance'] = 'Reactor_Energy_Drain'
        self.loot_table_translation['fltMaxEnergy'] = 'Capacitor_Energy'
        self.loot_table_translation['fltRechargeRate'] = 'Recharge_Rate'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Energy_Drain'] = False
        self.higher_is_better_dct['Capacitor_Energy'] = True
        self.higher_is_better_dct['Recharge_Rate'] = True
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,9]
        
                
class Droid_Interface(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Energy_Drain', 'Droid_Command_Speed']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyMaintenance'] = 'Reactor_Energy_Drain'
        self.loot_table_translation['fltCommandSpeed'] = 'Droid_Command_Speed'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Energy_Drain'] = False
        self.higher_is_better_dct['Droid_Command_Speed'] = False
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,4,5,6,7,8,9,10]
        

class Engine(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Energy_Drain', 'Pitch_Rate_Maximum', 'Yaw_Rate_Maximum', 'Roll_Rate_Maximum', 'Engine_Top_Speed']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyMaintenance'] = 'Reactor_Energy_Drain'
        self.loot_table_translation['fltMaxPitch'] = 'Pitch_Rate_Maximum'
        self.loot_table_translation['fltMaxYaw'] = 'Yaw_Rate_Maximum'
        self.loot_table_translation['fltMaxRoll'] = 'Roll_Rate_Maximum'
        self.loot_table_translation['fltMaxSpeed'] = 'Engine_Top_Speed'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Energy_Drain'] = False
        self.higher_is_better_dct['Pitch_Rate_Maximum'] = True
        self.higher_is_better_dct['Yaw_Rate_Maximum'] = True
        self.higher_is_better_dct['Roll_Rate_Maximum'] = True
        self.higher_is_better_dct['Engine_Top_Speed'] = True
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,4,5,7,9]
        
        
class Reactor(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Generation_Rate']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyGeneration'] = 'Reactor_Generation_Rate'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Generation_Rate'] = True
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [9]
        
        
class Shield(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Energy_Drain', 'Front_Shield_Hitpoints', 'Back_Shield_Hitpoints', 'Shield_Recharge_Rate']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyMaintenance'] = 'Reactor_Energy_Drain'
        self.loot_table_translation['fltShieldHitpointsMaximumFront'] = 'Front_Shield_Hitpoints'
        self.loot_table_translation['fltShieldHitpointsMaximumBack'] = 'Back_Shield_Hitpoints'
        self.loot_table_translation['fltShieldRechargeRate'] = 'Shield_Recharge_Rate'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Energy_Drain'] = False
        self.higher_is_better_dct['Front_Shield_Hitpoints'] = True
        self.higher_is_better_dct['Back_Shield_Hitpoints'] = True
        self.higher_is_better_dct['Shield_Recharge_Rate'] = True
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,4,5,9]
        

class Weapon(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_names += ['Reactor_Energy_Drain', 'Min_Damage', 'Max_Damage', 'Vs_Shields', 'Vs_Armor', 'Energy_Per_Shot', 'Refire_Rate']
        self.stats_dct_init()
        
        self.loot_table_translation['fltEnergyMaintenance'] = 'Reactor_Energy_Drain'
        self.loot_table_translation['fltMinDamage'] = 'Min_Damage'
        self.loot_table_translation['fltMaxDamage'] = 'Max_Damage'
        self.loot_table_translation['fltShieldEffectiveness'] = 'Vs_Shields'
        self.loot_table_translation['fltArmorEffectiveness'] = 'Vs_Armor'
        self.loot_table_translation['fltEnergyPerShot'] = 'Energy_Per_Shot'
        self.loot_table_translation['fltRefireRate'] = 'Refire_Rate'
        self.add_modifier_name_to_translation_dct()
        
        self.higher_is_better_dct['Reactor_Energy_Drain'] = False
        self.higher_is_better_dct['Min_Damage'] = True
        self.higher_is_better_dct['Max_Damage'] = True
        self.higher_is_better_dct['Vs_Shields'] = True
        self.higher_is_better_dct['Vs_Armor'] = True
        self.higher_is_better_dct['Energy_Per_Shot'] = False
        self.higher_is_better_dct['Refire_Rate'] = False
        
        self.recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,4,9]


def item_radial_option(item_coords, radial_option='1'):
    '''
    Parameters
    ----------
    item_coords: list of int
        Monitor coordinates [x, y] of the item that is in a container.

    radial_option: str
        String of the int that is the radial option number to select.

    Purpose
    -------
    Radial an item that is visible (the window is on top) in a container and
    then select the radial option provided.
    '''
    click(item_coords, button='right')
    pdi.press(radial_option)
    time.sleep(0.2)
    
    
def drop_item_and_move_up(item_coords, radial_option='2'):
    '''
    Parameters
    ----------
    item_coords : TYPE
        DESCRIPTION.
    radial_option : TYPE, optional
        DESCRIPTION. The default is '2'.

    Returns
    -------
    None.

    '''
    item_radial_option(item_coords, radial_option=radial_option)
    # Close inventory
    pdi.press('i')
    # Put mouse into non-free moving mode
    pdi.press('alt')
    # Move item to ceiling to get it out of the way. We cannot just put into a bin since sometimes bulky items (containers) come out of crates.
    chat('/move up 250')
    # Re-open inventory
    pdi.press('i')
        
        
def item_is_container(corner_description_idx, first_indentation_level_col,  img_arr):
    '''
    Parameters
    ----------
    corner_description_idx: list of int
        [row, col] index of the img_arr of the swg_window for the top of the leftmost line bounding the item description area in the inventory.
        
    first_indentation_level_col: int
        The leftmost column (pixel) index of a character (in the img_arr matrix). This usually applies to the component type and reverse engineering level.
        
    img_arr : TYPE
        DESCRIPTION.

    Returns
    -------
    True: The currently selected item is a container.
    False: O/w

    Purpose
    -------
    Determine whether the item currently selected is a container or not.
    
    Method
    ------
    If an item is a container, it will have the 'Contents' attribute in the description pane. See if the attribute exists for the currently selected item.
    '''
    col = first_indentation_level_col
    row = find_str_on_image_given_col(inventory_dct['Contents'], img_arr, col, row_start=corner_description_idx[0])
    return (row is not None)


def close_hopper():
    '''
    Returns
    -------
    None
    
    Purpose
    -------
    Activate the currently open hopper window in order to close it.
    '''
    global currently_open_hopper
    if currently_open_hopper is not None:
        # Close hopper
        time.sleep(0.2)
        chat('/open ' + currently_open_hopper)
        time.sleep(0.2)
        pdi.press('esc')
        currently_open_hopper = None
        time.sleep(0.2)


def sort_inventory(generic_component, component_dct, sorting_crates=False, will_sort_crates=False):
    '''
    Purpose
    -------
    When there are ship components, reward crates, collection items, or other 
    items in the inventory, put these items in the correct container in your
    house to empty the inventory except for non-space related things.
    
    Notes
    -----
    1. Position inventory such that there are num_inventory_cols columns and 
    all items are visible and the left corner is tucked away in the left corner 
    of the swg_window.
    
    2. The inventory is assumed to be open before running this function.
    
    3. It is assumed you are in the house containing the containers for the 
    various types of items, and that you are nearby these containers.
    
    4. Make invnentory, backpack, and droid inventories be 10 rows by 9 cols
    with the upper left corner of description section showing as well as the 
    bottom edge along the bottom of the screen. This needs to encapsulate all 
    contents without scrolling.
    Make input hopper or other containers have 10 rows and 10 cols with upper 
    left corner of description section showing and the right edge along the 
    right edge of the screen. The capcity numbers must be showing at the bottom
    right. The hopper windows must not go all the way to the bottom (but almost)/
    '''
    global starting_inventory_position
    component_type_id_dct = {'Booster_Energy':'booster', 'Capacitor_Energy':'capacitor', 'Droid_Command_Speed':'droid_interface', 'Engine_Top_Speed':'engine', 'Reactor_Generation_Rate':'reactor', 'Shield_Recharge_Rate':'shield', 'Energy_Per_Shot':'weapon'}
    # Get the top left corner indices of img_arr
    corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
    first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
    second_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level
    
    item_count, item_capacity = get_item_count_and_capacity(region, img_arr=None)
    item_inventory_position = deepcopy(starting_inventory_position)
    for i in range(starting_inventory_position, item_count + num_equipped_items - num_items_in_bulky_containers):
        item_coords = get_item_coords(corner_description_idx, region, item_inventory_position)
        # Click on item
        click(item_coords, button='left', start_delay=0.05, return_delay=0.9)
        # Get screenshot
        img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                scale_to=255, sharpen=True, set_focus=False)
        found_name = None
        for name in inventory_dct:
            if '_name' not in name:
                continue
            if find_str_on_image_given_col(inventory_dct[name], img_arr, first_indentation_level_col, row_start=corner_description_idx[0]) is not None:
                # Remove the '_name' portion
                found_name = name[:-5]
                break
        if found_name is None:
            # First check to see if it has Reverse_Engineering_Level stat (cuz all loot components will have this stat). It's possible that there is no description such that found_name is None but it actually is a component.
            col = first_indentation_level_col
            row = find_str_on_image_given_col(inventory_dct['Reverse_Engineering_Level'], img_arr, col, row_start=corner_description_idx[0])
            if row is None:
                # Non-space related item or no item at all.
                if sorting_crates:
                    # See if no item at all
                    # Close and re-open inventory
                    pdi.press('i')
                    pdi.press('i')
                    # Get name header
                    click(item_coords, button='left', start_delay=0.05, return_delay=1.5)
                    inventory_corner_description_idx, inventory_img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
                    name_header = get_name_header(inventory_corner_description_idx, img_arr=inventory_img_arr)
                    # The inventory string is offset differently than item strings so get_name_header will return '  ' if no item is selected.
                    if name_header == '  ':
                        # There was truly no item at all there.
                        item_inventory_position += 1
                        break
                    if item_is_container(inventory_corner_description_idx, first_indentation_level_col, inventory_img_arr):
                        # This will be unnecessary when use a hopper which can contain containers
                        drop_item_and_move_up(item_coords, radial_option='3')
                    else:
                        # Move item to non-space component hopper
                        generic_component.store_loot_in_hopper(item_coords, 'non_components')
                        # Activate the inventory
                        pdi.press('i', presses=2)
                        drag_mouse(autoit_dir, start_coords=item_coords, end_coords=into_hopper_coords, num_drags=1, delay_return=0.75)
                        # Activate non-space component hopper and close it.
                        close_hopper()
                else:
                    # Skip
                    item_inventory_position += 1
                continue
            else:
                # It is a space component. Find out which type.
                for stat_key in component_type_id_dct:
                    row = find_str_on_image_given_col(inventory_dct[stat_key], img_arr, col, row_start=corner_description_idx[0])
                    if row is not None:
                        found_name = component_type_id_dct[stat_key]
                        break
                # Armor only has mass and armor which are common to all other components and so must be identified separately.
                if found_name is None:
                    found_name = 'armor'
        if 'crate' in found_name:
            # Move crate to crate container.
            generic_component.store_loot_in_hopper(item_coords, 'crate')
            continue
        elif 'collection' in found_name:
            # Move crate to crate container.
            generic_component.store_loot_in_hopper(item_coords, 'collection')
            continue
        elif found_name not in component_dct:
            continue
        component = component_dct[found_name]
        component.get_stats(img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col)
        component.get_max_loot_percentile_value_stc()
        if component.worth_keeping():
            # Put into hopper.
            # (For now don't worry about whether it's full, that's a TODO for later)
            component.store_loot_in_hopper(item_coords, 'good_loot')
        elif component.component_type == 'droid_interface':
            component.store_loot_in_hopper(item_coords, 'junk_droid_interface')
        elif not will_sort_crates:
            # If not going to sort crates then can just keep junk items in inventory because you only need to remove junk to hopper to make way for opening crates.
            item_inventory_position += 1
        else:
            component.store_loot_in_hopper(item_coords, 'junk_loot')
        component.update_recorded_stats_df()
        component.recorded_stats_df.to_csv(component.recorded_stats_fpath, index=False)
    starting_inventory_position = deepcopy(item_inventory_position)
    close_hopper()
        
        
def sort_backpack(generic_component, component_dct):
    '''
    Purpose
    -------
    When there are ship components, reward crates, collection items, or other 
    items in the inventory, put these items in the correct container in your
    house to empty the inventory except for non-space related things.
    
    Notes
    -----
    1. Position inventory such that there are num_inventory_cols columns and 
    all items are visible and the left corner is tucked away in the left corner 
    of the swg_window.
    
    2. The inventory is assumed to be open before running this function.
    
    3. It is assumed you are in the house containing the containers for the 
    various types of items, and that you are nearby these containers.
    
    4. Make invnentory, backpack, and droid inventories be 10 rows by 9 cols
    with the upper left corner of description section showing as well as the 
    bottom edge along the bottom of the screen. This needs to encapsulate all 
    contents without scrolling.
    Make input hopper or other containers have 10 rows and 10 cols with upper 
    left corner of description section showing and the right edge along the 
    right edge of the screen. The capcity numbers must be showing at the bottom
    right. The hopper windows must not go all the way to the bottom (but almost)/
    
    5. Backpack is already open.
    '''
    global starting_backpack_position
    # Get the top left corner indices of img_arr
    corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
    first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
    second_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level

    item_inventory_position = deepcopy(starting_backpack_position)
    item_count = generic_component.backpack_item_count
    for i in range(starting_backpack_position, item_count):
        item_coords = get_item_coords(corner_description_idx, region, item_inventory_position)
        # Click on item
        click(item_coords, button='left', start_delay=0.05, return_delay=0.9)
        # Get screenshot
        img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                scale_to=255, sharpen=True, set_focus=False)
        found_name = None
        for name in inventory_dct:
            if '_name' not in name:
                continue
            if find_str_on_image_given_col(inventory_dct[name], img_arr, first_indentation_level_col, row_start=corner_description_idx[0]) is not None:
                # Remove the '_name' portion
                found_name = name[:-5]
                break
        if found_name is None:
            # Non-space related item. Skip
            item_inventory_position += 1
            continue
        if 'crate' in found_name:
            # Move crate to crate container.
            generic_component.store_loot_in_hopper(item_coords, 'crate')
            continue
        elif 'collection' in found_name:
            # Move crate to crate container.
            generic_component.store_loot_in_hopper(item_coords, 'collection')
            continue
        elif found_name not in component_dct:
            continue
        component = component_dct[found_name]
        component.backpack_item_count = generic_component.backpack_item_count
        component.backpack_coords = generic_component.backpack_coords
        component.get_stats(img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col)
        component.get_max_loot_percentile_value_stc()
        if component.worth_keeping():
            # Put into hopper.
            # (For now don't worry about whether it's full, that's a TODO for later)
            component.store_loot_in_hopper(item_coords, 'good_loot')
        elif component.component_type == 'droid_interface':
            component.store_loot_in_hopper(item_coords, 'junk_droid_interface')
        else:
            item_inventory_position += 1
        component.update_recorded_stats_df()
        component.recorded_stats_df.to_csv(component.recorded_stats_fpath, index=False)
    starting_backpack_position = deepcopy(item_inventory_position)
    # Close backpack
    pdi.press('esc')
    close_hopper()
    
    
def sort_droid_inventory(generic_component, component_dct):
    '''
    Purpose
    -------
    When there are ship components, reward crates, collection items, or other 
    items in the inventory, put these items in the correct container in your
    house to empty the inventory except for non-space related things.
    
    Notes
    -----
    1. Position inventory such that there are num_inventory_cols columns and 
    all items are visible and the left corner is tucked away in the left corner 
    of the swg_window.
    
    2. The inventory is assumed to be open before running this function.
    
    3. It is assumed you are in the house containing the containers for the 
    various types of items, and that you are nearby these containers.
    
    4. Make invnentory, backpack, and droid inventories be 10 rows by 9 cols
    with the upper left corner of description section showing as well as the 
    bottom edge along the bottom of the screen. This needs to encapsulate all 
    contents without scrolling.
    Make input hopper or other containers have 10 rows and 10 cols with upper 
    left corner of description section showing and the right edge along the 
    right edge of the screen. The capcity numbers must be showing at the bottom
    right. The hopper windows must not go all the way to the bottom (but almost)/
    '''
    # Get the top left corner indices of img_arr
    corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
    first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
    second_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level
    
    item_count, item_capacity = get_item_count_and_capacity(region, img_arr=None)
    item_inventory_position = 0
    for i in range(item_count):
        item_coords = get_item_coords(corner_description_idx, region, item_inventory_position)
        # Click on item
        click(item_coords, button='left', start_delay=0.05, return_delay=0.9)
        # Get screenshot
        img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                scale_to=255, sharpen=True, set_focus=False)
        found_name = None
        for name in inventory_dct:
            if '_name' not in name:
                continue
            if find_str_on_image_given_col(inventory_dct[name], img_arr, first_indentation_level_col, row_start=corner_description_idx[0]) is not None:
                # Remove the '_name' portion
                found_name = name[:-5]
                break
        if found_name is None:
            # Non-space related item. Skip
            item_inventory_position += 1
            continue
        if 'crate' in found_name:
            # Move crate to crate container.
            generic_component.store_loot_in_hopper(item_coords, 'crate')
            continue
        elif 'collection' in found_name:
            # Move crate to crate container.
            generic_component.store_loot_in_hopper(item_coords, 'collection')
            continue
        elif found_name not in component_dct:
            continue
        component = component_dct[found_name]
        component.get_stats(img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col)
        component.get_max_loot_percentile_value_stc()
        if component.worth_keeping():
            # Put into hopper.
            # (For now don't worry about whether it's full, that's a TODO for later)
            component.store_loot_in_hopper(item_coords, 'good_loot')
        elif component.component_type == 'droid_interface':
            component.store_loot_in_hopper(item_coords, 'junk_droid_interface')
        else:
            item_inventory_position += 1
        component.update_recorded_stats_df()
        component.recorded_stats_df.to_csv(component.recorded_stats_fpath, index=False)
    close_hopper()
    
    
    
def sort_crates(generic_component, component_dct, reopen_inventory=True):
    '''
    Purpose
    -------
    One at a time, move a crate from the crates hopper to the inventory and 
    then sort the inventory, until there are no more crates in the hopper.
    
    Notes
    -----
    1. Assumes inventory is open when this function is called.
    
    2. Assumes by this point you have enough inventory space to unpack 1 crate.
    '''
    global starting_inventory_position
    # Close inventory
    pdi.press('i')
    # For now, only 1 crates hopper, crates0.
    # Open the crates hopper.
    chat('/open clothing')
    time.sleep(0.3)
    # Get the number of crates in there.
    item_count, item_capacity = get_item_count_and_capacity(region, img_arr=None, start_row=25, start_col=600)
    for i in range(item_count):
        corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
        crate_coords = get_item_coords(corner_description_idx, region, 0)
        # Pick up crate (place into inventory)
        item_radial_option(crate_coords, radial_option='1')
        # Open inventory
        pdi.press('i')
        time.sleep(0.4)
        corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
        inventory_item_count, inventory_item_capacity = get_item_count_and_capacity(region, img_arr=img_arr)
        # Open crate
        starting_inventory_position = max(starting_inventory_position, 0)
        item_coords = get_item_coords(corner_description_idx, region, starting_inventory_position)
        item_radial_option(item_coords, radial_option='1')
        sort_inventory(generic_component, component_dct, sorting_crates=True, will_sort_crates=True)
        # Close inventory
        pdi.press('i')
    # Close crates hopper
    pdi.press('esc')
    if reopen_inventory:
        # Reopen inventory
        pdi.press('i')
    close_hopper()
    
    
def get_backpack_item_count():
    '''
    Purpose
    -------
    Open the backpack and get the backpack_item_count so you can then run sort_inventory using the backpack.
    
    Notes
    -----
    1. Assumes inventory is already open before calling this function.
    '''
    corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
    backpack_coords = get_item_coords(corner_description_idx, region, backpack_inventory_position)
    # Open the backpack
    item_radial_option(backpack_coords, radial_option='1')
    time.sleep(0.4)
    corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
    backpack_item_count, item_capacity = get_item_count_and_capacity(region, img_arr=img_arr)
    return backpack_item_count, backpack_coords
    

def put_junk_into_caravan(backpack_coords=None):
    '''
    Parameters
    ----------
    backpack_coords: list of int or None
        [x, y] position on monitor of the backpack item in the inventory.
        If None then it is assumed you are putting junk into another container other than the backpack.

    Purpose
    -------
    Put items from the space junk hopper into a caravan container such as backpack, inventory, or pit droid so it can be taken away to the chassis dealer.

    Notes
    -----
    1. Inventory must be open before calling this function.
    2. If you're calling this function for an inventory droid, then its inventory must be open (or at least, the droid must be out and located at into_inventory_coords)
    '''
    print('entered caravan function')
    global junk_hopper_i, all_done
    done = False
    if backpack_coords is not None:
        # Open backpack
        item_radial_option(backpack_coords, radial_option='1')
    while not done:
        # Get number of items that can be put into caravan still
        caravan_item_count, caravan_item_capacity = get_item_count_and_capacity(region)
        caravan_items_remaining = caravan_item_capacity - caravan_item_count
        # Open junk hopper
        chat('/open Loot_' + str(junk_hopper_i))
        time.sleep(0.4)
        # Get number of items in hopper
        hopper_item_count, hopper_item_capacity = get_item_count_and_capacity(region, img_arr=None, start_row=25, start_col=600)
        all_done = hopper_item_count == 0
        print('caravan_item_count, caravan_item_capacity, caravan_items_remaining', caravan_item_count, caravan_item_capacity, caravan_items_remaining)
        num_items_to_move_from_hopper_to_caravan = min(caravan_items_remaining, hopper_item_count)
        print('hopper_item_count, hopper_item_capacity, num_items_to_move_from_hopper_to_caravan', hopper_item_count, hopper_item_capacity, num_items_to_move_from_hopper_to_caravan)
        corner_description_idx, img_arr = find_inventory_dct_item_on_region(region, 'top_left_corner_of_description_section_130_threshold')
        item_coords = get_item_coords(corner_description_idx, region, 0)
        for i in range(num_items_to_move_from_hopper_to_caravan):
            # Move items into caravan
            drag_mouse(autoit_dir, start_coords=item_coords, end_coords=into_inventory_coords, num_drags=1, delay_return=0.5)
        # Close hopper
        pdi.press('esc')
        # If number of items in junk hopper was the number to move, then the caravan had at least enough space or more. Thus all items in
        # the hopper were transferred to the caravan, so we can decrement junk_hopper_i and proceed to move items from that hopper to the caravan.
        # But if junk_hopper_i is 0, then don't decrement cuz we're done.
        if hopper_item_count == num_items_to_move_from_hopper_to_caravan:
            if junk_hopper_i == 0:
                done = True
            else:
                junk_hopper_i -= 1
        else:
            # Here means the caravan did not have enough space to hold all the items in the junk hopper, so we're done with this function
            done = True
    if backpack_coords is not None:
        # Close backpack
        pdi.press('esc')
        
def open_droid_inventory():
    '''
    Purpose
    -------
    Look at and radial the droid and select the option to open its inventory.

    Notes
    -----
    1. The droid must already be called out.
    '''
    # Bring up the radial menu for the droid which allows you to select the droid inventory
    chat('/ui action radialMenu')
    time.sleep(1.1)
    # Get current mouse position
    mouse_x, mouse_y = pag.position()
    pdi.moveTo(mouse_x + 105, mouse_y - 55, duration=0.1)
    time.sleep(1.1)
    mouse_x, mouse_y = pag.position()
    click([mouse_x, mouse_y - 45], return_delay=1.5)
    
    
        
def deal_with_droids(generic_component, component_dct):
    '''
    Parameters
    ----------
        
    Return
    ------
    None
    
    Purpose
    -------
    For each inventory droid, open its inventory, sort the components in there, sort the crates gotten from there.
    '''
    global starting_inventory_position
    # Close inventory
    pdi.press('i')
    # Iterate through the droids on the toolbar
    for d in range(pit_droid_i, num_pit_droids):
        # call the droid
        chat('/ui action toolbarSlot' + str(d).zfill(2))
        time.sleep(2)
        # open the droid's inventory
        open_droid_inventory()
        # Move crates to crate hopper, good loot to its hopper, and leave junk in the droid's inventory
        sort_droid_inventory(generic_component, component_dct)
        # Open inventory
        pdi.press('i')
        starting_inventory_position -= 1
        # Sort inventory to destroy collection items
        sort_inventory(generic_component, component_dct)
        # unpack and sort crates in the hopper
        sort_crates(generic_component, component_dct, reopen_inventory=False)
        # Move junk to droid
        put_junk_into_caravan()
        # store the droid
        chat('/ui action toolbarSlot' + str(d).zfill(2))
        # Close droid inventory
        pdi.press('esc')
        time.sleep(0.2)
    # Open inventory
    pdi.press('i')
        
        
def query_cdf_value(component=None, stats_dct=None, component_type=None, re_lvl=None, stat_key=None, stat_value=None, verbose=False):
    component_dct = {'armor': Armor(), 'booster': Booster(), 'capacitor': Capacitor(), 'droid_interface': Droid_Interface(),
                'engine': Engine(), 'reactor': Reactor(), 'shield': Shield(), 'weapon': Weapon()}
    
    if component is None:
        component = component_dct[component_type]
    if stats_dct is not None:
        component_type = component.__class__.__name__.lower()
        re_lvl = str(stats_dct['Reverse_Engineering_Level'])
    if verbose:
        pprint(extreme_avg_and_modifier_dct[component_type][re_lvl])
    if stats_dct is not None:
        for stat_key, stat_value in stats_dct.items():
            if verbose:
                print(stat_key, stat_value)
            cdf_value = component.get_cdf_value(stat_value, extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['mean'], 
                              extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['stdev'], 
                              extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['Avg'], 
                              extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['Modifier'], 
                              stat_key)
            
            if not component.higher_is_better_dct[stat_key]:
                cdf_value = 1.0 - cdf_value
            if verbose:
                print('cdf_value', cdf_value)
            return cdf_value
    
    else:
        cdf_value = component.get_cdf_value(stat_value, extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['mean'], 
                              extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['stdev'], 
                              extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['Avg'], 
                              extreme_avg_and_modifier_dct[component_type][re_lvl][stat_key]['Modifier'], 
                              stat_key)
        
        if not component.higher_is_better_dct[stat_key]:
            cdf_value = 1.0 - cdf_value
        if verbose:
            print('cdf_value', cdf_value)
        return  cdf_value
    
    
def get_value_of_desired_percentile(component=None, stats_dct=None, component_type=None, re_lvl=None, stat_key=None, desired_percentile=None, iterator_magnitude=10, start_value=0):
    '''
    Purpose
    -------
    component: sub-class of Ship_Component
        Ship component object
        e.g.
        Engine()
        
    stats_dct: dict
        Keys: names of the stats of a component
        Values: values of the stats of a component
    '''
    component_dct = {'armor': Armor(), 'booster': Booster(), 'capacitor': Capacitor(), 'droid_interface': Droid_Interface(),
                'engine': Engine(), 'reactor': Reactor(), 'shield': Shield(), 'weapon': Weapon()}
    
    if component is None:
        component = component_dct[component_type]
    if stats_dct is not None:
        component_type = component.__class__.__name__.lower()
        re_lvl = str(stats_dct['Reverse_Engineering_Level'])
    if component.higher_is_better_dct[stat_key]:
        iterator = iterator_magnitude
    else:
        iterator = -1 * iterator_magnitude
    stat_value = start_value
    cdf_value = 0
    while cdf_value < desired_percentile:
        cdf_value = query_cdf_value(component=component, stats_dct=stats_dct, component_type=component_type, re_lvl=re_lvl, stat_key=stat_key, stat_value=stat_value, verbose=False)
        stat_value += iterator
    print('stat_value', round(stat_value,1))
    
    
def orient():
    '''
    pit_droid_pane: int
        The toolbar pane that has all your inventory droids placed in the slots in contiguous order.
    
    Returns
    -------
    None
    
    Purpose
    -------
    Scroll all the way in and face the ground so that your cursor will align with the pit droid so you can open up its inventory. This function makes sure the toolbar pane that has the pit droids is active.
    
    Notes
    -----
    1. The inventory droids can also be on the extra (vertical) toolbar pane (if you have that many)
    2. Do not have inventory already open when this function starts
    3. Do not be in free-moving mouse mode already when this function starts
    '''
    # Switch to toolbar pane 6 where the droids are
    pdi.keyDown('ctrl')
    pdi.press(str(pit_droid_pane))
    pdi.keyUp('ctrl')
    # Scroll (zoom) all the way in
    for _ in range(50):
        pag.scroll(100)
    # Get to free-moving mouse mode
    pdi.press('alt')
    # Drag mouse so that you are facing directly down
    #drag_mouse(autoit_dir=autoit_dir,
    #        start_coords=[int(rect.left + rect.width()/2), rect.top + rect.height()],
    #        end_coords=[int(rect.left + rect.width()/2), int(rect.top + 2.5 * rect.height())],
    #        num_drags=1)
    
    
    pdi.moveRel(xOffset=0, yOffset=-50)
    
    # Get back out of free-move mouse mode
    pdi.press('alt')
    # Open inventory
    pdi.press('i')
    # activate inventory window
    click(inventory_activation_coords, button='left', start_delay=0.3, return_delay=0.3)
    
    
def sort_loot_when_in_house(sorting_desires_dct):
    '''
    sorting_desires_dct: dict
    What to sort.
    'inventory': bool
    'backpack': bool
    'crates': bool
    'droids': bool
    
    Note: if crates is True then inventory must also be True to make sure there is room to unpack crates.
    
    generic_component: Ship_Component
        An instance of Ship_Component instead of Armor, Booster, etc. This object is used to use the methods of Ship_Component without creating an actual component object.
        
    component_dct: dict
        keys: 'armor', 'booster', 'capacitor', 'droid_interface', 'engine', 'reactor', 'shield', 'weapon'
        values: Armor(), Booster(), etc
        
        One Armor() object will be passed around for use in all functions.
        
    Returns
    -------
    None

    Purpose
    -------
    While standing in your house next to all hoppers, sort raw space loot and crates into their appropriate hoppers and then fill the backpack,inventory, and droid inventories with what junk space components you can
    fit so that you can take them to the chassis dealer.
    
    Notes
    -----
    1. Have the inventory open before calling this function.
    '''
    if sorting_desires_dct['crates'] and not sorting_desires_dct['inventory']:
        raise Exception('If crates need to be sorted, then inventory needs to be sorted')
    swg_window.set_focus()
    generic_component = Ship_Component()
    # Set up an object for each component type
    component_dct = {'armor': Armor(), 'booster': Booster(), 'capacitor': Capacitor(), 'droid_interface': Droid_Interface(),
                'engine': Engine(), 'reactor': Reactor(), 'shield': Shield(), 'weapon': Weapon()}
    
    orient()
    
    if sorting_desires_dct['inventory']:
        sort_inventory(generic_component, component_dct, will_sort_crates=sorting_desires_dct['crates'])
        # At this point, inventory is empty of space items.
    if sorting_desires_dct['crates']:
        # One by one, put crates from hopper into inventory and sort inventory.
        sort_crates(generic_component, component_dct, reopen_inventory=True)
    if sorting_desires_dct['backpack']:
        # Open backpack and then sort it as if it were the inventory
        backpack_item_count, backpack_coords = get_backpack_item_count()
        generic_component.backpack_item_count = backpack_item_count
        generic_component.backpack_coords = backpack_coords
        sort_backpack(generic_component, component_dct)
        if sorting_desires_dct['crates']:
            sort_crates(generic_component, component_dct, reopen_inventory=True)
    # Now, put as much junk loot from the hoppers into the backpack as possible.
    put_junk_into_caravan(generic_component.backpack_coords)
    if sorting_desires_dct['droids']:
        # Now, sort droid inventories
        deal_with_droids(generic_component, component_dct)
    # Put as much junk loot from the hoppers into the inventory as possible
    put_junk_into_caravan()
    # Close inventory
    pdi.press('esc')
# Global vars set by user
'''
sorting_desires_dct: dict
    What to sort.
    'inventory': bool
    'backpack': bool
    'crates': bool
    'droids': bool
    
    Note: if crates is True then inventory must also be True to make sure there is room to unpack crates.

starting_inventory_position: int
    Position in the inventory (0-indexed) of the first space related item (as opposed to other things in the inventory like clothing).
    
num_equipped_items: int
    Number of items your toon has equipped (including equipped appearance). These are items that show up in the inventory but do not count towards the 80 limit.
    A backpack only counts as 1.
    
num_items_in_bulky_containers: int
    Number of items inside containers (not including the container itself) that are not equipped 
    
num_pit_droids: int
    Number of pit droids. This is 1 plus the maximum value of pit_droid_i. i.e. num_pit_droids is the number of droids used for storage of space loot starting from pit_droid_i = 0.
    These droids must be on the toolbar in the same order as the toolbarSlot index on toolbarPane pit_droid_pane.
    
    e.g.
    You have 30 pit droids, and the starting pit_droid_i you want to use is 2 (meaning the 1st and 2nd droid should be skipped) and the last droid available for storing component loot is the 25th droid.
    (droids 26-30 are used for storage of something else). Then the max value of pit_droid_i will be 23 so num_pit_droids will be 24. (Even if the skipped ones at the beginning are not used for space loot).
    
pit_droid_pane: int
        The toolbar pane that has all your inventory droids placed in the slots in contiguous order.
        
starting_backpack_position: int
    Position in the backpack (0-indexed) of the first space related item (as opposed to other things in the inventory like clothing).
    
junk_hopper_i: int
    The lowest junk loot hopper name index (e.g. 0 for Loot_0) that is not full.
    
pit_droid_i: int
    The lowest 0-indexed inventory droid as ordered by toolbarSlot that you want to start from when sorting the inventory droids.
    
droid_interface_hopper_i: int
    The lowest DI hopper name index (e.g. 0 for DIs_0) that is not full.
    
non_components_hopper_i: int
    The lowest name index (e.g. 0 for non_components_0) for the hopper of items gotten from a crate that are not ship components.
    
backpack_inventory_position:
    Position in the inventory (0-indexed) of the equipped backpack.
    
autoit_dir: str
    Path of the directory containing drag_mouse.exe which is an autoit program for dragging the mouse.
    
Constants
---------
digit_height: int
    Number of pixels that each digit in the item description window is tall.
    
num_cols_from_left_side_to_first_indentation_level: int
    Number of pixels from the left edge of the item description pane (which is the column that top_left_corner_of_description_section_130_threshold is found) to the leftmost column (pixel) of a character.
    This usually applies to the component type and reverse engineering level.
    
num_cols_from_left_side_to_second_indentation_level: int
    Number of pixels from the left edge of the item description pane (which is the column that top_left_corner_of_description_section_130_threshold is found) to the leftmost column (pixel) of a digit.
    This usually applies to a component stat.
    
width_of_description_pane: The (maximimum) width (number of pixels) of the description pane. The max is when the inventory window is stretched horizontally.

num_inventory_cols: int
    The number of columns of items in the appropriately placed and sized inventory panes. (See notes)
    
num_hopper_cols: int
    The number of columns of items in the appropriately placed and sized hopper panes. (See notes)

num_cols_from_right_corner_col_to_start_of_item_count: int
    Number of pixels from the column (in the pixel, screenshot matrix) that lower_right_corner is found to the column to the left that can be used as the start column to search for the item count of an open container.
    
num_rows_from_right_corner_row_to_start_of_item_count: int
    Number of pixels from the row (in the pixel, screenshot matrix) that lower_right_corner is found to the row below that can be used as the start row to search for the item count of an open container.
    
into_hopper_coords: list of int
    [x,y] coordinates on the screen where items can be dragged into a hopper window.
    
into_inventory_coords: list of int
    [x,y] coordinates on the screen where items can be dragged into an inventory window.
    
inventory_activation_coords: list of int
    [x,y] coordinates on the screen where an inventory window can be clicked to activate it (bring it to foreground).
    
currently_open_hopper: str or None
    If None, no hopper is currently open. Else, this will be the name of the open hopper. There should only be 1 hopper open at a time.
    
extreme_avg_and_modifier_dct: dict
    See get_extreme_avg_and_modifier_combo_for_stats() docs.
    
Notes
-----
1. starting_inventory_position, junk_hopper_i, pit_droid_i, and non_components_hopper_i are used so that the program doesn't have to start at index 0 and figure out where the first space related item is or which
    hopper is not full. (Although it will automatically if starting_inventory_position is set to 0).
    
2. The inventory should be placed and sized such that the name of the item appears on the top bar, it has num_inventory_cols columns of items (9 is good for default icon size), the number of item contents out
    of 80 are visible (in the lower right corner), and the inventory window extends to the bottom of the swg window. Droid inventory windows and the backpack window should also follow this positioning scheme.
    
3. The storage hopper windows should be sized and placed such that the height is minimize, the width is maximized, and the top left corner of the description pane is visible.
'''
starting_inventory_position = 26
num_equipped_items = 24
num_items_in_bulky_containers = 13
num_pit_droids = 22
pit_droid_pane = 6
starting_backpack_position = 0
junk_hopper_i = 0
# Index of starting droid to investigate. num_droids is still total number of droids including those not wished to be investigated (minus any at the end that don't have space stuff, if any)
pit_droid_i = 15
droid_interface_hopper_i = 0
non_components_hopper_i = 0
collection_hopper_i = 0
backpack_inventory_position = 0
autoit_dir=r'D:\autoit\swg\REing'
# Constants
digit_height = 7
num_cols_from_left_side_to_first_indentation_level = 7
num_cols_from_left_side_to_second_indentation_level = 27
width_of_description_pane = 263
num_inventory_cols = 9
num_hopper_cols = 10
num_cols_from_right_corner_col_to_start_of_item_count = 60
num_rows_from_right_corner_row_to_start_of_item_count = 25
# Coords of where to drag items into a hopper
into_hopper_coords = [region['left'] + 950, region['top'] + 50]
# Coords of where to drag items into an inventory
into_inventory_coords = [region['left'] + 500, region['top'] + 350]
inventory_activation_coords = [region['left'] + 50, region['top'] + 763]
currently_open_hopper = None
all_done = False
extreme_avg_and_modifier_dct = get_extreme_avg_and_modifier_combo_for_stats(extreme_avg_and_modifier_json_dir=r'D:\python_scripts\swg\loot_tables\extreme_values', 
        loot_table_dir=r'D:\python_scripts\swg\dsrc\sku.0\sys.server\compiled\game\datatables\ship\components')

if __name__ == '__main__':
    '''
    sorting_desires_dct = {
'inventory': True, 'backpack': True, 'crates': False, 'droids': True
    }
    sort_loot_when_in_house(sorting_desires_dct)
    '''
    swg_window.set_focus()
    time.sleep(0.5)
    #pdi.press('alt')
    #pdi.moveRel(xOffset=0, yOffset=10)
    #pdi.press('alt')
    #orient()
    sorting_desires_dct = {
'inventory': True, 'backpack': True, 'crates': True, 'droids': False
    }
    round_trip_i = 0
    while not all_done:
        sort_loot_when_in_house(sorting_desires_dct)
        if all_done:
            break
        go_to_chassis_dealer.go_to_chassis_dealer(calibrate_to_north=round_trip_i == 0)
        round_trip_i += 1
    #pass
    #for lvl in list(range(1,11))[::-1]:
    #    for percentile in [0.95, 0.96, 0.97, 0.98, 0.99, 0.999, 0.9999, 0.99999]:
    #        get_value_of_desired_percentile(component_type='droid_interface', re_lvl=str(lvl), stat_key='Droid_Command_Speed', desired_percentile=percentile, iterator_magnitude=0.1, start_value=50)
'''
Done
. Check the number of items in a crate container (e.g. travel pack). Note, containers that can be examined have a "Item Count" attribute and "/exmaine crates0" works.
. Check the number of items in a given input hopper.

TODO
. Make invnentory, backpack, and droid inventories be 10 rows by 9 cols with the upper left corner of description section showing as well as the bottom edge along the bottom of the screen. This needs to encapsulate all contents without scrolling.
. Make input hopper or other containers have 10 rows and 10 cols with upper left corner of description section showing and the right edge along the right edge of the screen. The capcity numbers must be showing at the bottom right.
#. The examine window (gotten by /examine name) must have the upper left corner of description section showing and be wide enough that "Item Count" value can be read on the same line.
. Make input hoppers for junk that will be put back into pit droids be 1 row and 10 columns

. Start with the inventory, putting crates into bags (or ideally another hopper).
. Put junk parts in inventory into separate container (another hopper).
. When inventory is empty of space stuff, one at a time, put a crate into inventory and sort.
. When all crates in hopper are gone, sort backpack as if it were the inventory.
. When backpack is empty of space stuff, fill it with as much junk loot as possible.
. One at a time, open a pit droid and pick up all its contents and then sort the inventory. Before moving on to the next droid, fill its inventor with junk parts.

. Deal with full good loot hoppers, junk loot hoppers, non-space hoppers, or crate hoppers
. Deal with when house is full (could happen if sorting crates).
'''
