# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 20:30:53 2021

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
from python_utils import file_utils
os = file_utils.os
np = file_utils.np
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import run_waypoint_path as rwp
import pydirectinput as pdi
import swg_window_management as swm
import swg_utils
import time
import get_land_coords as glc


swg_window = swm.swg_windows[0]
region = swm.swg_window_regions[0]


def find_travel_button():
    travel_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Travel.csv'), dtype=int)
    img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    # Assume Travel button is in the bottom half of the screen.
    travel_button_idx, _ = swg_utils.find_arr_on_region(travel_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), fail_gracefully=False)
    return travel_button_idx


def click_on_travel_button(travel_button_idx=None, return_delay=0):
    # Find and click on travel button
    if travel_button_idx is None:
        travel_button_idx = find_travel_button()
    swg_utils.click(button='left', start_delay=0, return_delay=return_delay, interval_delay=0, window=None, region=region, coords_idx=travel_button_idx)
    return travel_button_idx
    

def instant_travel_vehicle():
    # Switch to toolbar pane with itv command on it.
    swg_utils.press(['ctrl', '2'], return_delay=0.2)
    # Press the itv command
    swg_utils.press(['1'], return_delay=1)
    # Click to open the itv window
    swg_utils.click(return_delay=4)
    # Click on Mos Espa Starport
    travel_button_idx = find_travel_button()
    starport_idx = [travel_button_idx[0] - 425, travel_button_idx[1] - 242]
    swg_utils.click(button='left', presses=2, start_delay=0.5, return_delay=0.5, interval_delay=0, window=None, region=region, coords_idx=starport_idx)
    time.sleep(14)
    
    
def open_ship_details_window():
    select_button_idx = None
    while select_button_idx is None:
        # Click to open the Starship Terminal
        swg_utils.click(return_delay=4)
        select_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Select.csv'), dtype=int)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                    sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        # Assume Select button is in the bottom half of the screen.
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), fail_gracefully=True)
        if select_button_idx is None:
            # Someone is in the way.
            time.sleep(5)
    # Click on Select button
    swg_utils.click(button='left', start_delay=0, return_delay=4, interval_delay=0, window=None, region=region, coords_idx=select_button_idx)
    
    
def space_travel():
    open_ship_details_window()
    _ = click_on_travel_button(return_delay=3)
    travel_button_idx = find_travel_button()
    lok_idx = [travel_button_idx[0] - 170, travel_button_idx[1] - 60]
    swg_utils.click(button='left', start_delay=0, return_delay=1, interval_delay=0, window=None, region=region, coords_idx=lok_idx)
    _ = click_on_travel_button(travel_button_idx=travel_button_idx, return_delay=14)
    
def sell_to_chassis_dealer():
    # Click on chassis dealer
    swg_utils.click(return_delay=3)
    # Back up
    pdi.press('s', presses=2)
    swg_utils.chat('/ui action conversationResponse0', start_delay=0, return_delay=5)
    select_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Select.csv'), dtype=int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, fail_gracefully=False)
    while select_button_idx is not None:
        # Press and hold enter to sell quickly.
        pdi.keyDown('enter')
        time.sleep(35)
        pdi.keyUp('enter')
        time.sleep(3)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, fail_gracefully=True)
        # The "select" on the SELL LOOT window will disappear once all loot has been sold.
        
        
def launch_ship():
    open_ship_details_window()
    # Find travel button to click on Launch Ship button
    travel_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Travel.csv'), dtype=int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    # Assume Travel button is in the bottom half of the screen.
    travel_button_idx, _ = swg_utils.find_arr_on_region(travel_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), fail_gracefully=False)
    # Launch Ship button is 100 columns to the left of Travel button.
    launch_ship_idx = [travel_button_idx[0], travel_button_idx[1] - 100]
    swg_utils.click(button='left', start_delay=0, return_delay=14, interval_delay=0, window=None, region=region, coords_idx=launch_ship_idx)
    
    
def empty_function():
    pass


def go_home_via_G9():
    pdi.press('0')
    time.sleep(2)
    pdi.click()
    time.sleep(2)
    pdi.press('down')
    time.sleep(0.1)
    pdi.press('enter')
    time.sleep(14)


def go_to_chassis_dealer(swg_window_i=0, calibrate_to_north=True):
    global swg_window, region
    swg_window = swm.swg_windows[swg_window_i]
    region = swm.swg_window_regions[swg_window_i]
    waypoint_csv_path = os.path.join(git_path, 'house_to_chassis_dealer.csv')
    arrow_rect_csv_fpath = os.path.join(git_path, 'arrow_rect.csv')
    rwp.main(swg_window_i, waypoint_csv_path, function_list=[empty_function, instant_travel_vehicle, sell_to_chassis_dealer, space_travel,  go_home_via_G9], arrow_rect_csv_fpath=arrow_rect_csv_fpath, calibrate_to_north=calibrate_to_north)


def main():
    swg_window.set_focus()
    time.sleep(0.5)
    go_to_chassis_dealer()
    
    
if __name__ == '__main__':
    main()