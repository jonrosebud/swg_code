# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 15:55:17 2021

@author: trose
"""

import time
import pyautogui as pag
import swg_window_management as swm
import swg_utils
import os
import pydirectinput as pdi
import numpy as np
import sys
sys.path.append(r'C:\Users\trose\Documents\python_packages')
from python_utils import file_utils
import random


inventory_arr_dir = 'inventory_dir'
top_left_corner_of_description_csv = os.path.join(inventory_arr_dir, 'top_left_corner_of_description_section.csv')
top_left_corner_of_description_arr = np.array(file_utils.read_csv(top_left_corner_of_description_csv)).astype(np.int)
stat_names = ['agility', 'camouflage', 'constitution', 'luck', 'precision', 'stamina', 'strength']
stat_arr_dct = {stat_name : np.array(file_utils.read_csv(os.path.join(inventory_arr_dir, stat_name + '.csv'))).astype(np.int) for stat_name in stat_names}
stats_to_keep = [23, 24, 25]
stats_to_keep_arr_dct = {stat_to_keep : np.array(file_utils.read_csv(os.path.join(inventory_arr_dir, str(stat_to_keep) + '.csv'))).astype(np.int) for stat_to_keep in stats_to_keep}
contents_for_backpack_csv = os.path.join(inventory_arr_dir, 'Contents.csv')
contents_for_backpack_arr = np.array(file_utils.read_csv(contents_for_backpack_csv)).astype(np.int)


def press_destroy(item_to_destroy_coords,
        destroy_keys=['6', '4', '5', '3'], spin=True):
    '''
    Parameters
    ----------
    item_to_destroy_coords: list of int
        This list is the [x, y] coordinates on the monitor that the item to
        destory is located and visible.
        
    destroy_keys: list of str
        List of single digit keys (2-6) that could be the destroy key. This 
        function will try pressing each of these keys in the order provided.
        When indoors, the default value ['6', '4', '5', '3'] will usually
        work.
        
    spin: bool
        True: Send ctrl shift s to make the toon spin
        False: Do not send strl shift s

    Returns
    -------
    None
    
    Purpose
    -------
    Given the coordinates of the item in an open inventory, this function
    will loop through destroy keys, right clicking on the item to open the 
    radial menu and pressing the next key in destroy_keys. The idea is that 
    at least one of these keys will be the destroy key and that the order
    of the provided destroy_keys will be such as to not open up a window
    (such as Examine) because then the item will probably not be destroyed
    after this function has run (if the window covers up the item).
    
    Notes
    -----
    1. This function currently iterates through all of the keys in destroy_keys
        regardless of whether one of the keys succeeded in destroying the 
        item. This means that the possibility exists that this function will
        destroy one item and then Examine or Destroy etc the item that is
        next in the inventory which now occupies the same coordinates as the
        original item.
    '''
    
    for destroy_key in destroy_keys:
        pdi.moveTo(item_to_destroy_coords[0], item_to_destroy_coords[1])
        pdi.mouseDown(button='right')
        pdi.mouseUp(button='right')
        time.sleep(0.5)
        pdi.press(destroy_key)
        
    if spin:
        # Make the toon spin!
        pdi.press('d', presses=2)
        pdi.keyDown('ctrl')
        pdi.keyDown('shift')
        pdi.press('s')
        pdi.keyUp('shift')
        pdi.keyUp('ctrl')
    
    
def find_top_left_of_corner_description(swg_window_region):
    # Inventory must be open already and the description section must
    # be visible.
    img_arr = swg_utils.take_screenshot(swg_window_region)
    img_arr = swg_utils.take_grayscale_screenshot(img_arr, sharpen_threshold=160,
            scale_to=255, sharpen=True)

    for j in range(img_arr.shape[1]):
        for i in range(img_arr.shape[0]):
            if np.all(img_arr[i : i + top_left_corner_of_description_arr.shape[0], 
                    j : j + top_left_corner_of_description_arr.shape[1]] ==
                    top_left_corner_of_description_arr):
                
                return i, j, img_arr
    file_utils.write_rows_to_csv('top_corner.csv', list(map(list,img_arr)))
    return None, None, None


def determine_if_worth_keeping(img_arr, top_of_stat, left_of_stat):
    left_of_number = left_of_stat + 80
    for stat_to_keep, stat_to_keep_arr in stats_to_keep_arr_dct.items():
        for i in range(top_of_stat, top_of_stat + stat_to_keep_arr.shape[0]):
            if np.all(img_arr[i : i + stat_to_keep_arr.shape[0], left_of_number : left_of_number + stat_to_keep_arr.shape[1]] == stat_to_keep_arr):
                return True
    return False


def find_stats(img_arr, top_of_corner_description, left_of_corner_description):
    left_of_loot_backpack = 7 + left_of_corner_description
    for i in range(top_of_corner_description, img_arr.shape[0]):
        if np.all(img_arr[i : i + contents_for_backpack_arr.shape[0], left_of_loot_backpack : left_of_loot_backpack + contents_for_backpack_arr.shape[1]] == contents_for_backpack_arr):
            return False
    left_of_stat = 27 + left_of_corner_description
    for stat_name, stat_arr in stat_arr_dct.items():
        for i in range(top_of_corner_description, img_arr.shape[0]):
            if np.all(img_arr[i : i + stat_arr.shape[0], left_of_stat : left_of_stat + stat_arr.shape[1]] == stat_arr):
                worth_keeping = determine_if_worth_keeping(img_arr, i, left_of_stat)
                if worth_keeping:
                    return True
    return False


def get_coords_of_item(top_of_corner_description, left_of_corner_description, swg_window_region, item_inventory_position):
    '''
    Parameters
    ----------
    top_of_corner_description: int
        row index of the img_arr of the swg_window for the top of the leftmost line bounding the item description area in the inventory.
    
    left_of_corner_description: int
        col index of the img_arr of the swg_window for the leftmost line bounding the item description area in the inventory.
        
    swg_window_region: dict
        region of the monitor used when getting the img_arr.
        Keys: 'left', 'top', 'width', 'height'
        
    item_inventory_position: int
        The index of the position of the item in the inventory to delete.
        e.g. 0 means delete the first item in the inventory.

    Returns
    -------
    top_of_item: int
        y coordinate on monitor of the item located at item_inventory_position
        
    left_of_item: int
        x coordinate on monitor of the item located at item_inventory_position

    Purpose
    -------
    It might be easier to input the index in the inventory 
    '''
    item_width = 64
    item_height = 65
    # top and left of the center of the item in row 0, column 0 in the inventory
    top_of_first_item = top_of_corner_description + swg_window_region['top'] + 8 + int(item_width / 2)
    left_of_first_item = left_of_corner_description + swg_window_region['left'] + 305
    row_num = int(item_inventory_position / 11)
    col_num = item_inventory_position % 11
    top_of_item = top_of_first_item + item_height * row_num
    left_of_item = left_of_first_item + item_width * col_num
    return top_of_item, left_of_item


def main():
    # Assumes 11 rows and 11 columns are visible.
    # Will only work up to the 121st item in the inventory (including equipped items).
    # Assumes the top left corner of the item description window is visible.
    # Assumes you already have at least 1 of every type of stackacble loot (such as junk loot) that you care about in your inventory.
    # Assumes that the inventory is open before running this program.
    
    # 0-indexed
    my_backpack_inventory_positions = [24, 13, 26]
    item_to_inspect_inventory_positions = [73, 83, 94]
    last_item_inventory_positions = [102, 95, 102]
    outside=[False,False,True]
    swg_window_regions = [{'top': swg_window.rectangle().top, 'left': swg_window.rectangle().left, 'width': swg_window.rectangle().width(), 'height': swg_window.rectangle().height()} for swg_window in swm.swg_windows]
    i = 0
    while True:
        for j, swg_window in enumerate(swm.swg_windows):
            if outside[j]:
                destroy_keys=['5', '4', '3', '2']
            else:
                destroy_keys=['6', '4', '5', '3']
            top_of_corner_description = None
            while top_of_corner_description is None:
                swg_window.set_focus()
                time.sleep(2)
                pdi.press('r')
                time.sleep(1)
                pdi.press('esc', presses=2)
                pdi.press('i')
                time.sleep(8)
                top_of_corner_description, left_of_corner_description, img_arr = find_top_left_of_corner_description(swg_window_regions[j])
            top_of_item_to_inspect, left_of_item_to_inspect = get_coords_of_item(top_of_corner_description, left_of_corner_description, swg_window_regions[j], item_to_inspect_inventory_positions[j])
            pdi.mouseDown(left_of_item_to_inspect, top_of_item_to_inspect)
            pdi.mouseUp(left_of_item_to_inspect, top_of_item_to_inspect)
            time.sleep(5)
            top_of_corner_description, left_of_corner_description, img_arr = find_top_left_of_corner_description(swg_window_regions[j])
            found_stat_worth_keeping = find_stats(img_arr, top_of_corner_description, left_of_corner_description)
            if found_stat_worth_keeping:
                if item_to_inspect_inventory_positions[j] < last_item_inventory_positions[j]:
                    # Move to next open position in inventory
                    item_to_inspect_inventory_positions[j] = item_to_inspect_inventory_positions[j] + 1
                elif random.random() < 0.9:
                    # Attempt to drag item into backpack
                    pdi.click(left_of_item_to_inspect, top_of_item_to_inspect)
                    time.sleep(1)
                    top_of_my_backpack, left_of_my_backpack = get_coords_of_item(top_of_corner_description, left_of_corner_description, swg_window_regions[j], my_backpack_inventory_positions[j])
                    pdi.moveTo(left_of_my_backpack, top_of_my_backpack)
                    pdi.mouseUp(left_of_my_backpack, top_of_my_backpack)
                    pdi.moveTo(left_of_item_to_inspect, top_of_item_to_inspect)
                else:
                    press_destroy([left_of_item_to_inspect, top_of_item_to_inspect], destroy_keys=destroy_keys)
            else:
                press_destroy([left_of_item_to_inspect, top_of_item_to_inspect], destroy_keys=destroy_keys)
            time.sleep(1)
        i += 1
        
if __name__ == '__main__':
    #swm.calibrate_window_position(swm.swg_windows)
    main()
    #top_of_corner_description, left_of_corner_description, img_arr = find_top_left_of_corner_description()
    #find_stats(img_arr, top_of_corner_description, left_of_corner_description)