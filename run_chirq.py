# -*- coding: utf-8 -*-
"""
Created on Tue Jul 27 23:23:19 2021

@author: trose
"""

from config_utils import Instruct
import socket
config_fpath = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config = Instruct(config_fpath)
config.get_config_dct()
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils, windows_process_utils
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import time
import numpy as np
import pydirectinput_tmr as pdi
import get_land_coords as glc
import waypoint_path as wpp
import swg_window_management as swm
import random
import string
import swg_utils
os = file_utils.os

swg_window_i = config.config_dct['main']['swg_window_i']
if swg_window_i is None:
    # Set custom value here
    swg_window_i = 0
swg_window = swm.swg_windows[swg_window_i]
region = swm.swg_window_regions[swg_window_i]

destroy_arr = file_utils.read_csv(os.path.join('words_dir', 'Destroy.csv'), dtype=int)
player_nearby_global = False

def check_if_player_nearby(swg_window, letters_to_skip=[]):
    meters_m_arr = file_utils.read_csv('meters_m.csv', dtype=int)
    rect = swg_window.rectangle()
    height_of_window_header = 26
    # The screen part to capture
    region = {'top': rect.top + height_of_window_header, 'left': rect.left, 'width': rect.width(), 'height': rect.height() - height_of_window_header}
    alphabet = string.ascii_lowercase
    row_of_meters = 73
    col_of_single_digit_meters = 310
    col_of_double_digit_meters = 316
    row_of_target_name = 17
    col_of_target_name = 337
    target_name_height = 7
    target_name_width = 65
    # Black White (grayscale) color
    cyan_bw_shade = 145
    purple_bw_shade = 80
    for letter in alphabet + "'-":
        if letter in letters_to_skip:
            continue
        swg_utils.chat('/tar ' + letter, start_delay=0, return_delay=0.1, interval_delay=0.1)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, sharpen_threshold=255, scale_to=255, set_focus=False, sharpen=True)
        if (np.all(img_arr[row_of_meters : row_of_meters + meters_m_arr.shape[0], col_of_single_digit_meters : col_of_single_digit_meters + meters_m_arr.shape[1]] == meters_m_arr) or 
            np.all(img_arr[row_of_meters : row_of_meters + meters_m_arr.shape[0], col_of_double_digit_meters : col_of_double_digit_meters + meters_m_arr.shape[1]] == meters_m_arr)):
            # We've targeted something within 100m away.
            # Determine whether the target is a plyaer or not.
            # If it's a player, the name will be cyan or purple which have grayscale colors of 145 and 80, respectively.
            # If the number of matches is greater than a threshold, then say it's a player
            img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, sharpen_threshold=255, scale_to=255, set_focus=False, sharpen=False)
            target_name_arr = img_arr[row_of_target_name : row_of_target_name + target_name_height, col_of_target_name : col_of_target_name + target_name_width]
            if len(np.where(target_name_arr == cyan_bw_shade)[0]) > 40 or len(np.where(target_name_arr == purple_bw_shade)[0]) > 40:
                return True
    return False

def check_if_player_nearby_2():
    global player_nearby_global
    # Cyan is B: 171, G: 161, R: 0
    # Purple is B: 198, G: 0, R: 132
    
    # Find talus, then use the top left corner of the grayscale csv for talus as the starting point. (relative coordinates / search region)
    # Search the 114 x 114 matrix for cyan and purple (with BGR) only where the grayscale talus was 0
    # If you find even 1 pixel of cyan or purple in the allowed search region, say there's a player.
    player_nearby = True
    while player_nearby:
        img_arr = swg_utils.take_screenshot(region=radar_region, set_focus=False)
        #swg_utils.save_BGR_to_csvs(img_arr, '.', 'debug')
        # Find all indices of cyan and purple
        purple_set = swg_utils.find_pixels_on_BGR_arr(img_arr, b=198, g=0, r=132, return_as_set=True)
        cyan_set = swg_utils.find_pixels_on_BGR_arr(img_arr, b=171, g=161, r=0, return_as_set=True)
        player_set = purple_set.union(cyan_set)
        player_nearby = len(radar_searchable_indices.intersection(player_set)) > 0
        if player_nearby:
            player_nearby_global = True
    
    
def get_radar_region(swg_window, region, planet='Talus'):
    planet_arr = swg_utils.get_search_arr(planet, dir_path='land_ui_dir', mask_int=0)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, sharpen=False, sharpen_threshold=212)
    # Assume radar is in upper right corner
    planet_idx, _ = swg_utils.find_arr_on_region(planet_arr, region=region, img_arr=img_arr, start_col=int(img_arr.shape[1]/2), fail_gracefully=False)
    # Talus on row 78 and col 43
    radar_region = {'left': planet_idx[1] - 43 + region['left'], 'top': planet_idx[0] - 78 + region['top'], 'width': 114, 'height': 114}
    return radar_region


def get_radar_searchable_indices(planet='Talus'):
    planet_radar_csv = os.path.join('land_ui_dir', planet + '_radar_grayscale.csv')
    planet_radar_arr = file_utils.read_csv(planet_radar_csv, dtype=int)
    where_arr = np.where(planet_radar_arr == 0)
    searchable_indices = set(tuple(zip(where_arr[0], where_arr[1])))
    return searchable_indices
    


def empty_function():
    pass


def attack():
    '''
    Returns
    -------
    None

    Purpose
    -------
    Attack macro via python when you're in an area that they automatically
    dump your in-game macros.
    '''
    for _ in range(2):
        pdi.press('tab')
        time.sleep(0.05)
        pdi.press('r')
        time.sleep(0.05)
        pdi.press('1')
        time.sleep(0.05)
        pdi.press('2')
        time.sleep(0.05)
        pdi.press('3')
        time.sleep(0.05)
        pdi.press('4')
        time.sleep(0.05)
        pdi.press('5')
        time.sleep(0.05)
        pdi.press('6')
        time.sleep(0.05)
        pdi.press('7')
        time.sleep(0.05)
        pdi.press('8')
        time.sleep(0.05)
        pdi.press('9')
        time.sleep(0.05)
        pdi.press('-')
        time.sleep(0.05)
        pdi.press('=')
        time.sleep(0.05)
        time.sleep(1)
        

def destroy_for_all_windows():
    item_to_destroy_coord_list = [[380, 550]]
    num_items_to_destroy = [17]
    radial_option_delta_dct = {'6': [52, -106], '5': [70, -12], '4': [52, 81], '3': [-3, 104], '2': [-59, 81]}
    for i in range(len(swm.swg_windows)):
        #if i != 2:
        #    continue
        #swg_utils.press(['alt', 'tab'], presses=1, return_delay=0.5)
        #swg_window = swm.swg_windows[i]
        #pdi.keyDown('alt')
        #swg_utils.press(['tab'], presses=3, return_delay=0.5)
        #pdi.keyUp('alt')
        
        region = swm.swg_window_regions[i]
        
        time.sleep(0.8)
        pdi.press('esc', presses=2)
        pdi.press('i')
        mouse_pos = item_to_destroy_coord_list[i]
        pdi.moveTo(x=mouse_pos[0], y=mouse_pos[1])
        raise Exception('done')
        for j in range(num_items_to_destroy[i]):
            swg_utils.click(coords=mouse_pos, button='right', start_delay=0, return_delay=0.3)
            img_arr = glc.take_screenshot_and_sharpen(swg_window, region, 
                    sharpen_threshold=230, scale_to=255, set_focus=False, sharpen=True)
            
            mouse_idx = [mouse_pos[1] - region['top'], mouse_pos[0] - region['left']]
            for radial_option in radial_option_delta_dct:
                potential_destroy_idx = [radial_option_delta_dct[radial_option][0] + mouse_idx[0], radial_option_delta_dct[radial_option][1] + mouse_idx[1]]
                if np.all(img_arr[potential_destroy_idx[0] : potential_destroy_idx[0] + destroy_arr.shape[0], potential_destroy_idx[1] : potential_destroy_idx[1] + destroy_arr.shape[1]] == destroy_arr):
                    pdi.press(radial_option)
            time.sleep(0.7)
        swg_utils.press('i', return_delay=0.1)
        

radar_searchable_indices = get_radar_searchable_indices(planet='Talus')
radar_region = get_radar_region(swg_window, region)
def main():
    global player_nearby_global
    time.sleep(0.5)
    swg_window.set_focus()
    time.sleep(1)
    waypoint_list = list(map(list, np.array(file_utils.read_csv('aclo_grenadier.csv')).astype(int)))
    glc.north_calibrate(swg_window, arrow_rect_csv_fpath='arrow_rect.csv')
    for _ in range(2000):
        wpp.move_along(swg_window, waypoint_list, function_list=[check_if_player_nearby_2, attack, destroy_for_all_windows])
        if player_nearby_global:
            while check_if_player_nearby(swg_window, letters_to_skip=['o']):
                for _ in range(3):
                    swg_utils.chat('/ui action untarget')
                time.sleep(60)
            player_nearby_global = False
    
if __name__ == '__main__':
    main()