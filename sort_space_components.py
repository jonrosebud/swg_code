# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 17:41:08 2021
@author: trose
"""
from copy import deepcopy
import string, os
import random
from pprint import pprint
import pandas as pd
import numpy as np
import math
import pyautogui as pag
import pydirectinput_tmr as pdi
import time
from config_utils import Instruct
import socket
config_fpath = os.path.join('..', 'swg_config_file_for_' + socket.gethostname() + '.conf')
config = Instruct(config_fpath)
config.get_config_dct()
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils
git_path = config.config_dct['main']['git_path']
onedrive_path = config.config_dct['main']['onedrive_path']
sys.path.append(r"" + git_path)
import swg_utils
import swg_window_management as swm
import run_waypoint_path as rwp
import go_to_chassis_dealer as gtc
from pynput.keyboard import Listener, Key

win_pressed=False
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
inventory_arr_dir = os.path.join(git_path, 'inventory_dir') #usually sharpened at 145
inventory_dct = {
         fname : file_utils.read_csv(os.path.join(inventory_arr_dir, fname + '.csv'), dtype=int)
        for fname in ['cargo_crate_name', 'military_crate_name', 'collection_name',
        'Armor', 'Mass', 'Reverse_Engineering_Level', 'Reactor_Energy_Drain', 'Reactor_Generation_Rate',
        'Booster_Energy', 'Booster_Recharge_Rate', 'Booster_Energy_Consumption_Rate',
        'Acceleration', 'Top_Booster_Speed', 'Capacitor_Energy', 'Recharge_Rate',
        'Droid_Command_Speed', 'Pitch_Rate_Maximum', 'Yaw_Rate_Maximum', 
        'Roll_Rate_Maximum', 'Engine_Top_Speed', 'Front_Shield_Hitpoints', 
        'Back_Shield_Hitpoints', 'Shield_Recharge_Rate', 'Min_Damage', 'Max_Damage', 'Vs_Shields',
        'Vs_Armor', 'Energy_Per_Shot', 'Refire_Rate', 'Contents', 'period', 'slash', 'dash',
        'top_left_corner_of_description_section_130_threshold', 'container_down_arrow_130_thresh', 'show_description_toggle_100_threshold',
        'square_bracket', 'item_count_130_thresh', 'Flawed', 'Damaged', 'Seized', 'Faulty', 'Salvaged', 'Amount', 'Charges_130'] +
        list(map(str, range(10)))
        }

character_arr_dir = os.path.join(git_path, 'character_dir')
character_names_dct = {
    fname : file_utils.read_csv(os.path.join(character_arr_dir, fname + '.csv'), dtype=int)
        for fname in list(string.ascii_uppercase) + list(map(str, range(10))) 
        + ['and', 'open_parenthesis', 'close_parenthesis', 'dash', 'period', 'slash', 'space']
    }

land_ui_arr_dir = os.path.join(git_path, 'land_ui_dir')
land_ui_dct = {
        fname : file_utils.read_csv(os.path.join(inventory_arr_dir, fname + '.csv'), dtype=int)
        for fname in ['meters_m', 'Rosethorn_group_member_225']
        }

swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
swg_window = swm.swg_windows[swg_window_i]
region = swm.swg_window_regions[swg_window_i]
        

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


def find_str_on_image_given_col(str_arr, img_arr, col, start_row=0):
    '''
    Parameters
    ----------
    str_arr: np.array, variable shape
         Grayscaled (and sharpened) screenshot matrices the string you want to find. The shape is just enough to encapsulate the string.
        
    img_arr: np.array, shape: (1030, 771)
        Screenshot matrix of the swg_window (with top border removed) which has been Grayscaled and sharpened with the same cutoff as used in str_arr when it was made.
        
    col: int
        The column that you believe str_arr should be found on img_arr
        
    start_row: int
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
    for row in range(start_row, img_arr.shape[0] - str_arr.shape[0]):
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
    
    
    '''
    digits = ''
    for i in range(line_arr.shape[1]):
        for digit_key in ['slash', 'dash', 'square_bracket', 'period'] + list(map(str,range(10))):
           target_arr = line_arr[:, i: i + inventory_dct[digit_key].shape[1]]
           if target_arr.shape[1] != inventory_dct[digit_key].shape[1]:
               continue
           if np.all(target_arr == inventory_dct[digit_key]):
               if digit_key == 'slash':
                   digits += '/'
               elif digit_key == 'dash':
                   digits += '-'
               elif digit_key == 'square_bracket':
                   # Should only get here when looking at a container
                   digits = digits.split('/')
                   return [numeric_type(digits[0]), numeric_type(digits[1])]
               elif digit_key == 'period':
                   digits += '.'
               else:
                   digits += digit_key
    if '/' in digits:
        digits = digits.split('/')
        return [numeric_type(digits[0]), numeric_type(digits[1])]
    if '-' in digits:
        digits = digits.split('-')
        return [numeric_type(digits[0]), numeric_type(digits[1])]
    return numeric_type(digits)


def get_str_from_arr(line_arr):
        '''
        line_arr: 2D np.array
            This matrix must be the same height (number of rows) as the stored
            char matrices in character_names_dct. line_arr contains some of the
            char matrices in character_names_dct which will be read sequentially
            to get the overall (single) number.
            
        Returns
        -------
        digits: str
            The string read in line_arr
        
        Purpose
        -------
        Use character_names_dct to put togehter all characters in the string in line_arr. (image to text recognition).
        '''
        i = 0
        char_start_col = 0
        char_end_col = 0
        result = ''
        # Iterate through the columns of line_arr
        for i in range(line_arr.shape[1]):
            # Iterate through all the stored character matrices to see if one
            # matches.
            for key, arr in character_names_dct.items():
                # Generate target_arr as the portion of line_arr with the same shape as arr
                target_arr = line_arr[:,i:i+arr.shape[1]]
                # If still doesnt have the same shape, then you are nearing the end of the line_arr.
                if arr.shape[1] != target_arr.shape[1]:
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
                    elif key == 'space':
                        result += ' '
                    else:
                        result += key
        result = np.array(result.split(' '))
        result = list(result[np.where(result != '')])
        result = ' '.join(result)
        return result
    
    
def find_and_get_stat(search_arr, region=None, img_arr=None, start_row=0, start_col=0, end_row=None, end_col=None, fail_gracefully=False, sharpen_threshold=130, return_as_tuple=False, n_matches=None, abs_diff_tol=0, dtype=float, corner_description_idx=np.array([36,12])):
    width_of_description_pane = 263
    found_idx, img_arr = swg_utils.find_arr_on_region(search_arr, region=region, img_arr=img_arr, start_row=start_row, start_col=start_col, end_row=end_row, end_col=end_col, fail_gracefully=fail_gracefully, sharpen_threshold=sharpen_threshold, return_as_tuple=return_as_tuple, n_matches=n_matches, abs_diff_tol=abs_diff_tol)
    if found_idx is None:
        return None
    row, col = found_idx
    line_arr = img_arr[row : row + search_arr.shape[0], col + search_arr.shape[1] : width_of_description_pane + corner_description_idx[1]]
    if dtype is list:
        numeric_type = int
    else:
        numeric_type = dtype
    digits = get_number_from_arr(line_arr, numeric_type=numeric_type)
    if type(digits) is list and dtype is not list:
        # This usually happens when a slash is encountered. We're only interested in the number after the slash in this case so take the 1th element.
        return dtype(digits[1])
    else:
        return dtype(digits)
    
    
def get_item_count_and_capacity(region, img_arr=None, start_row=600, start_col=600, fail_gracefully=False):
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
    # Move to bottom of the window so cursor wont cause something to appear over the numbers.
    swg_utils.moveTo(coords=[region['left'] + region['width'] - 10, region['top'] + region['height'] - 10])
    time.sleep(0.5)
    # Get lower right corner indices of container window in img_arr
    down_arrow_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['container_down_arrow_130_thresh'], region=region, img_arr=img_arr, start_row=start_row, start_col=start_col, sharpen_threshold=130, fail_gracefully=fail_gracefully)
    if down_arrow_idx is None:
        return None, None, None
    start_of_item_count_idx = np.array([down_arrow_idx[0] + down_arrow_to_start_of_item_count_offset[0], down_arrow_idx[1] - down_arrow_to_start_of_item_count_offset[1]])
    # Get the container item count.
    line_arr = img_arr[start_of_item_count_idx[0] : digit_height + down_arrow_idx[0] + down_arrow_to_start_of_item_count_offset[0], 
            start_of_item_count_idx[1] : down_arrow_idx[1]]
    
    item_count, item_capacity = get_number_from_arr(line_arr, numeric_type=int)
    return item_count, item_capacity, down_arrow_idx
    
    
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
    named_component_offset = np.array([-33, -3]) + np.array([int(config.config_dct['main']['named_component_row_offset']), 0])
    named_component_idx = named_component_offset + corner_description_idx
    named_component_row_length = 800
    named_component_height = 10
    line_arr = img_arr[named_component_idx[0] : named_component_idx[0] + named_component_height, named_component_idx[1] : named_component_idx[1] + named_component_row_length]
    result = get_str_from_arr(line_arr).strip()
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
            stc_fpath = os.path.join('..', 'STC', self.component_type + '_stc.csv')
            self.stc_df = pd.read_csv(stc_fpath, dtype=float)
            self.stc_df = self.stc_df.astype({'Reverse_Engineering_Level': int})
        
        # Once enough of my own data has been collected, I'll use my own percentiles.
        # Collect data by keeping track of component stats
        self.recorded_stats_fpath = os.path.join('..', 'STC', self.component_type + '_recorded_stats.csv')
        if os.path.exists(self.recorded_stats_fpath):
            self.recorded_stats_df = pd.read_csv(self.recorded_stats_fpath)
            if len(self.recorded_stats_df) > 0:
                type_dct = {col_name:float for col_name in self.recorded_stats_df.columns if col_name != 'named_component'}
                type_dct['Reverse_Engineering_Level'] = int
                self.recorded_stats_df = self.recorded_stats_df.astype(type_dct)
        else:
            file_utils.mkdir_if_DNE(os.path.join('..', 'STC'))
            # The sub-classes will take care of instantiating it.
            self.recorded_stats_df = None
            
        # Do the same thing for good recorded stats
        self.good_recorded_stats_fpath = os.path.join(onedrive_path, 'swg_good_loot', self.component_type + '_good_recorded_stats.xlsx')
        if os.path.exists(self.good_recorded_stats_fpath):
            self.good_recorded_stats_df = pd.read_excel(self.good_recorded_stats_fpath)
            if len(self.good_recorded_stats_df) > 0:
                type_dct = {col_name:float for col_name in self.good_recorded_stats_df.columns if col_name != 'named_component' and col_name != 'good_stats'}
                type_dct['Reverse_Engineering_Level'] = int
                self.good_recorded_stats_df = self.good_recorded_stats_df.astype(type_dct)
        else:
            # The sub-classes will take care of instantiating it.
            self.good_recorded_stats_df = None
            
        self.recorded_stats_names = list(self.stats.keys())
        # Default
        self.REable = True
            
        
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
        return self.max_loot_percentile_value >= keep_percentile - 0.00000000001 and (self.stats['Reverse_Engineering_Level'] not in self.usually_bad_re_lvls or self.max_loot_percentile_value >= 0.999998999999998)
        
        
    def store_loot_in_hopper(self, item_coords, hopper_type, sorting_inventory, calibrator=None):
        '''
        Parameters
        ----------
        item_coords: list of int
            Monitor coordinates [x, y] of the item that is in the inventory.
            
        hopper_type: str
            Options are 'junk_loot', 'good_loot', 'crate', 'junk_droid_interface', 'non_components'
            Determines where the item in the inventory gets placed.
            
        sorting_inventory: bool
            True: You are sorting the inventory and this function will close and open the inventory
            False: You are sorting a droid or a backpack or a pack and so this container will be activated by clicking at the bottom.
        Purpose
        -------
        Store the loot item in the appropriate input hopper.
        '''
        global junk_hopper_i
        global droid_interface_hopper_i
        global non_components_hopper_i
        global collection_hopper_i
        global currently_open_hopper
        global crate_hopper_i
        global currently_open_hopper_item_count
        # Determine which intput hopper to open
        # Deal with multiple good loot hoppers (the index like _0, _1, etc) later.
        hc = Hopper_Calibrator()
        opened_new_hopper = False
        if hopper_type == 'good_loot':
            hopper_name = self.component_type[0].upper() + str(self.stats['Reverse_Engineering_Level'])[-1] + '_0'
        elif hopper_type == 'junk_loot':
            hopper_name = 'Loot_' + str(junk_hopper_i)
        elif hopper_type == 'crate':
            hopper_name = 'Crates_' + str(crate_hopper_i)
        elif hopper_type == 'DIscanners':
            # Never going to have more than 1 DIscanner hopper
            hopper_name = 'DIscanners_0'
        elif hopper_type == 'junk_droid_interface':
            hopper_name = 'DIs_' + str(droid_interface_hopper_i)
        elif hopper_type == 'non_components':
            # Check if it is a stackable item and if so, put it in that bin instead of non_components hopper
            name_header = get_name_header(calibrator.corner_description_idx, img_arr=None)
            if 'CONVOY FLIGHT PLAN' in name_header:
                hopper_name = 'stackable_crate_loot_0'
            else:
                hopper_name = 'non_components_' + str(non_components_hopper_i)
        elif hopper_type == 'collection':
            num_tiers_per_collection_hopper = 2
            found_collection_name = None
            collection_names = ['Flawed', 'Damaged', 'Seized', 'Faulty', 'Salvaged']
            img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                    scale_to=255, sharpen=True, set_focus=False)
            
            # Determine which tier the collection item is.
            for collection_i, collection_name in enumerate(collection_names):
                row = find_str_on_image_given_col(inventory_dct[collection_name], img_arr, calibrator.first_indentation_level_col, start_row=calibrator.corner_description_idx[0])
                if row is not None:
                    found_collection_name = collection_name
                    break
            if found_collection_name is None:
                # Collection name is not in the space collection list. Assume it is a non-space collection item and destroy it.
                item_radial_option(item_coords, radial_option='3')
            collection_hopper_i = int(collection_i / num_tiers_per_collection_hopper)
            hopper_name = 'collections_' + str(collection_hopper_i)
        if currently_open_hopper != hopper_name:
            close_hopper()
            # Open desired hopper
            swg_utils.chat('/open ' + hopper_name)
            time.sleep(0.2)
            opened_new_hopper = True
            currently_open_hopper = deepcopy(hopper_name)
        # Check to see if we filled it up.
        if opened_new_hopper:
            currently_open_hopper_item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=100, start_col=880)
        # 100 is item_capacity of a hopper
        while currently_open_hopper_item_count == 100:
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
            elif hopper_type == 'crate':
                crate_hopper_i += 1
                hopper_name = 'Crates_' + str(crate_hopper_i)
            # Open new hopper
            swg_utils.chat('/open ' + hopper_name)
            time.sleep(0.2)
            opened_new_hopper = True
            currently_open_hopper = deepcopy(hopper_name)
            currently_open_hopper_item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=100, start_col=880)
        if opened_new_hopper:
            if sorting_inventory:
                # activate inventory window
                pdi.press('i', presses=2)
            else:
                # Activate container window
                if calibrator is not None:
                    swg_utils.click(coords_idx=calibrator.desired_lower_right_corner_idx, button='left', start_delay=0.1, return_delay=0.1, window=swg_window, region=region)
                else:
                    swg_utils.click(coords=caravan_activation_coords, button='left', start_delay=0.1, return_delay=0.1)
        # Drag item from inventory to the hopper.
        swg_utils.click_drag(start_coords=item_coords, end_coords=hc.into_coords, num_drags=1, start_delay=0.0, return_delay=0.75)
        currently_open_hopper_item_count += 1
        
        
    def get_max_loot_percentile_value_stc(self):
        '''
        Purpose
        -------
        Of all the stats on a particular loot piece, find the one with the highest percentile and store the highest percentile into self.max_loot_percentile_value. The percentiles are based off of the STC file instead
        of the distribution from the loot tables because it is unclear how to combine the distributions of a given component type and RE level into one distribution. However, eventually I'll have enough loot recorded
        that I can use the empirical percentiles. For now, use the STC file as an approximation. Also, keep track of all stats with good percentile values.
        '''
        self.good_loot_percentile_dct = {}
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
            if stat_key == 'Armor' and self.component_type != 'armor':
                if percentile > 0.99999:
                    self.max_loot_percentile_value = max(self.max_loot_percentile_value, percentile)
                    if percentile >= keep_percentile:
                        self.good_loot_percentile_dct[stat_key] = percentile
            else:
                self.max_loot_percentile_value = max(self.max_loot_percentile_value, percentile)
                if percentile >= keep_percentile:
                    self.good_loot_percentile_dct[stat_key] = percentile
        
        
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
            # Subtract 1 from row number because digits have a blank line above them (so that square bracket can be found).
            row = find_str_on_image_given_col(inventory_dct[stat_key], img_arr, col, start_row=corner_description_idx[0]) # - 1
            if row is None:
                if stat_key == 'Reverse_Engineering_Level':
                    self.REable = False
                    return
                raise Exception('Could not find', stat_key)
            # Now that the row of the stat is found, we need to get the stat value.
            # The stat value will be somewhere to the right of the right edge of inventory_dct[stat_key] and will be to the
            # left of width_of_description_pane. Note that Droid_Command_speed is actually on the next line below inventory_dct['Droid_Command_Speed'].
            if stat_key == 'Droid_Command_Speed':
                row += 13
                col += 3
            else:
                col += inventory_dct[stat_key].shape[1]
            line_arr = img_arr[row : row + inventory_dct[stat_key].shape[0], col : width_of_description_pane + corner_description_idx[1]]
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
        if self.stats['named_component'] is None or self.stats['named_component'] == '' or self.stats['named_component'] == np.nan:
            print('Got an unnamed component with self.stats:', self.stats)
            return
        self.recorded_stats_df = self.recorded_stats_df.append(self.stats, ignore_index=True)
        self.recorded_stats_df.drop_duplicates(subset=None, keep='first', inplace=True)
        self.recorded_stats_df.to_csv(self.recorded_stats_fpath, index=False)
        
        
    def good_recorded_stats_df_init(self):
        if self.good_recorded_stats_df is None:
            recorded_stats_init = {recorded_stats_name: [] for recorded_stats_name in self.recorded_stats_names + ['good_stats', 'initial_price', 'sold_price', 'price_id']}
            self.good_recorded_stats_df = pd.DataFrame(recorded_stats_init)


    def update_good_recorded_stats_df(self):
        '''
        Purpose
        -------
        Append a new row to good_recorded_stats_df which contains the values of the stats on the current loot piece. Delete any duplicate rows in the dataframe. A duplicate row is most likely due to running the program
        on the same loot piece more than once, because every stat value and name would have to match for the row to be a duplicate.
        '''
        if self.stats['named_component'] is None or self.stats['named_component'] == '' or self.stats['named_component'] == np.nan:
            print('Got an unnamed component with self.stats:', self.stats)
            return
        if not self.worth_keeping():
            return
        good_stats = deepcopy(self.stats)
        good_stats['good_stats'] = ', '.join(list(self.good_loot_percentile_dct.keys()))
        if good_stats['good_stats'] == '':
            return
        good_stats['initial_price'] = 0.0
        good_stats['sold_price'] = 0.0
        good_stats['price_id'] = 0.0
        self.good_recorded_stats_df = self.good_recorded_stats_df.append(good_stats, ignore_index=True)
        self.good_recorded_stats_df.drop_duplicates(subset=self.recorded_stats_names, keep='first', inplace=True)
        file_utils.rm(self.good_recorded_stats_fpath)
        self.good_recorded_stats_df.to_excel(self.good_recorded_stats_fpath, index=False)


def merge_onedrive_files(self):
    # Sometimes Onedrive will make a second copy because it couldnt merge for some reason. Its fname will have a hostname appended. Merge this with the original     
    self.good_recorded_stats_fpath = os.path.join(onedrive_path, 'swg_good_loot', self.component_type + '_good_recorded_stats.xlsx')
    good_recorded_stats_fname = set(file_utils.fname_from_fpath(self.good_recorded_stats_fpath))
    similar_fnames = set([file_utils.fname_from_fpath(fpath) for fpath in file_utils.find(os.path.dirname(self.good_recorded_stats_fpath), good_recorded_stats_fname + '*.xlsx')])
    unmerged_fnames = similar_fnames - good_recorded_stats_fname
    unmerged_fpaths = [os.path.join(os.path.dirname(self.good_recorded_stats_fpath), unmerged_fname + '.xlsx') for unmerged_fname in unmerged_fnames]
    for unmerged_fpath in unmerged_fpaths:
        unmerged_df = pd.read_excel(unmerged_fpath)
        if len(unmerged_df) > 0:
            type_dct = {col_name:float for col_name in unmerged_df.columns if col_name != 'named_component' and col_name != 'good_stats'}
            type_dct['Reverse_Engineering_Level'] = int
            unmerged_df = unmerged_df.astype(type_dct)
        self.good_recorded_stats_df = self.good_recorded_stats_df.append(unmerged_df, ignore_index=True)
        self.good_recorded_stats_df.drop_duplicates(subset=self.recorded_stats_names, keep='first', inplace=True)
        file_utils.rm(unmerged_fpath)
    self.good_recorded_stats_df.drop_duplicates(subset=self.recorded_stats_names, keep='first', inplace=True)
    file_utils.rm(self.good_recorded_stats_df)
    self.good_recorded_stats_df.to_excel(self.good_recorded_stats_fpath, index=False)
       
        
class Armor(Ship_Component):
    def __init__(self):
        super().__init__()
        self.recorded_stats_df_init()
        self.good_recorded_stats_df_init()
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
        self.good_recorded_stats_df_init()
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
        self.good_recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,5,7,9]
        
                
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
        self.good_recorded_stats_df_init()
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
        self.good_recorded_stats_df_init()
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
        self.good_recorded_stats_df_init()
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
        self.good_recorded_stats_df_init()
        self.usually_bad_re_lvls = [1,2,3,4,9]
        

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
        self.good_recorded_stats_df_init()
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
    swg_utils.click(coords=item_coords, button='right', start_delay=0.1, return_delay=1.2)
    pdi.press(radial_option)
    time.sleep(0.2)
    
    
def get_item_container_item_count_and_capacity(corner_description_idx, first_indentation_level_col,  img_arr):
    '''
    Parameters
    ----------
    corner_description_idx: list of int
        [row, col] index of the img_arr of the swg_window for the top of the leftmost line bounding the item description area in the inventory.
        
    first_indentation_level_col: int
        The leftmost column (pixel) index of a character (in the img_arr matrix). This usually applies to the component type and reverse engineering level.
        
    img_arr: TYPE
        DESCRIPTION.
    Returns
    -------
    
    
    Purpose
    -------
    Get item count and item capacity of the selected item if it is a container. If it is not a container, return None, None
    
    Method
    ------
    If an item is a container, it will have the 'Contents' attribute in the description pane. See if the attribute exists for the currently selected item.
    '''
    
    item_count_and_capacity = find_and_get_stat(inventory_dct['Contents'], region=region, img_arr=img_arr, start_row=corner_description_idx[0], start_col=first_indentation_level_col, end_col=first_indentation_level_col, fail_gracefully=True, dtype=list, corner_description_idx=corner_description_idx)
    if item_count_and_capacity is None:
        return None, None
    else:
        item_count, item_capacity = item_count_and_capacity
        return item_count, item_capacity

        
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
        swg_utils.chat('/open ' + currently_open_hopper)
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
    
    4. Make inventory, backpack, and droid inventories be 10 rows by 9 cols
    with the upper left corner of description section showing as well as the 
    bottom edge along the bottom of the screen. This needs to encapsulate all 
    contents without scrolling.
    Make input hopper or other containers have 10 rows and 10 cols with upper 
    left corner of description section showing and the right edge along the 
    right edge of the screen. The capcity numbers must be showing at the bottom
    right. The hopper windows must not go all the way to the bottom (but almost)/
    '''
    global starting_inventory_position
    calibrator = Inventory_Calibrator()
    component_type_id_dct = {'Booster_Energy':'booster', 'Capacitor_Energy':'capacitor', 'Droid_Command_Speed':'droid_interface', 'Engine_Top_Speed':'engine', 'Reactor_Generation_Rate':'reactor', 'Shield_Recharge_Rate':'shield', 'Energy_Per_Shot':'weapon'}
    # Get the top left corner indices of img_arr
    corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
    first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
    second_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level
    
    item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None)
    item_inventory_position = deepcopy(starting_inventory_position)
    end_inventory_position = item_count + num_equipped_items - num_items_in_bulky_containers
    while item_inventory_position < end_inventory_position:
        item_coords = get_item_coords(corner_description_idx, region, item_inventory_position)
        # Click on item
        img_arr = swg_utils.click_on_item(region, item_coords=item_coords, sub_region=calibrator.description_region)
        # Check to see whether it is a pack containing ship component loot
        inventory_corner_description_idx, inventory_img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
        container_item_count, container_item_capacity = get_item_container_item_count_and_capacity(inventory_corner_description_idx, first_indentation_level_col, inventory_img_arr)
        if container_item_count is not None:
            # If sorting_crates, then container is likely a cargo container that needs to be stored.
            if sorting_crates:
                # Move container to non-space component hopper
                generic_component.store_loot_in_hopper(item_coords, 'non_components', True, calibrator=calibrator)
            elif container_item_count > 0:
                # Sort through this pack
                # Open pack
                item_radial_option(item_coords, radial_option='1')
                # Sort pack
                sort_backpack(generic_component, component_dct, True)
                # Pack is closed at the end of sort_backpack
                end_inventory_position -= container_item_count
                item_inventory_position += 1
                continue
        found_name = get_name(img_arr, calibrator, 'house', item_coords)
        if found_name is None:
            # Non-space related item or no item at all.
            if sorting_crates or will_sort_crates:
                # See if no item at all
                # Close and re-open inventory
                pdi.press('i')
                pdi.press('i')
                # Get name header
                swg_utils.click(coords=item_coords, button='left', start_delay=0.2, return_delay=0.4)
                inventory_corner_description_idx, inventory_img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
                name_header = get_name_header(inventory_corner_description_idx, img_arr=inventory_img_arr)
                # The inventory string is offset differently than item strings so get_name_header will return '  ' if no item is selected.
                if name_header == '  ':
                    # There was truly no item at all there.
                    break
                # Move item to non-space component hopper
                generic_component.store_loot_in_hopper(item_coords, 'non_components', True, calibrator=calibrator)
                # Activate non-space component hopper and close it.
                close_hopper()
                end_inventory_position -= 1
            else:
                # Skip
                item_inventory_position += 1
            continue
        elif found_name in ['crate', 'collection']:
            end_inventory_position -= 1
            continue
        component = component_dct[found_name]
        component.get_stats(img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col)
        if not component.REable:
            item_inventory_position += 1
            continue
        component.get_max_loot_percentile_value_stc()
        if component.worth_keeping():
            # Put into hopper.
            # (For now don't worry about whether it's full, that's a TODO for later)
            component.store_loot_in_hopper(item_coords, 'good_loot', True, calibrator=calibrator)
            end_inventory_position -= 1
        elif component.component_type == 'droid_interface':
            component.store_loot_in_hopper(item_coords, 'junk_droid_interface', True, calibrator=calibrator)
            end_inventory_position -= 1
        elif not will_sort_crates:
            # If not going to sort crates then can just keep junk items in inventory because you only need to remove junk to hopper to make way for opening crates.
            item_inventory_position += 1
        else:
            component.store_loot_in_hopper(item_coords, 'junk_loot', True, calibrator=calibrator)
            end_inventory_position -= 1
        component.update_recorded_stats_df()
        component.update_good_recorded_stats_df()
    starting_inventory_position = deepcopy(item_inventory_position)
    close_hopper()
        
        
def sort_backpack(generic_component, component_dct, pack):
    '''
    pack: bool
        True: container is a pack that is not the main backpack (65-item capacity backpack). Instead, it is a 50-capacity pack.
        False: container is the main backpack.
        
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
    
    4. Make inventory, backpack, and droid inventories be 10 rows by 9 cols
    with the upper left corner of description section showing as well as the 
    bottom edge along the bottom of the screen. This needs to encapsulate all 
    contents without scrolling.
    Make input hopper or other containers have 10 rows and 10 cols with upper 
    left corner of description section showing and the right edge along the 
    right edge of the screen. The capcity numbers must be showing at the bottom
    right. The hopper windows must not go all the way to the bottom (but almost)/
    
    5. Backpack is already open.
    '''
    # Get the top left corner indices of img_arr
    corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
    first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
    second_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level

    item_inventory_position = 0
    if pack:
        item_count, _ = get_backpack_item_count(backpack_already_open=True)
        calibrator = Pack_Calibrator()
    else:
        item_count = generic_component.backpack_item_count
        calibrator = Backpack_Calibrator()
    end_inventory_position = deepcopy(item_count)
    while item_inventory_position < end_inventory_position:
        item_coords = get_item_coords(corner_description_idx, region, item_inventory_position)
        # Click on item
        img_arr = swg_utils.click_on_item(region, item_coords=item_coords, button='left', sub_region=calibrator.description_region)
        # Check to see whether it is a pack containing ship component loot
        inventory_corner_description_idx, inventory_img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
        container_item_count, container_item_capacity = get_item_container_item_count_and_capacity(inventory_corner_description_idx, first_indentation_level_col, inventory_img_arr)
        if container_item_count is not None and container_item_count > 0:
            # Sort through this pack
            # Open pack
            item_radial_option(item_coords, radial_option='1')
            # Sort pack
            sort_backpack(generic_component, component_dct, True)
            # Pack is closed at the end of sort_backpack
            end_inventory_position -= container_item_count
            item_inventory_position += 1
            continue
        
        found_name = get_name(img_arr, calibrator, 'house', item_coords)
        if found_name is None:
            # Non-space related item. Skip
            item_inventory_position += 1
            continue
        elif found_name in ['crate', 'collection']:
            end_inventory_position -= 1
            continue
        
        component = component_dct[found_name]
        if not pack:
            component.backpack_item_count = generic_component.backpack_item_count
            component.backpack_coords = generic_component.backpack_coords
        component.get_stats(img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col)
        if not component.REable:
            item_inventory_position += 1
            continue
        component.get_max_loot_percentile_value_stc()
        if component.worth_keeping():
            # Put into hopper.
            # (For now don't worry about whether it's full, that's a TODO for later)
            component.store_loot_in_hopper(item_coords, 'good_loot', False, calibrator=calibrator)
            end_inventory_position -= 1
        elif component.component_type == 'droid_interface':
            component.store_loot_in_hopper(item_coords, 'junk_droid_interface', False, calibrator=calibrator)
            end_inventory_position -= 1
        else:
            item_inventory_position += 1
        component.update_recorded_stats_df()
        component.update_good_recorded_stats_df()
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
    
    4. Make inventory, backpack, and droid inventories be 10 rows by 9 cols
    with the upper left corner of description section showing as well as the 
    bottom edge along the bottom of the screen. This needs to encapsulate all 
    contents without scrolling.
    Make input hopper or other containers have 10 rows and 10 cols with upper 
    left corner of description section showing and the right edge along the 
    right edge of the screen. The capcity numbers must be showing at the bottom
    right. The hopper windows must not go all the way to the bottom (but almost)/
    '''
    # Get the top left corner indices of img_arr
    corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
    first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
    second_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level
    dc = Droid_Calibrator()
    gc = Good_Loot_Calibrator()
    hc = Hopper_Calibrator()
    
    item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None)
    item_inventory_position = 0
    end_inventory_position = item_count
    while item_inventory_position < end_inventory_position:
        item_coords = get_item_coords(corner_description_idx, region, item_inventory_position)
        # Click on item
        img_arr = swg_utils.click_on_item(region, item_coords=item_coords, button='left', sub_region=dc.description_region)
        found_name = get_name(img_arr, dc, 'house', item_coords)
        if found_name is None:
            # Non-space related item. Skip
            item_inventory_position += 1
            continue
        elif found_name in ['crate', 'collection']:
            end_inventory_position -= 1
            continue
        
        component = component_dct[found_name]
        component.get_stats(img_arr, corner_description_idx, first_indentation_level_col, second_indentation_level_col)
        if not component.REable:
            item_inventory_position += 1
            continue
        component.get_max_loot_percentile_value_stc()
        if component.worth_keeping():
            # Put into hopper.
            # (For now don't worry about whether it's full, that's a TODO for later)
            component.store_loot_in_hopper(item_coords, 'good_loot', False, calibrator=gc)
            end_inventory_position -= 1
        elif component.component_type == 'droid_interface':
            component.store_loot_in_hopper(item_coords, 'junk_droid_interface', False, calibrator=hc)
            end_inventory_position -= 1
        else:
            item_inventory_position += 1
        component.update_recorded_stats_df()
        component.update_good_recorded_stats_df()
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
    swg_utils.chat('/open Crates_')
    time.sleep(0.3)
    # Get the number of crates in there.
    item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=25, start_col=600)
    for i in range(item_count):
        corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
        crate_coords = get_item_coords(corner_description_idx, region, 0)
        # Pick up crate (place into inventory)
        item_radial_option(crate_coords, radial_option='1')
        # Open inventory
        pdi.press('i')
        time.sleep(0.4)
        corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
        #inventory_item_count, inventory_item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=img_arr)
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
    
    
def get_backpack_item_count(backpack_already_open=False, close_backpack_after_done=False):
    '''
    Purpose
    -------
    Open the backpack and get the backpack_item_count so you can then run sort_inventory using the backpack.
    '''
    if not backpack_already_open:
        corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
        backpack_coords = get_item_coords(corner_description_idx, region, backpack_inventory_position)
        # Open the backpack
        item_radial_option(backpack_coords, radial_option='1')
        time.sleep(0.2)
    else:
        backpack_coords = None
    corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
    backpack_item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=img_arr)
    if close_backpack_after_done:
        pdi.press('esc')
    return backpack_item_count, backpack_coords
    

def put_items_into_caravan(backpack_coords=None, hopper_type='junk_loot', max_items_to_transfer=1e6, double_clickable=False):
    '''
    Parameters
    ----------
    backpack_coords: list of int or None
        [x, y] position on monitor of the backpack item in the inventory.
        If None then it is assumed you are putting junk into another container other than the backpack.
        
    hopper_type: str
        Hopper key string of the hopper to move items from.
    
    max_items_to_transfer: int
        Maximum number of items to transfer to caravan. Useful for only transerring 5 items for DIscanners, for example.
        
    Returns
    -------
    num_items_transferred: int
        Number of items transferred from hoppers to caravan.
        
    Purpose
    -------
    Put items from the specified hopper type into a caravan container such as backpack, inventory, or droid so it can be taken away to the chassis dealer, or used in some other way.
    
    Notes
    -----
    1. Inventory must be open before calling this function.
    2. If you're calling this function for an inventory droid, then its inventory must be open (or at least, the droid must be out and located at into_inventory_coords)
    '''
    global all_done, currently_open_hopper
    global droid_interface_hopper_i
    ic = Inventory_Calibrator()
    if hopper_type == 'junk_loot':
        hopper_i = hopper_dct['loot_'] - 1
        hopper_name_prefix = 'Loot_'
    elif hopper_type == 'junk_droid_interface':
        hopper_i = droid_interface_hopper_i
        hopper_name_prefix = 'DIs_'
    done = False
    max_items_remaining_to_transfer = int(max_items_to_transfer)
    num_items_transferred = 0
    if max_items_remaining_to_transfer < 1:
        if hopper_type == 'junk_droid_interface':
            droid_interface_hopper_i = hopper_i
        return 0
    if backpack_coords is not None:
        # Open backpack
        item_radial_option(backpack_coords, radial_option='1')
    while not done:
        hopper_name = hopper_name_prefix + str(hopper_i)
        currently_open_hopper = hopper_name
        # Get number of items that can be put into caravan still
        caravan_item_count, caravan_item_capacity, down_arrow_idx = get_item_count_and_capacity(region)
        caravan_items_remaining = caravan_item_capacity - caravan_item_count
        # Open hopper
        swg_utils.chat('/open ' + hopper_name)
        time.sleep(0.4)
        # Get number of items in hopper
        hopper_item_count, hopper_item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=25, start_col=600)
        if hopper_type == 'junk_loot':
            all_done = hopper_item_count == 0
        num_items_to_move_from_hopper_to_caravan = min(caravan_items_remaining, hopper_item_count, max_items_remaining_to_transfer)
        corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
        item_coords = get_item_coords(corner_description_idx, region, 0)
        for i in range(num_items_to_move_from_hopper_to_caravan):
            # Move items into caravan
            if double_clickable:
                swg_utils.click(coords=item_coords, presses=2, start_delay=0.1, return_delay=0.5)
            else:
                swg_utils.click_drag(start_coords=item_coords, end_coords=ic.into_coords, num_drags=1, start_delay=0.0, return_delay=0.5)
            num_items_transferred += 1
            max_items_remaining_to_transfer -=  1
            if max_items_remaining_to_transfer == 0:
                # Close hopper
                close_hopper()
                if backpack_coords is not None:
                    # Close backpack
                    pdi.press('esc')
                if hopper_type == 'junk_droid_interface':
                    droid_interface_hopper_i = hopper_i
                return num_items_transferred
        # Close hopper
        close_hopper()
        # If number of items in hopper was the number to move, then the caravan had at least enough space or more. Thus all items in
        # the hopper were transferred to the caravan, so we can decrement junk_hopper_i and proceed to move items from that hopper to the caravan.
        # But if hopper_i is 0, then don't decrement cuz we're done.
        if hopper_item_count == num_items_to_move_from_hopper_to_caravan:
            if hopper_i == 0:
                done = True
            else:
                hopper_i -= 1
                # Changed hopper so close hopper
                close_hopper()
        else:
            # Here means the caravan did not have enough space to hold all the items in the hopper, so we're done with this function
            done = True
    if backpack_coords is not None:
        # Close backpack
        pdi.press('esc')
    if hopper_type == 'junk_droid_interface':
        droid_interface_hopper_i = hopper_i
    return num_items_transferred
        
        
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
    swg_utils.chat('/ui action radialMenu')
    time.sleep(1.1)
    # Get current mouse position
    mouse_x, mouse_y = pag.position()
    pdi.moveTo(mouse_x + 105, mouse_y - 55, duration=0.1)
    time.sleep(1.1)
    mouse_x, mouse_y = pag.position()
    swg_utils.click(coords=[mouse_x, mouse_y - 45], start_delay=0.1, return_delay=1.3)
    
    
        
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
    for d in range(droid_i, num_droids):
        # call the droid
        swg_utils.chat('/ui action toolbarSlot' + str(d).zfill(2))
        time.sleep(2)
        # open the droid's inventory
        open_droid_inventory()
        # Move crates to crate hopper, good loot to its hopper, and leave junk in the droid's inventory
        sort_droid_inventory(generic_component, component_dct)
        # Open inventory
        pdi.press('i')
        starting_inventory_position -= 1
        # Sort inventory to move collection items
        sort_inventory(generic_component, component_dct)
        # unpack and sort crates in the hopper
        sort_crates(generic_component, component_dct, reopen_inventory=False)
        # Move junk to droid
        #put_items_into_caravan()   For now I want to use droids for only storing good loot
        # store the droid
        swg_utils.chat('/ui action toolbarSlot' + str(d).zfill(2))
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
    
    
def orient(open_inventory=True, zoom_in=True):
    '''
    droid_pane: int
        The toolbar pane that has all your inventory droids placed in the slots in contiguous order.
    
    Returns
    -------
    None
    
    Purpose
    -------
    Scroll all the way in and face the ground so that your cursor will align with the droid so you can open up its inventory. This function makes sure the toolbar pane that has the droids is active.
    
    Notes
    -----
    1. The inventory droids can also be on the extra (vertical) toolbar pane (if you have that many)
    2. Do not have inventory already open when this function starts
    3. Do not be in free-moving mouse mode already when this function starts
    '''
    # Switch to toolbar pane 6 where the droids are
    pdi.keyDown('ctrl')
    pdi.press(str(droid_pane))
    pdi.keyUp('ctrl')
    if zoom_in:
        # Scroll (zoom) all the way in
        for _ in range(40):
            pag.scroll(80)
    # Get to free-moving mouse mode
    # If not in free-moving mouse mode already, press alt
    non_free_moving_mouse_mode_circle_arr = swg_utils.get_search_arr('non_free_moving_mouse_mode_circle', dir_path=os.path.join(git_path, 'land_ui_dir'), mask_int=0)
    img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen=False, set_focus=False)
    if np.all(non_free_moving_mouse_mode_circle_arr == img_arr[373:373+non_free_moving_mouse_mode_circle_arr.shape[0],504:504+non_free_moving_mouse_mode_circle_arr.shape[1]]):
        pdi.press('alt')
        time.sleep(0.1)

    swg_utils.moveTo(window=swg_window, region=region, coords_idx=[region['height'] - 1, int(region['width']/2)], return_delay=0.1)
    
    pdi.moveRel(xOffset=0, yOffset=250)
    time.sleep(0.1)
    # Get back out of free-move mouse mode
    pdi.press('alt')
    if open_inventory:
        # Open inventory
        pdi.press('i')
        # activate inventory window
        swg_utils.click(coords=inventory_activation_coords, button='left', start_delay=0.1, return_delay=0.1)


class Container_Calibrator:
    def __init__(self):
        '''
        capacity: int
            Number of items the container can hold. This is used to find the lower right corner.
            
        desired_lower_right_corner_idx: list of int
            [row, col] of the final position of the lower right corner of the container window.
            
        desired_upper_left_corner_idx: list of int
            [row, col] of the final position of the upper left corner of the container window.
        '''
        self.lower_right_corner_to_start_of_item_count_offset = np.array([-110, -60])
        self.toggle_to_corner_description_offset = np.array([8, 1]) #np.array([8, -3])
        self.toggle_to_upper_left_corner_offset = np.array([-28, -11])
        self.upper_left_corner_to_corner_description_offset = self.toggle_to_corner_description_offset - self.toggle_to_upper_left_corner_offset
        self.corner_description_idx = self.desired_upper_left_corner_idx + self.upper_left_corner_to_corner_description_offset
        self.first_indentation_level_col = self.corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
        self.second_indentation_level_col = self.corner_description_idx[1] + num_cols_from_left_side_to_second_indentation_level
        self.item_position = 0
        self.desired_down_arrow_idx = self.desired_lower_right_corner_idx - down_arrow_to_lower_right_corner_offset
        self.desired_down_arrow_coords = np.array([region['left'] + self.desired_down_arrow_idx[1], region['top'] + self.desired_down_arrow_idx[0]])
        self.into_coords = self.desired_down_arrow_coords - np.array([11,6])
        self.description_region = {'left': int(region['left'] + self.corner_description_idx[1]), 'top': int(region['top'] + self.corner_description_idx[0]), 'width': int(width_of_description_pane), 'height': int(self.desired_lower_right_corner_idx[0] - self.corner_description_idx[0])}
        
        
    def get_attributes(self, item_position=0, end_item_position_addition=0, fail_gracefully=False):
        self.item_count, self.item_capacity, self.down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, 
                    start_row=self.desired_lower_right_corner_idx[0] + self.lower_right_corner_to_start_of_item_count_offset[0], 
                    start_col=self.desired_lower_right_corner_idx[1] + self.lower_right_corner_to_start_of_item_count_offset[1],
                    fail_gracefully=fail_gracefully)
        
        self.item_position = deepcopy(item_position)
        self.end_item_position = self.item_count + end_item_position_addition

    
    def get_lower_right_dragable_idx_safe(self):
        '''
        Notes
        -----
        1. Requires self.capacity to equal item_capacity gotten. Thus all containers of type self must have the same capacity.
            This is more safe but requires you to set up a different class for every type of hopper with a differeing amount of capacity,
            or some other workaround. Easier to use get_lower_right_dragable_idx.
        '''
        item_count, item_capacity, self.down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=0, start_col=0)
        # Try rows first
        while item_capacity != self.capacity and self.down_arrow_idx is not None:
            item_count, item_capacity, self.down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=self.down_arrow_idx[0] + 1, start_col=0)
        if self.down_arrow_idx is None:
            item_count, item_capacity, self.down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=0, start_col=0)
            # Now try cols
            while item_capacity != self.capacity:
                item_count, item_capacity, self.down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=0, start_col=self.down_arrow_idx[1] + 1)
        # At this point, we've found the lower right corner of the container.
        
        self.dragable_idx = self.down_arrow_idx + down_arrow_to_lower_right_corner_offset
    
    
    def get_lower_right_dragable_idx(self):
        item_count, item_capacity, self.down_arrow_idx = get_item_count_and_capacity(region, img_arr=None, start_row=0, start_col=0)
        self.dragable_idx = self.down_arrow_idx + down_arrow_to_lower_right_corner_offset
    
    
    def calibrate_container_position(self):
        '''
        Returns
        -------
        None
    
        Purpose
        -------
        A container may have a position/sizing that is undesirable such as for tasks that require dragging items from one container to another. 
        This function puts the bottom right and top left corners of the window with given capacity into the desired places. This automation is nice
        if (e.g.) there are many containers that all need to be resized/re-positioned.
        
        Methods
        -------
        1. This function starts by seeing if the toggle button is visible. If so, the upper left corner is panned to be made visible (if necessary) and dragged to the
            desired location.
        2. If toggle is not visible then tries to pan and drag the lower corner, and then returns to seeing if the toggle is visible for upper left movement.
        
        Notes
        -----
        1. Call the container in question C.
        2. C must have (*/50) visible (and have a little space underneath it to click-drag) (if given capacity is 50) OR toggle for showing description is visible and a little space to the right of it to drag.
        3. If another open container has the same capacity, then the capacity string (e.g. 10/50) for C must be found first.
        4. If another open container has a toggle button showing, then the toggle button for C must be found first.
        5. If desired_lower_right_corner_idx and desired_upper_left_corner_idx are too close together, this function might still work, but only place one of the two corners in the desired location.
        '''
        global win_pressed
        tolerance = 0
        win_pressed = False
        def on_win_press(key):
            global win_pressed
            if key == Key.cmd_l:
                win_pressed = True


        def on_release(key):
            pass
        
        
        def wait_for_press(thing_visible):
            global win_pressed
            print(thing_visible + ' not found. Move the container window so that it is visible, then press Windows key.')
            while not win_pressed:
                time.sleep(0.1)
            win_pressed = False
            
        
        with Listener(on_press=on_win_press, on_release=on_release) as listener:
            swg_utils.idx_checks(region=region, idx=self.desired_lower_right_corner_idx, fail_gracefully=False)
            swg_utils.idx_checks(region=region, idx=self.desired_upper_left_corner_idx, fail_gracefully=False)
            dragged_lower_right = False
            dragged_upper_left = False
            i = -1
            while i < 10 and not (dragged_upper_left and dragged_lower_right):
                i += 1
                if not dragged_upper_left:
                    # Find upper left corner
                    description_toggle_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['show_description_toggle_100_threshold'], region=region, sharpen_threshold=100, fail_gracefully=True)
                    if description_toggle_idx is None:
                        wait_for_press('Description toggle button')
                        continue
                    self.dragable_idx = description_toggle_idx + self.toggle_to_upper_left_corner_offset
                    if not swg_utils.idx_checks(region=region, idx=self.dragable_idx, fail_gracefully=True):
                        wait_for_press('Container upper left corner')
                        continue
                    if abs(np.sum(self.dragable_idx) - np.sum(self.desired_upper_left_corner_idx)) > tolerance:
                        swg_utils.click_drag(start_idx=self.dragable_idx, end_idx=self.desired_upper_left_corner_idx, region=region, num_drags=1, start_delay=0.1, return_delay=0.75)
                    dragged_upper_left = True
                if not dragged_lower_right:
                    self.get_lower_right_dragable_idx()
                    if not swg_utils.idx_checks(region=region, idx=self.dragable_idx, fail_gracefully=True):
                        wait_for_press('Container lower right corner')
                        continue
                    if abs(np.sum(self.dragable_idx) - np.sum(self.desired_lower_right_corner_idx)) > tolerance:
                        swg_utils.click_drag(start_idx=self.dragable_idx, end_idx=self.desired_lower_right_corner_idx, region=region, num_drags=1, start_delay=0.1, return_delay=0.75)
                    dragged_lower_right = True
            if i == 10:
                raise Exception('Could not calibrate container position for some reason.')
                
                
    def get_pack_position(self):
        self.pack_position = None
        while self.item_position < self.end_item_position:
            item_coords = get_item_coords(self.corner_description_idx, region, self.item_position)
            # Click on item
            img_arr = swg_utils.click_on_item(region, item_coords=item_coords, button='left', sub_region=self.description_region)
            # Check to see whether it is a pack
            container_item_count, container_item_capacity = get_item_container_item_count_and_capacity(self.corner_description_idx, self.first_indentation_level_col, img_arr)
            if container_item_count is not None:
                self.pack_position = deepcopy(self.item_position)
                break
            self.item_position = self.item_position + 1
        if self.pack_position is None:
            raise Exception('Need a 50-item pack in the 65-item backpack')
                    
                    
class Inventory_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 80
        self.desired_upper_left_corner_idx = [0,0]
        self.desired_lower_right_corner_idx = [region['height'] - 10, 910]
        super(Inventory_Calibrator, self).__init__()
        
    
class Backpack_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 65
        self.desired_upper_left_corner_idx = [0,0]
        self.desired_lower_right_corner_idx = [region['height'] - 1, 910]
        super(Backpack_Calibrator, self).__init__()
        

class Droid_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 30
        self.desired_upper_left_corner_idx = [0,0]
        self.desired_lower_right_corner_idx = [region['height'] - 1, 955]
        super(Droid_Calibrator, self).__init__()
        

class Hopper_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 100
        self.desired_upper_left_corner_idx = [0,0]
        self.desired_lower_right_corner_idx = [250, region['width'] - 1]
        super(Hopper_Calibrator, self).__init__()
        
        
class Pack_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 50
        self.desired_upper_left_corner_idx = [0,0]
        self.desired_lower_right_corner_idx = [region['height'] - 1, 910]
        super(Pack_Calibrator, self).__init__()
        
        
class Loot_Box_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 75
        self.desired_upper_left_corner_idx = [0, 0]
        self.desired_lower_right_corner_idx = [int(0.8 * region['height']), int(0.9 * region['width'])]
        super(Loot_Box_Calibrator, self).__init__()
        
        
class Good_Loot_Calibrator(Container_Calibrator):
    def __init__(self):
        self.capacity = 100
        self.desired_upper_left_corner_idx = [0,0]
        self.desired_lower_right_corner_idx = [region['height'] - 10, region['width'] - 1]
        super(Good_Loot_Calibrator, self).__init__()
        
      
def calibrate_containers(calibration_desires_dct={
            'inventory': True,
            'backpack': True,
            'droids': True,
            'hopper': True,
            'pack': True,
            'loot_box': True,
            'good_loot': True}):
    '''
    calibration_desires_dct: dict
        What to calibrate. Options are.
        'inventory': bool
        'backpack': bool
        'droids': bool
        'hopper': bool
        'pack': bool
        'loot_box': bool
        'good_loot': bool
        
    user_input_before_calibrations: bool
        True: If cannot find toggle arrow on the window after opening container,
            wait for user to give an input before calibrating it so that the 
            user has the chance to resize/re-position the window such that the 
            program will not fail when trying to calibrate it.
            e.g. If a window is too large, then the program will not be able to grab
            both upper left and lower right corners and so will fail. So, the user
            must make the window size smaller manually.
            
        False: If cannot find toggle arrow on the window after opening container,
            skip this container. Close all windows and re-open any necessary windows
            to check the next container. Use False if you are sure all windows not
            seen are actually not even there, or can be skipped (dangerous).
        
    Returns
    -------
    None.
    Purpose
    -------
    Cycle through and calibrate window position of all windows of the types desired.
    
    Methods
    -------
    For each type in calibration_desires_dct, open each container of the type desired and calibrate its position.
    For inventory, open inventory, calibrate position, close inventory.
    For backpack, use backpack_inventory_position to open backpack, calibrate, close.
    For droids, orient(), then use droid_pane and num_droids to open/calibrate/close them one at a time.
    For hopper, go through Loot_0-Loot9, collections_0-collections_1, DIs_0-DIs_5, non_components_0-non_components_4
    For pack, open inventory, start at the position you would start looking for loot, go through each item. Each item that is a container gets opened, inventory closed, pack calibrated, pack closed, inventory opened.
    For loot_box, (in the gunship) open Loot Box, calibrate, close.
    For good_loot, go through A0-A9, B0-B9, ..., W0-W9
    
    Notes
    -----
    1. Have no containers open at the time this function is called.
    '''
    # Orient so we zoom in so that no pixel changes, otherwise my toon breathing/shuffling around will indicate a pixel change.
    orient(open_inventory=False)
    ic = Inventory_Calibrator()
    bc = Backpack_Calibrator()
    dc = Droid_Calibrator()
    hc = Hopper_Calibrator()
    pc = Pack_Calibrator()
    lc = Loot_Box_Calibrator()
    gc = Good_Loot_Calibrator()
    calibrated_inventory = False
    if calibration_desires_dct['droids']:
        orient(open_inventory=False, zoom_in=True)
    for container_type, calibrate_container_type in calibration_desires_dct.items():
        if not calibrate_container_type:
            continue
        if (container_type == 'inventory' or container_type == 'backpack' or container_type == 'pack') and not calibrated_inventory:
            # Open inventory
            pdi.press('i')
            time.sleep(0.1)
            # Move mouse out of the way
            swg_utils.moveTo(coords=[region['width'] + region['left'] - 30, region['top'] + region['height'] - 30], return_delay=0.2)
            ic.calibrate_container_position()
            # Close inventory
            pdi.press('i')
            calibrated_inventory = True
        if container_type == 'backpack':
            # Open inventory
            pdi.press('i')
            time.sleep(0.2)
            corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
            backpack_coords = get_item_coords(corner_description_idx, region, backpack_inventory_position)
            # Open backpack
            item_radial_option(backpack_coords, radial_option='1')
            # Close inventory
            pdi.press('i')
            time.sleep(0.2)
            bc.calibrate_container_position()
            # Close backpack
            pdi.press('esc')
        elif container_type == 'droids':
            for d in range(droid_i, num_droids):
                orient(open_inventory=False, zoom_in=False)
                # call the droid
                swg_utils.chat('/ui action toolbarSlot' + str(d).zfill(2))
                time.sleep(2)
                # open the droid's inventory
                open_droid_inventory()
                time.sleep(0.5)
                dc.calibrate_container_position()
                # Close droid's inventory
                pdi.press('esc')
                time.sleep(0.2)
                # Store the droid
                swg_utils.chat('/ui action toolbarSlot' + str(d).zfill(2))
                time.sleep(0.5)
        elif container_type == 'hopper':
            for hopper_type, num_hoppers in hopper_dct.items():
                for hopper_i in range(num_hoppers):
                    hopper_name = hopper_type + str(hopper_i)
                    before_img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=region, set_focus=False, sharpen=False)
                    # Open hopper
                    swg_utils.chat('/open ' + hopper_name, start_delay=0.1, return_delay=0.2)
                    after_img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=region, set_focus=False, sharpen=False)
                    # Use only a section of the window to exclude the radar and chat log (which might have a change in pixel value despite the container not being opened)
                    if (len(np.where((after_img_arr[80:575, 262:838] >= 40) & (after_img_arr[80:575, 262:838] <= 41))[0]) - 
                        len(np.where((before_img_arr[80:575, 262:838] >= 40) & (before_img_arr[80:575, 262:838] <= 41))[0]) < 80):
                        # No container with hopper_name was in range. Skip.
                        continue
                    hc.calibrate_container_position()
                    # Close hopper
                    pdi.press('esc')
        elif container_type == 'pack':
            # Open inventory
            pdi.press('i')
            corner_description_idx, img_arr = swg_utils.find_arr_on_region(inventory_dct['top_left_corner_of_description_section_130_threshold'], region=region, sharpen_threshold=130)
            first_indentation_level_col = corner_description_idx[1] + num_cols_from_left_side_to_first_indentation_level
            item_count, item_capacity, down_arrow_idx = get_item_count_and_capacity(region, img_arr=None)
            i = starting_inventory_position
            end_by_i = item_count + num_equipped_items - num_items_in_bulky_containers
            while i < end_by_i:
                item_coords = get_item_coords(corner_description_idx, region, i)
                # Click on item
                img_arr = swg_utils.click_on_item(region, item_coords=item_coords, button='left', sub_region=ic.description_region)
                container_item_count, container_item_capacity = get_item_container_item_count_and_capacity(corner_description_idx, first_indentation_level_col,  img_arr)
                if container_item_count is None:
                    i += 1
                    continue
                # Open pack
                item_radial_option(item_coords, radial_option='1')
                # Close inventory
                pdi.press('i')
                pc.calibrate_container_position()
                pack_item_count, pack_item_capacity, pack_down_arrow_idx = get_item_count_and_capacity(region, img_arr=None)
                # Close pack
                pdi.press('esc')
                # Open inventory
                pdi.press('i')
                i += 1
                end_by_i -= pack_item_count
            # Close inventory
            pdi.press('i')
        elif container_type == 'loot_box':
            # Open Loot Box
            swg_utils.chat('/open Loot')
            lc.calibrate_container_position()
            # Close Loot Box
            pdi.press('esc')
        elif container_type == 'good_loot':
            for first_letter in ['A', 'B', 'C', 'D', 'E', 'R', 'S', 'W']:
                for re_lvl in range(10):
                    hopper_name = first_letter + str(re_lvl) + '_0'
                    # Open hopper
                    swg_utils.chat('/open ' + hopper_name)
                    gc.calibrate_container_position()
                    # Close hopper
                    pdi.press('esc')
 
                    
def get_name(img_arr, calibrator, sorting_task, item_coords):
    component_type_id_dct = {'Booster_Energy':'booster', 'Capacitor_Energy':'capacitor', 'Droid_Command_Speed':'droid_interface', 'Engine_Top_Speed':'engine', 'Reactor_Generation_Rate':'reactor', 'Shield_Recharge_Rate':'shield', 'Energy_Per_Shot':'weapon', 'Armor': 'armor'}
    hopper_type_dct = {'collection': 'collection', 'cargo_crate' : 'crate', 'military_crate': 'crate', 'crate': 'crate'}
    generic_component = Ship_Component()
    # Find out which type of space component. If it is not a space component, but it is in hopper_type_dct then that will be returned. Else None is returned.
    found_name = None
    for stat_key in component_type_id_dct:
        row = find_str_on_image_given_col(inventory_dct[stat_key], img_arr, calibrator.second_indentation_level_col, start_row=calibrator.corner_description_idx[0])
        if row is not None:
            found_name = component_type_id_dct[stat_key]
            return found_name
    if found_name is None:
        for name in inventory_dct:
            if name[-5:] != '_name':
                continue
            if find_str_on_image_given_col(inventory_dct[name], img_arr, calibrator.first_indentation_level_col, start_row=calibrator.corner_description_idx[0]) is not None:
                found_name = name[:-5]
                break
        if found_name is None:
            return None
        if 'crate' in found_name:
            found_name = 'crate'
        if sorting_task != 'kash' and ('collection' == found_name or ('crate' in found_name and sorting_task != 'POB')):
            generic_component.store_loot_in_hopper(item_coords, hopper_type_dct[found_name], False, calibrator=calibrator)
        if sorting_task == 'kash' and 'collection' == found_name:
            # Destroy collection piece. It's not supposed to be here.
            swg_utils.destroy_item(item_coords, swg_window, region)
        return found_name
    
         
def sort_loot_when_in_POB(keep_DI_frequency=0):
    '''
    keep_DI_frequency: float
        Fraction of the time to keep droid interfaces (for use in convoy flight plans). Float between 0 and 1.
        Setting this as a high value may fill up the droids quickly. Set at 0 if you don't want to do convoys.
        
    Returns
    -------
    None
    
    Purpose
    -------
    As loot drops into the Loot Container in a POB, sort it.
    
    Method
    ------
    1. Begin with an inventory full (or even overloaded) with packs which begin at the same
        location that you would start sorting loot if in house. These packs have 50 item capacity each.
    2. Also, have an equipped backpack with 65 item capacity (refer to this as backpack) which
        has at least 51 empty spaces initially.
    3. Previous to running this function, run
    calibrate_containers(calibration_desires_dct={
                'inventory': True,
                'backpack': True,
                'droids': True,
                'hopper': True,
                'pack': True,
                'loot_box': True,
                'good_loot': False})
    Notes
    -----
    1. You are already in the POB and in the room with the Loot Container
    2. You do not have inventory or any other windows open at the start of the function
    3. Start out with 1 pack in your backpack (which is for space loot).
    4. Start out with no items in packs in your inventory. (Some items can be in the pack in the backpack)
    '''
    global starting_inventory_position, droid_i
    # Set up an object for each component type
    component_dct = {'armor': Armor(), 'booster': Booster(), 'capacitor': Capacitor(), 'droid_interface': Droid_Interface(),
                'engine': Engine(), 'reactor': Reactor(), 'shield': Shield(), 'weapon': Weapon()}
    
    orient()
    
    ic = Inventory_Calibrator()
    bc = Backpack_Calibrator()
    pc = Pack_Calibrator()
    lc = Loot_Box_Calibrator()
    dc = Droid_Calibrator()
    hc = Hopper_Calibrator()
    # Inventory attributes
    ic.get_attributes(item_position=starting_inventory_position, end_item_position_addition=num_equipped_items - num_items_in_bulky_containers)
    # Backpack attributes
    backpack_coords = get_item_coords(ic.corner_description_idx, region, backpack_inventory_position)
    # Open backpack
    item_radial_option(backpack_coords, radial_option='1')
    time.sleep(0.4)
    bc.get_attributes()
    # Find pack position
    bc.get_pack_position()
    # Open pack
    bc.pack_coords = get_item_coords(bc.corner_description_idx, region, bc.pack_position)
    item_radial_option(bc.pack_coords, radial_option='1')
    # Pack attributes
    pc.get_attributes()
    # Open Loot Container
    swg_utils.chat('/open Loot')
    lc.get_attributes()
    lc.second_item_coords = get_item_coords(lc.corner_description_idx, region, 1)
    while ic.item_position < ic.end_item_position:
        # The credit chip will always occupy the 1st spot in the Loot container.
        # First check if a piece of loot occupies position 2
        lc.get_attributes()
        if lc.item_count > 1:
            # Click on item
            img_arr = swg_utils.click_on_item(region, item_coords=lc.second_item_coords, button='left', sub_region=lc.description_region)
            found_name = get_name(img_arr, lc, 'POB', lc.second_item_coords)
            if found_name is None:
                # Try getting name again due to the description disappearing when another loot items pops into the Loot box
                # Get screenshot
                img_arr = swg_utils.take_grayscale_screenshot(region=region, sharpen_threshold=130,
                        scale_to=255, sharpen=True, set_focus=False)
                
                
                found_name = get_name(img_arr, lc, 'POB', lc.second_item_coords)
            if found_name == 'collection':
                # If collection item, this was dealt with in get_name
                continue
            if found_name is not None and 'crate' not in found_name:
                component = component_dct[found_name]
                component.get_stats(img_arr, lc.corner_description_idx, lc.first_indentation_level_col, lc.second_indentation_level_col)
                if not component.REable:
                    ic.item_position += 1
                    continue
                component.get_max_loot_percentile_value_stc()
            if found_name is not None and (component.worth_keeping() or (component.component_type == 'droid_interface' and random.random() < keep_DI_frequency) or 'crate' in found_name):
                # Open droid inventory
                # Close out all other windows to open droid
                close_hopper()
                pdi.press('esc', presses=8)
                # Iterate through the droids on the toolbar
                while droid_i < num_droids:
                    # call the droid
                    swg_utils.chat('/ui action toolbarSlot' + str(droid_i).zfill(2), return_delay=2)
                    open_droid_inventory()
                    # See if droid full
                    dc.get_attributes()
                    if dc.item_count >= dc.item_capacity:
                        # Full, try the next one.
                        # Close droid inventory
                        pdi.press('esc')
                        # Store droid
                        swg_utils.chat('/ui action toolbarSlot' + str(droid_i).zfill(2), return_delay=2)
                        droid_i += 1
                        continue
                    break
                if droid_i >= num_droids:
                    # No more space to put good loot, stop.
                    return False
                # Activate Loot box
                swg_utils.chat('/open Loot', return_delay=0.3)
                # Put item into droid
                swg_utils.click_drag(start_coords=lc.second_item_coords, end_coords=dc.into_coords, num_drags=1, start_delay=0.05, return_delay=0.75)
                # Store droid
                swg_utils.chat('/ui action toolbarSlot' + str(droid_i).zfill(2), return_delay=2)
                # Close hopper
                pdi.press('esc')
                time.sleep(0.2)
                # Close droid
                pdi.press('esc')
                time.sleep(0.2)
                # Open inventory
                pdi.press('i')
                # Open backpack
                item_radial_option(backpack_coords, radial_option='1')
                # Open pack
                item_radial_option(bc.pack_coords, radial_option='1')
                # Open loot box
                swg_utils.chat('/open Loot', return_delay=0.3)
            else:
                # Put into pack
                # First check to see whether the pack is full already
                pc.get_attributes()
                while pc.item_count >= pc.item_capacity:
                    # Pack is full, get a new pack.
                    # Start by closing the collection and Loot containers
                    close_hopper()
                    swg_utils.chat('/open Loot')
                    pdi.press('esc')
                    # Close pack
                    pdi.press('esc')
                    # Equip pack
                    item_radial_option(bc.pack_coords, radial_option='2')
                    # Close backpack
                    pdi.press('esc')
                    # Equip backpack
                    item_radial_option(backpack_coords, radial_option='2')
                    # Move new pack to backpack
                    # Go through inventory positions until a pack is found
                    ic.item_coords = get_item_coords(ic.corner_description_idx, region, ic.item_position)
                    img_arr = swg_utils.click_on_item(region, item_coords=ic.item_coords, button='left', sub_region=ic.description_region)
                    container_item_count, container_item_capacity = get_item_container_item_count_and_capacity(ic.corner_description_idx, ic.first_indentation_level_col,  img_arr)
                    if container_item_count is not None:
                        # Open pack
                        item_radial_option(ic.item_coords, radial_option='1')
                        pc.get_attributes()
                        if pc.item_count < pc.item_capacity:
                            # Close pack
                            pdi.press('esc')
                            # Move pack to backpack
                            swg_utils.click_drag(start_coords=ic.item_coords, end_coords=backpack_coords, num_drags=1, start_delay=0.0, return_delay=0.75)
                            # Open backpack
                            item_radial_option(backpack_coords, radial_option='1')
                            # Open pack
                            item_radial_option(bc.pack_coords, radial_option='1')
                        else:
                            ic.item_position += 1
                    else:
                        ic.item_position += 1
                    if ic.item_position >= ic.end_item_position:
                        # No more packs to get. Return.
                        return False
                    # Open loot box
                    swg_utils.chat('/open Loot')
                # Put into pack
                swg_utils.click_drag(start_coords=lc.second_item_coords, end_coords=into_inventory_coords, num_drags=1, start_delay=0.05, return_delay=0.75)
                # Destroy item if it is not a component, nor collection, nor crate (which is when found_name is None). This can happen when you loot something like a datadisk with a useless message.
                if found_name is None:
                    # Activate pack
                    swg_utils.click(coords_idx=pc.desired_lower_right_corner_idx, button='left', start_delay=0.1, return_delay=0.1, window=swg_window, region=region)
                    pc.get_attributes()
                    item_coords = get_item_coords(pc.corner_description_idx, region, pc.item_count - 1)
                    swg_utils.destroy_item(item_coords, swg_window, region)
                    # Activate Loot box
                    swg_utils.chat('/open Loot')
            if found_name is not None and 'crate' not in found_name:
                component.update_recorded_stats_df()
                component.update_good_recorded_stats_df()
                
                
def sort_kash_nunes(component_type='weapon', level=8):
    '''
    Parameters
    ----------
    component_type: str
        valid values are 'armor', 'booster', 'capacitor', 'droid_interface', 'engine', 'reactor', 'shield', 'weapon'
        
    level: int
        Component level. An int in the range [1,10]

    Returns
    -------
    None

    Purpose
    -------
    Spend all duty mission tokens you have at kash nunes buying a single type of component at a certain level repeatedly.
    If you obtain a component that passes the check in worth_keeping(), then put it into a droid. Else, fill up your 65-pack,
    and then fill up inventory. When both full, take to chassis dealer and sell. Return to Kash for more buying and repeat.
    
    Method
    ------
    1. Fill up inventory
    2. Sort loot, transferring junk to backpack and good loot to droid.
    3. Repeat steps 1 and 2 until backpack and inventory full.
    4. Go to chassis dealer and return to Kash
    5. Repeat steps 1-4 until run nearly out of tokens.
    
    while not out of tokens:
        while backpack and inventory not full:
            while inventory not full:
                fill up inventory
            for all new loot:
                sort loot
        go to chassis dealer, sell, and return to Kash
    
    Notes
    -----
    1. Assumes start off close to Kash.
    2. Be a spy and have cloak already on.
    3. Make a macro in-game for each combination of component type and level that you are interested in. Call
        the macro e.g. KashA0 or KashW8. The macro for KashW0 looks like this:
        
        /tar Kash;
        /pause 0.1;
        /conversationStart;
        /pause 0.1;
        /npcConversationSelect 0;
        /pause 0.1;
        /npcConversationSelect 9;
        /pause 0.1;
        /npcConversationSelect 7;
        /pause 0.1;
        /npcConversationSelect 0;
        
        where first Select is trade tokens for parts, second Select is level,
        third Select is level index, last Select is to end conversation.
        
    4. This algorithm requires the duty mission tokens to always be at the position specified in the conf file. Thus,
        this function will not purchase anything if you only have 100 or less tokens.
    5. All items starting at starting_inventory_position that are not a ship component or crate will be skipped. (Except collection items which will be destroyed).
    
    Todo
    ----
    1. Become spy and have function 0 in function list in move_along() be a check to make sure we are still cloaked.
    2. Deal with the possibility that a player is standing on top of me and thus I am unable to access the droid
    2a. Perhaps move to another room to do sorting such that it is low probability that someone is standing there and/or watching.
    '''
    global droid_i
    generic_component = Ship_Component()
    # Set up an object for each component type
    component_dct = {'armor': Armor(), 'booster': Booster(), 'capacitor': Capacitor(), 'droid_interface': Droid_Interface(),
                'engine': Engine(), 'reactor': Reactor(), 'shield': Shield(), 'weapon': Weapon()}
    
    ic = Inventory_Calibrator()
    bc = Backpack_Calibrator()
    dc = Droid_Calibrator()
    
    # Inventory attributes
    pdi.press('i')
    time.sleep(0.2)
    ic.get_attributes(item_position=starting_inventory_position, end_item_position_addition=num_equipped_items - num_items_in_bulky_containers)
    if ic.item_position >= ic.item_capacity:
        return True
    # Backpack attributes
    backpack_coords = get_item_coords(ic.corner_description_idx, region, backpack_inventory_position)
    # Open backpack
    item_radial_option(backpack_coords, radial_option='1')
    time.sleep(0.4)
    bc.get_attributes()
    # Close backpack
    pdi.press('esc')
    
    # Click on duty tokens so we can see the amount.
    duty_token_coords = get_item_coords(ic.corner_description_idx, region, duty_token_inventory_position)
    img_arr = swg_utils.click_on_item(region, item_coords=duty_token_coords, sub_region=ic.description_region)
    num_tokens = find_and_get_stat(inventory_dct['Amount'], region=region, img_arr=img_arr, start_row=ic.corner_description_idx[0], start_col=ic.first_indentation_level_col, end_col=ic.first_indentation_level_col, sharpen_threshold=130, dtype=int, corner_description_idx=ic.corner_description_idx)
    
    component_letter = component_type.upper()[0]
    token_cost = float(level * 5 + 50)
    # Subtract 1 so there's some tokens left over to maintain the inventory position of the tokens
    num_components = int(num_tokens / token_cost) - 1
    if num_components <= 0:
        return
    if level == 10:
        level = 0
    level_idx= str(level)
    swg_utils.chat('/macro Kash' + component_letter + level_idx)
    said_kash_last = True
    num_components -= 1
    ic.item_count += 1
    while num_components > 0:
        while ic.item_position < ic.item_capacity and num_components > 0:
            while ic.item_count < ic.item_capacity and num_components > 0:
                if said_kash_last is True:
                    swg_utils.press_sequentially([['enter'],['up'],['enter']], start_delay=0.8)
                else:
                    swg_utils.chat('/macro Kash' + component_letter + level_idx)
                    said_kash_last = True
                num_components -= 1
                ic.item_count += 1
            # Sort loot in inventory, putting junk in backpack until full and putting good loot
            # in droids. For each item put into backpack (increment bc.item_count) or droid, decrement ic.item_position and
            # ic.item_count.
            ##########################################################
            num_new_items = deepcopy(ic.item_count - ic.item_position + num_items_in_bulky_containers)
            for i in range(num_new_items):
                item_coords = get_item_coords(ic.corner_description_idx, region, ic.item_position)
                # Click on item
                img_arr = swg_utils.click_on_item(region, item_coords=item_coords, button='left', sub_region=ic.description_region)
                found_name = get_name(img_arr, ic, 'kash', item_coords)
                if found_name == 'collection':
                    # If collection item, this was destroyed in get_name
                    continue
                if found_name is not None and 'crate' not in found_name:
                    component = component_dct[found_name]
                    component.get_stats(img_arr, ic.corner_description_idx, ic.first_indentation_level_col, ic.second_indentation_level_col)
                    if not component.REable:
                        continue
                    component.get_max_loot_percentile_value_stc()
                if found_name is not None and (component.worth_keeping() or 'crate' in found_name):
                    # Open droid inventory
                    # Close out all other windows to open droid
                    pdi.press('esc', presses=8)
                    # Move to hidden place
                    rwp.main(swg_window_i, waypoint_csv_path=os.path.join(git_path, 'waypoint_paths', 'Kash_to_bar.csv'), function_list=[gtc.empty_function], calibrate_to_north=True)
                    # Iterate through the droids on the toolbar
                    while droid_i < num_droids:
                        # call the droid
                        swg_utils.chat('/ui action toolbarSlot' + str(droid_i).zfill(2), return_delay=2)
                        said_kash_last = False
                        open_droid_inventory()
                        # See if droid full
                        dc.get_attributes()
                        if dc.item_count >= dc.item_capacity:
                            # Full, try the next one.
                            # Close droid inventory
                            pdi.press('esc')
                            # Store droid
                            swg_utils.chat('/ui action toolbarSlot' + str(droid_i).zfill(2), return_delay=2)
                            said_kash_last = False
                            droid_i += 1
                            continue
                        break
                    if droid_i >= num_droids:
                        # No more space to put good loot, stop.
                        return False
                    # Activate inventory
                    pdi.press('i')
                    # Put item into droid
                    swg_utils.click_drag(start_coords=item_coords, end_coords=dc.into_coords, num_drags=1, start_delay=0.05, return_delay=0.75)
                    ic.item_count -= 1
                    # Store droid
                    swg_utils.chat('/ui action toolbarSlot' + str(droid_i).zfill(2), return_delay=2)
                    said_kash_last = False
                    # Close inventory
                    pdi.press('esc')
                    time.sleep(0.2)
                    # Close droid
                    pdi.press('esc')
                    time.sleep(0.2)
                    # Open inventory
                    pdi.press('i')
                    time.sleep(0.2)
                    rwp.main(swg_window_i, waypoint_csv_path=os.path.join(git_path, 'waypoint_paths', 'bar_to_Kash.csv'), function_list=[gtc.empty_function], calibrate_to_north=True)
                else:
                    # Skip item if it is not a component, nor collection, nor crate (which is when found_name is None).
                    if found_name is None:
                        ic.item_position += 1
                        print('found_name is None')
                        if ic.item_position > ic.item_capacity:
                            raise Exception('ic.item_position', ic.item_position, 'is greater than ic.item_capacity', ic.item_capacity)
                    elif bc.item_count < bc.item_capacity:
                        # Put into backpack
                        swg_utils.click_drag(start_coords=item_coords, end_coords=backpack_coords, num_drags=1, start_delay=0.05, return_delay=0.75)
                        ic.item_count -= 1
                        bc.item_count += 1
                    else:
                        # Skip
                        ic.item_position += 1
                if found_name is not None and 'crate' not in found_name:
                    component.update_recorded_stats_df()
                    component.update_good_recorded_stats_df()
                
                ##########################################################
        # Go to chassis dealer and sell all, then return to Kash
        pdi.press('esc', presses=8)
        rwp.main(swg_window_i, waypoint_csv_path=os.path.join(git_path, 'waypoint_paths', 'Kash_to_Chassis_and_back.csv'), function_list=[gtc.empty_function, gtc.sell_to_chassis_dealer], calibrate_to_north=True)
        ic.inventory_position = starting_inventory_position
        # Open inventory
        pdi.press('i')
        time.sleep(0.5)
        ic.get_attributes(item_position=starting_inventory_position, end_item_position_addition=num_equipped_items - num_items_in_bulky_containers)
        # Open backpack
        item_radial_option(backpack_coords, radial_option='1')
        time.sleep(0.4)
        bc.get_attributes()
        # Close backpack and inventory and all
        pdi.press('esc', presses=8)
        # Repeat until num_components is 0
    return True
    
    
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
        backpack_item_count, backpack_coords = get_backpack_item_count(backpack_already_open=False)
        generic_component.backpack_item_count = backpack_item_count
        generic_component.backpack_coords = backpack_coords
        sort_backpack(generic_component, component_dct, False)
        if sorting_desires_dct['crates']:
            sort_crates(generic_component, component_dct, reopen_inventory=True)
    if sorting_desires_dct['backpack'] and sorting_desires_dct['crates']:
        # Now, put as much junk loot from the hoppers into the backpack as possible.
        put_items_into_caravan(generic_component.backpack_coords)
    if sorting_desires_dct['droids']:
        # Now, sort droid inventories
        deal_with_droids(generic_component, component_dct)
    if sorting_desires_dct['crates']:
        # Put as much junk loot from the hoppers into the inventory as possible
        put_items_into_caravan(double_clickable=True)
    # Close inventory
    pdi.press('esc')
    
    
def go_to_friend_pob(pob_owner_name='Rosethorn', group_leader_name='Rosethorn', doaba_to_launch_waypoint_csv_path=os.path.join(git_path, 'waypoint_paths', 'Doaba_to_Launch.csv'),
                     Doaba_to_Chassis_dealer_to_Launch_waypoint_csv_path=os.path.join(git_path, 'waypoint_paths', 'Doaba_to_Chassis_dealer_to_Launch.csv')):
    '''
    Parameters
    ----------
    pob_owner_name: str
        in-game name of toon who is flying the POB (should show up when u target the ship)
        
    group_leader_name: str
        in-game name of toon who is group leader who has auto-invite macro going.
        
    doaba_to_launch_waypoint_csv_path: str
        Waypoint path file that takes you from Doaba Guerfel starport to launch without selling to chassis dealer.
        
    

    Returns
    -------
    got_into_group: bool
        True: group_leader_name is running autoinvite macro so we go into the group
        False: we did not get into the group

    Purpose
    -------
    get invited to group, Launch ship, findfriend, hyperspace to sector of friend, autopilot to friend, target pob owner and follow it, when close enough then dock, go to loot room.
    
    Notes
    -----
    1. Start out in Doaba Guerfel starport landing location
    
    2. Be in the friend's list of group_leader_name and pob_owner_name must be nearby group_leader_name
    
    3. group_leader_name must be running an invite macro
    
    4. For now, assumes pob_owner_name is in Ord Mantell space. Later, can destroy the friend wp and findfriend to 
        A. make sure group_leader_name is online
        B. determine which system (or even sector) group_leader_name is currently in
        C. Hyperspace to the correct system (or sector)
        
    5. For now assumes pob is stationary the whole time
    '''
    # Try stealth
    swg_utils.stealth_on()
    # Check to see if already in group
    found_idx, _ = swg_utils.find_arr_on_region(land_ui_dct[group_leader_name + '_group_member_225'], region=region, start_row=50, end_row=300, end_col=200, fail_gracefully=True, sharpen_threshold=225)
    if found_idx is None:
        # Not in the group.
        # Send tell to Rosethorn to get invited to group.
        swg_utils.chat('/t ' + group_leader_name + ' inv')
        start_time = time.time()
        while found_idx is None and time.time() - start_time < 31:
            found_idx, _ = swg_utils.find_arr_on_region(land_ui_dct[group_leader_name + '_group_member_225'], region=region, start_row=50, end_row=300, end_col=200, fail_gracefully=True, sharpen_threshold=225)
        if time.time() - start_time >= 31:
            # Rosethorn is not running his invite macro. Wait.
            return False
        swg_utils.chat('/join')
    # Launch ship
    rwp.main(swg_window_i, waypoint_csv_path=doaba_to_launch_waypoint_csv_path, function_list=[gtc.empty_function, swg_utils.stealth_on, gtc.launch_ship], calibrate_to_north=True)
        
    
    
def scan_DIs():
    '''
    Returns
    -------
    None

    Purpose
    -------
    Go through the stored droid interfaces in DIs_0, DIs_1, etc and scan them using the stored DI scanners in DIscanners_0.
    This produces flight plans which will be put in stackable_crate_loot_0 (because flight plans stack and sometimes come from convoy crates).
    
    Notes
    -----
    1. Inventory must be closed before calling this function
    '''
    global currently_open_hopper
    global droid_interface_hopper_i
    droid_interface_hopper_i = hopper_dct['DIs_'] - 1
    # Open inventory
    pdi.press('i')
    generic_component = Ship_Component()
    ic = Inventory_Calibrator()
    # item_position will refer to spot after DI scanner (unless DI scanner runs out of charges and disappears, in which case it will be the spot DI scanner was in)
    ic.get_attributes(item_position=starting_inventory_position + 1, end_item_position_addition=num_equipped_items - num_items_in_bulky_containers)
    DIscanner_item_coords = get_item_coords(ic.corner_description_idx, region, starting_inventory_position)
    # Open DIscanners_0
    swg_utils.chat('/open DIscanners_0')
    currently_open_hopper = 'DIscanners_0'
    # Get the number of DI scanners in the hopper
    hc = Hopper_Calibrator()
    hc.get_attributes()
    DIscanner_hopper_item_coords = get_item_coords(hc.corner_description_idx, region, 0)
    while hc.item_count > 0:
        # Get a DI scanner into your inventory
        swg_utils.click_drag(start_coords=DIscanner_hopper_item_coords, end_coords=ic.into_coords, num_drags=1, start_delay=0.0, return_delay=0.5)
        hc.item_count -= 1
        ic.item_count += 1
        close_hopper()
        # Get number of charges remaining on this DI scanner
        img_arr = swg_utils.click_on_item(region, item_coords=DIscanner_item_coords, sub_region=ic.description_region)
        num_charges = find_and_get_stat(inventory_dct['Charges_130'], region=region, img_arr=img_arr, start_row=ic.corner_description_idx[0], start_col=ic.first_indentation_level_col, end_col=ic.first_indentation_level_col, fail_gracefully=False, sharpen_threshold=130, dtype=int, corner_description_idx=ic.corner_description_idx)
        while num_charges > 0:
            # Get 5 droid interfaces into your inventory
            num_items_transferred = put_items_into_caravan(hopper_type='junk_droid_interface', max_items_to_transfer=5, double_clickable=True)
            ic.item_count += num_items_transferred
            if num_items_transferred < 5:
                # Not enough droid interfaces to scan, put the DIs back and then put the DIscanner back and then we're done.
                item_coords = get_item_coords(ic.corner_description_idx, region, ic.item_position)
                for _ in range(num_items_transferred):
                    ic.store_loot_in_hopper(item_coords, 'junk_droid_interface', True, calibrator=ic)
                    ic.item_count -= 1
                close_hopper()
                swg_utils.chat('/open DIscanners_0')
                currently_open_hopper = 'DIscanners_0'
                item_coords = get_item_coords(ic.corner_description_idx, region, ic.item_position - 1)
                ic.store_loot_in_hopper(item_coords, 'DIscanners', True, calibrator=ic)
                ic.item_count -= 1
                close_hopper()
                pdi.press('esc', presses=8)
                return
            ic.get_attributes(item_position=ic.item_position)
            previous_item_count = deepcopy(ic.item_count)
            # Put 5 droid interfaces into the scanner
            DI_item_coords = get_item_coords(ic.corner_description_idx, region, ic.item_position)
            swg_utils.click_drag(start_coords=DI_item_coords, end_coords=DIscanner_item_coords, num_drags=5, start_delay=0.0, return_delay=0.1)
            # Scan
            item_radial_option(DIscanner_item_coords, radial_option='5')
            num_charges -= 1
            time.sleep(3)
            ic.get_attributes(item_position=ic.item_position)
            if num_charges == 0:
                num_new_items = ic.item_count - previous_item_count + 5 + 1
                ic.item_position -= 1
            else:
                num_new_items = ic.item_count - previous_item_count + 5
            # item position is now the location to start sorting.
            # Sort through the items that were generated. They will either be flight plans or hyperspace chips
            item_coords = get_item_coords(ic.corner_description_idx, region, ic.item_position)
            for _ in range(num_new_items):
                img_arr = swg_utils.click_on_item(region, item_coords=item_coords, sub_region=ic.description_region)
                generic_component.store_loot_in_hopper(item_coords, 'non_components', True, calibrator=ic)
            if num_charges == 0:
                ic.item_position += 1
                swg_utils.chat('/open DIscanners_0')
                currently_open_hopper = 'DIscanners_0'
                hc.get_attributes()
    pdi.press('esc', presses=8)
                

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
    
num_droids: int
    Number of droids. This is 1 plus the maximum value of droid_i. i.e. num_droids is the number of droids used for storage of space loot starting from droid_i = 0.
    These droids must be on the toolbar in the same order as the toolbarSlot index on toolbarPane droid_pane.
    
    e.g.
    You have 30 droids, and the starting droid_i you want to use is 2 (meaning the 1st and 2nd droid should be skipped) and the last droid available for storing component loot is the 25th droid.
    (droids 26-30 are used for storage of something else). Then the max value of droid_i will be 23 so num_droids will be 24. (Even if the skipped ones at the beginning are not used for space loot).
    
droid_pane: int
        The toolbar pane that has all your inventory droids placed in the slots in contiguous order.
        
junk_hopper_i: int
    The lowest junk loot hopper name index (e.g. 0 for Loot_0) that is not full.
    
droid_i: int
    The lowest 0-indexed inventory droid as ordered by toolbarSlot that you want to start from when sorting the inventory droids.
    
droid_interface_hopper_i: int
    The lowest DI hopper name index (e.g. 0 for DIs_0) that is not full.
    
non_components_hopper_i: int
    The lowest name index (e.g. 0 for non_components_0) for the hopper of items gotten from a crate that are not ship components.
    
backpack_inventory_position:
    Position in the inventory (0-indexed) of the equipped backpack.
    
    
hopper_dct: dict
    keys are first letters of each type of hopper, values are the number of hoppers of this type in the house.
    
chatbar_idx: list
    [row, col] of where to click so that the chat cursor is activated.
    
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
down_arrow_to_start_of_item_count_offset: list of int
    [row_offset, col_offset] to get from down arrow idx to upper left corner of the line arr for getting item count and capacity of a container.
    
into_hopper_coords: list of int
    [x,y] coordinates on the screen where items can be dragged into a hopper window.
    
into_inventory_coords: list of int
    [x,y] coordinates on the screen where items can be dragged into an inventory window.
    
caravan_activation_coords: list of int
    [x,y] coordinates on the screen where a caravan window (such as droid inventory, backpack, pack, but not inventory because this can mess with backpack sorting) can be clicked to activate it (bring it to foreground).
    
currently_open_hopper: str or None
    If None, no hopper is currently open. Else, this will be the name of the open hopper. There should only be 1 hopper open at a time.
    
extreme_avg_and_modifier_dct: dict
    See get_extreme_avg_and_modifier_combo_for_stats() docs.
    
Notes
-----
1. starting_inventory_position, junk_hopper_i, droid_i, and non_components_hopper_i are used so that the program doesn't have to start at index 0 and figure out where the first space related item is or which
    hopper is not full. (Although it will automatically if starting_inventory_position is set to 0).
    
2. The inventory should be placed and sized such that the name of the item appears on the top bar, it has num_inventory_cols columns of items (9 is good for default icon size), the number of item contents out
    of 80 are visible (in the lower right corner), and the inventory window extends to the bottom of the swg window. Droid inventory windows and the backpack window should also follow this positioning scheme.
    
3. The storage hopper windows should be sized and placed such that the height is minimize, the width is maximized, and the top left corner of the description pane is visible.
'''


        

toon_name = swg_utils.get_toon_name(region)
starting_inventory_position = config.config_dct[toon_name + '_sort_space_components']['starting_inventory_position']
duty_token_inventory_position = config.config_dct[toon_name + '_sort_space_components']['duty_token_inventory_position']
num_equipped_items = config.config_dct[toon_name + '_sort_space_components']['num_equipped_items']
num_items_in_bulky_containers = config.config_dct[toon_name + '_sort_space_components']['num_items_in_bulky_containers']
num_droids  = config.config_dct[toon_name + '_sort_space_components']['num_droids']
droid_pane = config.config_dct[toon_name + '_sort_space_components']['droid_pane']
junk_hopper_i = config.config_dct[toon_name + '_sort_space_components']['junk_hopper_i']
crate_hopper_i = config.config_dct[toon_name + '_sort_space_components']['crate_hopper_i']
# Index of starting droid to investigate. num_droids is still total number of droids including those not wished to be investigated (minus any at the end that don't have space stuff, if any)
droid_i = config.config_dct[toon_name + '_sort_space_components']['droid_i']
droid_interface_hopper_i = config.config_dct[toon_name + '_sort_space_components']['droid_interface_hopper_i']
non_components_hopper_i = config.config_dct[toon_name + '_sort_space_components']['non_components_hopper_i']
collection_hopper_i = config.config_dct[toon_name + '_sort_space_components']['collection_hopper_i']
backpack_inventory_position = config.config_dct[toon_name + '_sort_space_components']['backpack_inventory_position']
num_inventory_cols = config.config_dct[toon_name + '_sort_space_components']['num_inventory_cols']
num_hopper_cols = config.config_dct[toon_name + '_sort_space_components']['num_hopper_cols']
keep_percentile = float(config.config_dct[toon_name + '_sort_space_components']['keep_percentile'])
chatbar_idx = config.config_dct[toon_name + '_sort_space_components']['chatbar_idx']

hopper_dct = {'DIs_': 6, 'non_components_': 5, 'loot_': 10, 'collections_': 3, 'Crates_': 5, 'stackable_crate_loot_': 1, 'DIscanners_': 1}
# Constants
digit_height = 8
num_cols_from_left_side_to_first_indentation_level = 7
num_cols_from_left_side_to_second_indentation_level = 27
width_of_description_pane = 263
down_arrow_to_start_of_item_count_offset = np.array([23, 75])
down_arrow_to_lower_right_corner_offset = np.array([83, 16])
# Coords of where to drag items into a hopper
into_hopper_coords = [region['left'] + 950, region['top'] + 60]
# Coords of where to drag items into an inventory
into_inventory_coords = [region['left'] + 500, region['top'] + 650]
caravan_activation_coords = [region['left'] + 50, region['top'] + 763]
inventory_activation_coords = [region['left'] + 50, region['top'] + 753]
# more initial values
currently_open_hopper = None
currently_open_hopper_item_count = 0
all_done = False
first_time = True
extreme_avg_and_modifier_dct = get_extreme_avg_and_modifier_combo_for_stats(extreme_avg_and_modifier_json_dir=r'D:\python_scripts\swg\loot_tables\extreme_values', 
        loot_table_dir=r'D:\python_scripts\swg\dsrc\sku.0\sys.server\compiled\game\datatables\ship\components')


def main(sorting_task, calibration_desires_dct, sorting_desires_dct):
    global first_time, all_done
    swg_window.set_focus()
    time.sleep(1)
    calibrate_containers(calibration_desires_dct=calibration_desires_dct)
    if sorting_task == 'pob_pickup':
        # We are dropping off loot that is in a POB in space.
        # Start in land location of Doaba Guerfel starport.
        # Launch
        # Go to Rosethorn
        # Dock with Rosethorn
        # Go to loot room
        # Pick up loot into inventory
        # Put collection items into hoppers and good loot into droids
        # Go to escape pod room
        # Use escape pod
        # Go to chassis dealer and sell
        # Launch
        # Repeat process, but dock with melmaso
        # Repeat process, but dock with melmaso' and dont launch.
        # Go to land location of Doaba Guerfel starport.
        sort_loot_when_in_house(sorting_desires_dct)
        
        return
    elif sorting_task == 'POB':
        sort_loot_when_in_POB()
        return
    elif sorting_task == 'house':    
        round_trip_i = 0
        while not all_done:
            sort_loot_when_in_house(sorting_desires_dct)
            pdi.press('alt')
            if first_time or not all_done:
                orient(open_inventory=False)
                gtc.go_to_chassis_dealer(calibrate_to_north=round_trip_i == 0)
            round_trip_i += 1
            if all_done and not first_time:
                break
            first_time = False
            if not sorting_desires_dct['crates']:
                break
        scan_DIs()
    elif sorting_task == 'kash':
        sort_kash_nunes()
        return
    elif sorting_task == 'scan_DIs':
        scan_DIs()
    elif sorting_task == 'query':
        for lvl in list(range(1,11))[::-1]:
            for percentile in [0.95, 0.96, 0.97, 0.98, 0.99, 0.999, 0.9999, 0.99999]:
                get_value_of_desired_percentile(component_type='droid_interface', re_lvl=str(lvl), stat_key='Droid_Command_Speed', desired_percentile=percentile, iterator_magnitude=0.1, start_value=50)

if __name__ == '__main__':
    main(config.config_dct[toon_name + '_sort_space_components']['sorting_task'],
         config.config_dct[toon_name + '_sort_space_components']['calibration_desires_dct'],
         config.config_dct[toon_name + '_sort_space_components']['sorting_desires_dct']
        )
    
'''
TODO
. Make it so you can scroll through container contents (so you can store, more packs, for example.)
. Deal with full good loot hoppers, junk loot hoppers, non-space hoppers, or crate hoppers
. Deal with when house is full (could happen if sorting crates).
. sort_crates can eventually have more than 1 Crates hopper
. Make get_item_coords not have hard-coded number of columns, but this is determined based on item width, height, and on window position and size.
'''