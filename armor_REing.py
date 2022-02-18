import time
import pyautogui as pag
from config_utils import Instruct
import socket
config_fpath = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config = Instruct(config_fpath)
config.get_config_dct()
import swg_window_management as swm
import os
import pydirectinput_tmr as pdi
import numpy as np
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils
import random
from copy import deepcopy
import get_land_coords as glc
import swg_utils


inventory_arr_dir = 'inventory_dir'
top_left_corner_of_description_csv = os.path.join(inventory_arr_dir, 'top_left_corner_of_description_section.csv')
top_left_corner_of_description_arr = np.array(file_utils.read_csv(top_left_corner_of_description_csv)).astype(np.int)
stat_names = ['Power', 'Item_Count', 'sockets_available']
stat_arr_dct = {stat_name : np.array(file_utils.read_csv(os.path.join(inventory_arr_dir, stat_name + '.csv'))).astype(np.int) for stat_name in stat_names}

'''
inventory_digit_csv_dir: str
    Directory containing csv files which each represent the matrix of a 
    particular digit. e.g. '0.csv', '1.csv', 'negative_sign.csv'.
    
inventory_digit_csvs: list of str
    List of csv fpaths for the digit files.
    
digit_arr: 2D np.array
    The matrix that is stored in the csv file for a particular digit.
    
digit_fname: str
    The filename without path information or extension. e.g. '0', '1', ... '9'
    
inventory_digit_dct: dict of 2D np.array
    Keys: 0', '1', ..., '9'
    Values: The digit_arr for the corresponding key
    
Notes
-----
1. This is executed here, globally, so that the files only have to be loaded
    into the dictionary one time.
    
2. The digit_arr matrices which are stored in the csv files were gotten in the
    following way:
    1. Use the calibrate_window_position function to get the windows into
        position.
    2. Use take_grayscale_screenshot.py to get a csv file with the sharpened
        grayscale image array.
    3. Use the outputted csv file to find and copy the cells corresponding to
        each digit (without including the columns that contain all zeros or 
        only one non-zero number) and copy and paste this selection of cells 
        to a new csv document and save to a csv file without an index or column
        labels.
'''
digit_lst = list(map( str,list(range(10))))
inventory_digit_csv_dir='inventory_dir'
inventory_digit_csvs = file_utils.find(inventory_digit_csv_dir, '*.csv')
inventory_digit_csvs = [fpath for fpath in inventory_digit_csvs if file_utils.fname_from_fpath(fpath) in digit_lst]
inventory_digit_dct = {}
for digit_csv in inventory_digit_csvs:
    digit_arr = np.array(file_utils.read_csv(digit_csv)).astype(np.int)
    digit_fname = file_utils.fname_from_fpath(digit_csv)
    inventory_digit_dct[digit_fname] = digit_arr
    
swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
swg_window = swm.swg_windows[swg_window_i]
region = swm.swg_window_regions[swg_window_i]

    
def find_top_left_of_corner_description(swg_window_region):
    # Inventory must be open already and the description section must
    # be visible.
    img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=swg_window_region, sharpen_threshold=160,
            scale_to=255, sharpen=True)

    for j in range(img_arr.shape[1]):
        for i in range(img_arr.shape[0]):
            if np.all(img_arr[i : i + top_left_corner_of_description_arr.shape[0], 
                    j : j + top_left_corner_of_description_arr.shape[1]] ==
                    top_left_corner_of_description_arr):
                
                return i, j, img_arr
    file_utils.write_rows_to_csv('top_corner.csv', list(map(list,img_arr)))
    return None, None, None


def drag_item(autoit_dir, start_coords, end_coords, delay=1):
    time.sleep(0.5)
    file_utils.write_rows_to_csv(os.path.join(autoit_dir, 'drag_coords.csv'), 
            [start_coords, end_coords])
    
    os.system(os.path.join(autoit_dir, 'drag_mouse.exe'))
    time.sleep(delay)
    
    
def click(coords, button='left', delay=1):
    time.sleep(0.5)
    pdi.moveTo(coords[0], coords[1])
    pdi.mouseDown(button=button)
    pdi.mouseUp(button=button)
    time.sleep(delay)
    
    
def press_item_radial_option(item_coords, 
        radial_option_key):
    '''
    Parameters
    ----------
    item_coords: list of int
        [x, y] coordinates on the monitor that the item is located and visible.
        
    radial_option_key: str
        Key to press once the radial menu is visible ('1', '2',...,'9')

    Returns
    -------
    None
    
    Purpose
    -------
    Given the coordinates of the item in an open inventory, this function
    will right click on the item to open the radial menu and press the 
    radial_option_key key to select that radial option.
    '''
    click(item_coords, button='right', delay=2)
    pdi.press(radial_option_key)
    
    
def get_number_from_arr(line_arr, digit_dct, numeric_type=int):
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
    digits = ''
    i = 0
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
            target_digit = line_arr[:, i : j].astype(np.int)
            # Increase i so it is starting on a column of all zeros and thus
            # ready to find the next digit.
            i += j - i
            # Iterate through all the stored digit matrices to see if one
            # matches.
            for digit_key, digit_arr in digit_dct.items():
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
    return numeric_type(digits)


def dump_macros():
    # Dump macros
    pdi.keyDown("shift")
    pdi.press('3')
    pdi.keyUp("shift")


class REing:
    def __init__(self, autoit_dir=r'D:\autoit\swg\REing', 
            junk_RE_tool_coords=[region['left'] + 315, 340],
            bit_RE_tool_coords=[region['left'] + 378, 340],
            free_item_coords=[region['left'] + 441, 340],
            knife_coords=[region['left'] + 504, 340],
            crate_of_knives_coords=[region['left'] + 711, 276],
            backpack_coords=[region['left'] + 448, 278],
            ok_coords = [region['left'] + 428, 434],
            next_statted_loot_coords=[region['left'] + 971, 119],
            next_crate_of_knives_coords=[region['left'] + 966, 349],
            num_junk_loots=3012,
            num_statted_loots=50,
            num_crates_of_knives=50,
            space_remaining_in_backpack=50, 
            corner_description_coords=[]):
        
        self.autoit_dir = autoit_dir
        self.initial_junk_RE_tool_coords = junk_RE_tool_coords
        self.initial_bit_RE_tool_coords = bit_RE_tool_coords
        self.initial_free_item_coords = free_item_coords
        # coords of knife once it is extracted from the crate. It should be
        # in the next inventory slot after free_item_coords
        self.initial_knife_coords = knife_coords
        # coords of the crate of knives in your inventory.
        self.initial_crate_of_knives_coords = crate_of_knives_coords
        # Backpack in inventory that will contain the completed 35s.
        self.initial_backpack_coords = backpack_coords
        self.initial_next_statted_loot_coords = next_statted_loot_coords
        self.initial_next_crate_of_knives_coords = next_crate_of_knives_coords
        # Lower of the 2 types of junk loots in the junk RE tool.
        self.num_junk_loots = num_junk_loots
        self.num_statted_loots = num_statted_loots
        # number of crates in the container. This is in addition to the one you
        # already have in your inventory located at crate_of_knives_coords.
        self.num_crates_of_knives = num_crates_of_knives
        # Backpack in inventory that will contain the completed 35s.
        self.space_remaining_in_backpack = space_remaining_in_backpack
        # Coords of OK button when being asked whether to fuse items when attaching
        # SEA to knife.
        self.initial_ok_coords = ok_coords
        self.corner_description_coords = corner_description_coords
        
        self.randomize_coords()
        
        self.left_of_stat = 7 + self.corner_description_coords[0]
        self.digit_height = 7
        self.max_num_digits = 10
        self.usual_digit_width = 5
       
        
    def randomize_coords(self):
        '''
        Purpose
        -------
        Randomly add a pixel up and/or down to the initial ones given in case 
        devs are looking to see whether you are clicking in the same exact 
        locations to detect 3rd part programs.
        '''
        self.junk_RE_tool_coords = [coord + random.randint(-2,2) for coord in self.initial_junk_RE_tool_coords]
        self.bit_RE_tool_coords = [coord + random.randint(-2,2) for coord in self.initial_bit_RE_tool_coords]
        self.free_item_coords = [coord + random.randint(-2,2) for coord in self.initial_free_item_coords]
        self.knife_coords = [coord + random.randint(-2,2) for coord in self.initial_knife_coords]
        self.crate_of_knives_coords = [coord + random.randint(-2,2) for coord in self.initial_crate_of_knives_coords]
        self.backpack_coords = [coord + random.randint(-2,2) for coord in self.initial_backpack_coords]
        self.next_statted_loot_coords = [coord + random.randint(-2,2) for coord in self.initial_next_statted_loot_coords]
        self.next_crate_of_knives_coords = [coord + random.randint(-2,2) for coord in self.initial_next_crate_of_knives_coords]
        self.ok_coords = [coord + random.randint(-2,2) for coord in self.initial_ok_coords]
        time.sleep(random.random() * 2)
        
        
    def get_stat_value(self, stat_name, stat_coords, fail_gracefully=False):
        attempt_limit = 2
        for attempt_number in range(attempt_limit):
            stat_value = None
            click(stat_coords, button='left', delay=2)
            img_arr = glc.take_screenshot_and_sharpen(swg_window, region, 
                    sharpen_threshold=160, scale_to=255, set_focus=False, sharpen=True)
            
            for i in range(self.corner_description_coords[1], img_arr.shape[0]):
                if np.all(img_arr[i : i + stat_arr_dct[stat_name].shape[0], self.left_of_stat : self.left_of_stat + stat_arr_dct[stat_name].shape[1]] == stat_arr_dct[stat_name]):
                    self.left_of_number = self.left_of_stat + stat_arr_dct[stat_name].shape[1] + 1
                    line_arr = img_arr[i : i + self.digit_height, self.left_of_number : self.left_of_number + self.usual_digit_width * self.max_num_digits]
                    stat_value = get_number_from_arr(line_arr, inventory_digit_dct, numeric_type=int)
                    break
            if stat_value is None and not fail_gracefully:
                if attempt_number == attempt_limit - 1:
                    dump_macros()
                    raise Exception('Could not find', stat_name)
                else:
                    continue
            else:
                return stat_value
        
        
    def put_power_bit_into_RE_tool(self):
        swg_utils.click_drag(self.free_item_coords, self.bit_RE_tool_coords, start_delay=0.5, return_delay=1)
        

    def get_power_bit(self):
        # Pick up a new statted loot.
        press_item_radial_option(self.next_statted_loot_coords, '1')
        # Move statted loot to inside the RE tool
        swg_utils.click_drag(self.free_item_coords, self.bit_RE_tool_coords, start_delay=0.5, return_delay=1)
        # RE
        press_item_radial_option(self.bit_RE_tool_coords, '5')
        # Put power bit into RE tool
        self.put_power_bit_into_RE_tool()
        self.num_statted_loots -= 1
    
    
    def get_mod_bit(self):
        # RE to get new mod bit
        press_item_radial_option(self.junk_RE_tool_coords, '5')
        # Move mod bit to the bit RE tool
        swg_utils.click_drag(self.free_item_coords, self.bit_RE_tool_coords, start_delay=0.5, return_delay=1)
        self.num_junk_loots -= 1


    def get_SEA(self):
        time.sleep(1.5)
        press_item_radial_option(self.bit_RE_tool_coords, '6')
        
        
    def attach_SEA_to_knife(self):
        swg_utils.click_drag(self.free_item_coords, self.knife_coords, start_delay=0.5, return_delay=0.6)
        click(self.ok_coords, button='left')


    def get_knife(self):
        '''
        Returns
        -------
        None

        Purpose
        -------
        Get a knife from the crate in your inventory. If it was the last one,
        then replace the crate with one from the container of crates.
        '''
        got_knife = False
        while not got_knife:
            # Get number of knives remaining in the crate that is in the inventory
            item_count = self.get_stat_value('Item_Count', self.crate_of_knives_coords)
            # Get knife from crate.
            press_item_radial_option(self.crate_of_knives_coords, '1')
            item_count -= 1
            if item_count == 0:
                # Pick up new crate
                press_item_radial_option(self.next_crate_of_knives_coords, '1')
                swg_utils.click_drag(self.knife_coords, self.crate_of_knives_coords, start_delay=0.5, return_delay=1)
                self.num_crates_of_knives -= 1
            sockets_available = self.get_stat_value('sockets_available', self.knife_coords, fail_gracefully=True)
            if sockets_available is None:
                # Destroy this knife that doesn't have a socket
                press_item_radial_option(self.knife_coords, '4')
            else:
                got_knife = True
            

    def RE_knife(self):
        # Move knife into RE tool
        swg_utils.click_drag(self.free_item_coords, self.bit_RE_tool_coords, start_delay=0.5, return_delay=1)
        # RE
        press_item_radial_option(self.bit_RE_tool_coords, '5')
        
        
    def finish_up_power_bit(self):
        # Click on power bit to see its power value.
        click(self.free_item_coords, button='left', delay=3.5)
        # If power 35, move power bit into backpack else, move it into RE tool
        if self.get_stat_value('Power', self.free_item_coords) == 35:
            # Move poewr bit into backpack
            swg_utils.click_drag(self.free_item_coords, self.backpack_coords, start_delay=0.5, return_delay=1)
            self.space_remaining_in_backpack -= 1
            # Get new power bit
            self.get_power_bit()
        else:
            swg_utils.click_drag(self.free_item_coords, self.bit_RE_tool_coords, start_delay=0.5, return_delay=1)
    
    
def main():
    # time limit in seconds. Useful for ent buffs or pups
    time_limit = 5.2 * 3600
    start_time = time.time()
    top_of_corner_description, left_of_corner_description, img_arr = find_top_left_of_corner_description(region)
    corner_description_coords = [left_of_corner_description, top_of_corner_description]
    REer = REing(corner_description_coords=corner_description_coords)
    #print('get power bit')
    #REer.get_power_bit()
    REer.put_power_bit_into_RE_tool()
    while REer.num_junk_loots > 0 and REer.num_statted_loots > 0 and REer.num_crates_of_knives > 0 and REer.space_remaining_in_backpack > 0 and time.time() - start_time < time_limit:
        print('get mod bit')
        REer.get_mod_bit()
        print('get SEA')
        REer.get_SEA()
        print('get knife')
        REer.get_knife()
        print('attach SEA to knife')
        REer.attach_SEA_to_knife()
        print('RE knife')
        REer.RE_knife()
        print('finishing up power bit')
        REer.finish_up_power_bit()
        print('done')
        REer.randomize_coords()
    dump_macros()
        
        
if __name__ == '__main__':
    swg_window.set_focus()
    main()
    #top_of_corner_description, left_of_corner_description, img_arr = find_top_left_of_corner_description()
    #find_stats(img_arr, top_of_corner_description, left_of_corner_description)
    
'''
TODO
Nice to haves
1. Put new junk loot into RE tool when empty instead of manually putting the number of junk loots
2. Could determine the remaining copacity of backpack instead of manually setting it.
3. Could determine whether there are any more crates or statted loot after the attempt to pick up was made (check for item count or stat value)
'''