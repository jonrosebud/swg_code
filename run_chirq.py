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
import time
import numpy as np
import pydirectinput as pdi
import get_land_coords as glc
import waypoint_path as wpp
import swg_window_management as swm
from destroy_junk import press_destroy
import random
import string
import swg_utils
os = file_utils.os

spyder_window = windows_process_utils.get_windows('pythonw.exe', 'Spyder (Python 3.8)', process_df=None)[0]
destroy_arr = np.array(file_utils.read_csv(os.path.join('words_dir', 'Destroy.csv'))).astype(np.int)

def check_if_player_nearby(swg_window, letters_to_skip=[]):
    meters_m_arr = np.array(file_utils.read_csv('meters_m.csv')).astype(np.int)
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
        img_arr = swg_utils.take_grayscale_screenshot_and_sharpen(swg_window, region, sharpen_threshold=255, scale_to=255, set_focus=False, sharpen=True)
        if (np.all(img_arr[row_of_meters : row_of_meters + meters_m_arr.shape[0], col_of_single_digit_meters : col_of_single_digit_meters + meters_m_arr.shape[1]] == meters_m_arr) or 
            np.all(img_arr[row_of_meters : row_of_meters + meters_m_arr.shape[0], col_of_double_digit_meters : col_of_double_digit_meters + meters_m_arr.shape[1]] == meters_m_arr)):
            # We've targeted something within 100m away.
            # Determine whether the target is a plyaer or not.
            # If it's a player, the name will be cyan or purple which have grayscale colors of 145 and 80, respectively.
            # If the number of matches is greater than a threshold, then say it's a player
            img_arr = swg_utils.take_grayscale_screenshot_and_sharpen(swg_window, region, sharpen_threshold=255, scale_to=255, set_focus=False, sharpen=False)
            target_name_arr = img_arr[row_of_target_name : row_of_target_name + target_name_height, col_of_target_name : col_of_target_name + target_name_width]
            if len(np.where(target_name_arr == cyan_bw_shade)[0]) > 40 or len(np.where(target_name_arr == purple_bw_shade)[0]) > 40:
                return True
    return False


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
    spin_toon = [True, True, False]
    item_to_destroy_coord_list = [[769, 601], [1479, 668], [2700,533]]
    num_items_to_destroy = [5,5,14]
    radial_option_delta_dct = {'6': [52, -106], '5': [70, -12], '4': [52, 81], '3': [-3, 104], '2': [-59, 81]}
    for i in range(len(swm.swg_windows)):
        swg_utils.press(['alt', 'tab'], presses=1, return_delay=0.5)
        swg_window = swm.swg_windows[i]
        pdi.keyDown('alt')
        swg_utils.press(['tab'], presses=3, return_delay=0.5)
        pdi.keyUp('alt')
        if i != 2:
            continue
        rect = swg_window.rectangle()
        height_of_window_header = 26
        # The screen part to capture
        region = {'top': rect.top + height_of_window_header, 'left': rect.left, 'width': rect.width(), 'height': rect.height() - height_of_window_header}
        time.sleep(0.8)
        pdi.press('esc', presses=2)
        pdi.press('i')
        mouse_pos = item_to_destroy_coord_list[i]
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
        

def main():
    time.sleep(0.5)
    swg_window = swm.swg_windows[2]
    swg_window.set_focus()
    time.sleep(1)
    waypoint_list = list(map(list, np.array(file_utils.read_csv('aclo_grenadier.csv')).astype(np.int)))
    glc.north_calibrate(swg_window, arrow_rect_csv_fpath='arrow_rect.csv')
    for _ in range(2000):
        wpp.move_along(swg_window, waypoint_list, function_list=[empty_function, attack, destroy_for_all_windows])
        # Wait to start next iteration until no other player is within 100m
        while check_if_player_nearby(swg_window, letters_to_skip=['o']):
            time.sleep(60)
    
    
if __name__ == '__main__':
    main()