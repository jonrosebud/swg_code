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

swg_window_idx = 0
swg_window = swm.swg_windows[swg_window_idx]
region = swm.swg_window_regions[swg_window_idx]


def click_on_travel_button(return_delay=0):
    # Find and click on travel button
    travel_button_arr = np.array(file_utils.read_csv(os.path.join('land_ui_dir', 'Travel.csv'))).astype(np.int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    # Assume Travel button is in the bottom half of the screen.
    travel_button_idx, _ = swg_utils.find_arr_on_region(travel_button_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=int(img_arr.shape[0]/2), start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False)
    if travel_button_idx is None:
        return False
    swg_utils.click(button='left', start_delay=0, return_delay=return_delay, interval_delay=0, window=None, region=region, coords_idx=travel_button_idx)
    return True
    

def instant_travel_vehicle():
    # Switch to toolbar pane with itv command on it.
    swg_utils.press(['ctrl', '2'], return_delay=0.2)
    # Press the itv command
    swg_utils.press(['1'], return_delay=0.4)
    # Open the itv window
    swg_utils.chat('/target Instant')
    swg_utils.chat('/ui action radialMenu', return_delay=3)
    swg_utils.press('1', return_delay=4)
    click_on_travel_button(return_delay=14)
    
    
def open_ship_details_window():
    select_button_idx = None
    while select_button_idx is None:
        # Click to open the Starship Terminal
        swg_utils.click(return_delay=4)
        select_button_arr = np.array(file_utils.read_csv(os.path.join('land_ui_dir', 'Select.csv'))).astype(np.int)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                    sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        # Will use the first ship.
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=True)
        if select_button_idx is None:
            # Someone is in the way.
            time.sleep(5)
    # Click on Select button
    swg_utils.click(button='left', start_delay=0, return_delay=4, interval_delay=0, window=None, region=region, coords_idx=select_button_idx)
    
    
def space_travel():
    open_ship_details_window()
    click_on_travel_button(return_delay=3)
    # Find Corellia and click on it
    corellia_arr = np.array(file_utils.read_csv(os.path.join('land_ui_dir', 'Corellia.csv'))).astype(np.int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    corellia_button_idx, _ = swg_utils.find_arr_on_region(corellia_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False)
    swg_utils.click(button='left', start_delay=0, return_delay=4, interval_delay=0, window=None, region=region, coords_idx=corellia_button_idx)
    # Find Guerfel and then click 10 rows up 30 cols right to select Doaba Guerfel
    guerfel_arr = np.array(file_utils.read_csv(os.path.join('land_ui_dir', 'Guerfel.csv'))).astype(np.int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    guerfel_idx, _ = swg_utils.find_arr_on_region(guerfel_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False)
    guerfel_button_idx = [guerfel_idx[0] - 10, guerfel_idx[1] + 30]
    swg_utils.click(button='left', start_delay=0, return_delay=4, interval_delay=0, window=None, region=region, coords_idx=guerfel_button_idx)
    # Travel button is 530 rows down and 100 cols to the right of guerfel button
    travel_button_idx = [guerfel_button_idx[0] + 530, guerfel_button_idx[1] + 100]
    swg_utils.click(button='left', start_delay=0, return_delay=14, interval_delay=0, window=None, region=region, coords_idx=travel_button_idx)
    
def sell_to_chassis_dealer():
    # Click on chassis dealer
    swg_utils.click(return_delay=4)
    swg_utils.chat('/ui action conversationResponse0', start_delay=0, return_delay=5)
    select_button_arr = np.array(file_utils.read_csv(os.path.join('land_ui_dir', 'Select.csv'))).astype(np.int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False)
    while select_button_idx is not None:
        # Press and hold enter to sell quickly.
        pdi.keyDown('enter')
        time.sleep(10)
        pdi.keyUp('enter')
        time.sleep(3)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=0, start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=True)
        # The "select" on the SELL LOOT window will disappear once all loot has been sold.

def launch_ship():
    open_ship_details_window()
    # Find travel button to click on Launch Ship button
    travel_button_arr = np.array(file_utils.read_csv(os.path.join('land_ui_dir', 'Travel.csv'))).astype(np.int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    # Assume Travel button is in the bottom half of the screen.
    travel_button_idx, _ = swg_utils.find_arr_on_region(travel_button_arr, img_arr=img_arr, iterate_row_then_col=True, start_row=int(img_arr.shape[0]/2), start_col=0, iterate_row_forwards=True, iterate_col_forwards=True, fail_gracefully=False)
    # Launch Ship button is 100 columns to the left of Travel button.
    launch_ship_idx = [travel_button_idx[0], travel_button_idx[1] - 100]
    swg_utils.click(button='left', start_delay=0, return_delay=14, interval_delay=0, window=None, region=region, coords_idx=launch_ship_idx)
    
    

def go_to_chassis_dealer():
    # Starting wp in house is -584, 1314
    waypoint_csv_path = os.path.join(git_path, 'likeCinnamon_house_to_chassis_dealer.csv')
    arrow_rect_csv_fpath = os.path.join(git_path, 'arrow_rect.csv')
    rwp.main(swg_window_idx, waypoint_csv_path, function_list=[instant_travel_vehicle, space_travel, sell_to_chassis_dealer, launch_ship], arrow_rect_csv_fpath=arrow_rect_csv_fpath, calibrate_to_north=True)


def main():
    go_to_chassis_dealer()
    #sell_to_chassis_dealer()
    #launch_ship()
    
    
if __name__ == '__main__':
    main()