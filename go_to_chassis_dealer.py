# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 20:30:53 2021

@author: trose
"""
from config_utils import Instruct
import socket, os
config_fpath = os.path.join('..', 'swg_config_file_for_' + socket.gethostname() + '.conf')
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
import pydirectinput_tmr as pdi
import swg_window_management as swm
import swg_utils
import time, random
import get_land_coords as gtc


def find_travel_button():
    swg_utils.moveTo(coords=[region['width'] + region['left'] - 30, region['top'] + region['height'] - 30], return_delay=0.2)
    travel_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Travel.csv'), dtype=int)
    img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    # Assume Travel button is in the bottom half of the screen.
    travel_button_idx, _ = swg_utils.find_arr_on_region(travel_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), start_col=0, fail_gracefully=False)
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
    # Open inventory
    pdi.press('i', return_delay=1.5)
    swg_utils.chat('/tar Instant', return_delay=1.5)
    # Click to open the itv window
    swg_utils.chat('/ui action defaultAction', return_delay=6)
    # Close inventory
    pdi.press('i')
    time.sleep(1.5)
    # Double click on Doaba Guerfel Starport to travel there.
    try:
        travel_button_idx = find_travel_button()
    except:
        # Sometimes the toolbar or chat window is covering up the travel button. Click
        # in the middle of the screen which should either activate the travel window or 
        # it will click on the ITV which will activate the travel window.
        swg_utils.click(coords_idx=[region['top'] + int(region['height'] / 2), region['left'] + int(region['width'] / 2)], region=region, window=swg_window, return_delay=0.3)
    travel_button_idx = find_travel_button()
    starport_idx = [travel_button_idx[0] - 534, travel_button_idx[1] - 58]
    swg_utils.click(button='left', presses=2, start_delay=0, return_delay=14, interval_delay=0, window=None, region=region, coords_idx=starport_idx)
    
    
def instant_travel_vehicle_default_starport():
    # Switch to toolbar pane with itv command on it.
    swg_utils.press(['ctrl', '2'], return_delay=0.2)
    # Press the itv command
    swg_utils.press(['1'], return_delay=1)
    # Open inventory
    pdi.press('i', return_delay=1.5)
    swg_utils.chat('/tar Instant', return_delay=1.5)
    # Click to open the itv window
    swg_utils.chat('/ui action defaultAction', return_delay=4)
    # Close inventory
    pdi.press('i')
    time.sleep(1.5)
    try:
        travel_button_idx = find_travel_button()
    except:
        # Sometimes the toolbar or chat window is covering up the travel button. Click
        # in the middle of the screen which should either activate the travel window or 
        # it will click on the ITV which will activate the travel window.
        swg_utils.click(coords_idx=[region['top'] + int(region['height'] / 2), region['left'] + int(region['width'] / 2)], region=region, window=swg_window)
    swg_utils.click(button='left', presses=1, start_delay=0, return_delay=14, interval_delay=0, window=None, region=region, coords_idx=travel_button_idx)
    
    
def open_ship_details_window():
    select_button_idx = None
    while select_button_idx is None:
        # Click to open the Starship Terminal
        swg_utils.click(return_delay=4)
        select_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Select.csv'), dtype=int)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                    sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        # Assume Select button is in the bottom half of the screen.
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), start_col=0, fail_gracefully=True)
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
    
    
def open_ship_details_window_starship_terminal():
    select_button_idx = None
    while select_button_idx is None:
        # Close all windows
        pdi.press('esc', presses=8)
        # Open inventory so cursor not on player or something
        pdi.press('i')
        # Open the Starship Terminal
        swg_utils.chat('/tar starship', return_delay=0.2)
        swg_utils.chat('/ui action defaultAction', return_delay=3)
        select_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Select.csv'), dtype=int)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                    sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        # Assume Select button is in the bottom half of the screen.
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), start_col=0, fail_gracefully=True)
        if select_button_idx is None:
            # Someone is in the way.
            time.sleep(5)
    # Click on Select button
    swg_utils.click(button='left', start_delay=0, return_delay=4, interval_delay=0, window=None, region=region, coords_idx=select_button_idx)
    
    
def space_travel_to_doaba_guerfel():
    open_ship_details_window_starship_terminal()
    _ = click_on_travel_button(return_delay=3)
    travel_button_idx = find_travel_button()
    corellia_idx = [travel_button_idx[0] - 422, travel_button_idx[1] - 131]
    swg_utils.click(button='left', start_delay=0, return_delay=1.5, interval_delay=0, window=None, region=region, coords_idx=corellia_idx)
    doaba_guerfel_idx = [travel_button_idx[0] - 534, travel_button_idx[1] - 58]
    swg_utils.click(button='left', start_delay=0, return_delay=1.5, interval_delay=0, window=None, region=region, coords_idx=doaba_guerfel_idx)
    _ = click_on_travel_button(travel_button_idx=travel_button_idx, return_delay=14)
    
    
def move_away_from_player():
    waypoint_csv_path = os.path.join(git_path, 'tmp_waypoint.csv')
    # Get current coordinates
    starting_coords = [rwp.glc.get_land_coords(region)]
    file_utils.write_rows_to_csv(waypoint_csv_path, starting_coords)
    meters_m_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'meters_m.csv'), dtype=int)
    # Check to see if player is right on top of you. If so, the macro wont work.
    found_idx = [0,0]
    while found_idx is not None:
        pdi.press('esc')
        swg_utils.click(return_delay=0.2)
        found_idx, _ = swg_utils.find_arr_on_region(meters_m_arr, region=region, img_arr=None, start_row=20, start_col=0, end_row=150, end_col=400, fail_gracefully=True, sharpen_threshold=255)
        if found_idx is not None:
            rand_number = random.random()
            if rand_number < 1/8:
                swg_utils.press('w', key_down_delay=0.1)
            elif rand_number < 2/8:
                swg_utils.press('s', key_down_delay=0.1)
            elif rand_number < 3/8:
                swg_utils.press('q', key_down_delay=0.1)
            elif rand_number < 4/8:
                swg_utils.press('e', key_down_delay=0.1)
            else:
                rwp.main(swg_window_i, waypoint_csv_path=waypoint_csv_path, function_list=[empty_function], calibrate_to_north=False)
    

def chassis_dealer_macro(macro_name):
    # 21 rows to get to next sellable item in the list
    #next_item_offset = np.array([21, 0])
    for i in range(4):
        if i == 0:
            swg_utils.chat('/macro ' + macro_name)
        else:
            if i == 1:
                swg_utils.click(region=region, coords_idx=[region['top'] + region['height'] - 1, chatbar_idx[1]], activate_window=False)
            swg_utils.chat('/macro ' + macro_name, chatbar_idx=chatbar_idx, region=region)
        time.sleep(2)
        select_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Select.csv'), dtype=int)
        img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                    sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
        
        select_button_idx, _ = swg_utils.find_arr_on_region(select_button_arr, img_arr=img_arr, start_row=0, start_col=0, fail_gracefully=True)
        if select_button_idx is None:
            pdi.press('esc', presses=8)
            pdi.press('i')
            return False
        # Find and click on first sellable item to get the first item activated. Then can hold down enter to sell all.
        open_square_bracket_arr = swg_utils.get_search_arr('open_square_bracket', dir_path=os.path.join(git_path, 'inventory_dir'), mask_int=None)
        sellable_item_idx, _ = swg_utils.find_arr_on_region(open_square_bracket_arr, img_arr=img_arr, start_row=select_button_idx[0], start_col=select_button_idx[1], end_row=None, end_col=select_button_idx[1], fail_gracefully=False)
        #sellable_item_idx += i * next_item_offset
        # Click on sellable item
        swg_utils.click(presses=1, return_delay=1, coords_idx=sellable_item_idx, activate_window=False, region=region, window=swg_window)
    pdi.press('i')
    pdi.press('i')
    # Press and hold enter to sell quickly.
    pdi.keyDown('enter')
    time.sleep(20)
    pdi.keyUp('enter')
    time.sleep(2)
    # If no more items, the window will not re-appear
    pdi.press('esc', presses=8)
    pdi.press('i')
    return True
    
    
def sell_to_chassis_dealer():
    chassis_dealer_wp = rwp.glc.get_land_coords(region)
    # Open inventory so you dont accidentally have your cursor on another player which will cause the macro to fail.
    pdi.press('i')
    if np.sqrt((37 - chassis_dealer_wp[0])**2 + (37 - chassis_dealer_wp[1])**2) < 30:
        macro_name = 'FenChassisDealer'
    else:
        macro_name = 'chassisDealer'
    while chassis_dealer_macro(macro_name):
        pass
    # Close inventory
    pdi.press('esc', presses=8)
    

def launch_ship():
    open_ship_details_window()
    # Find travel button to click on Launch Ship button
    travel_button_arr = file_utils.read_csv(os.path.join(git_path, 'land_ui_dir', 'Travel.csv'), dtype=int)
    img_arr = swg_utils.take_grayscale_screenshot(swg_window, region, 
                sharpen_threshold=197, scale_to=255, set_focus=False, sharpen=True)
    
    # Assume Travel button is in the bottom half of the screen.
    travel_button_idx, _ = swg_utils.find_arr_on_region(travel_button_arr, img_arr=img_arr, start_row=int(img_arr.shape[0]/2), start_col=0, fail_gracefully=False)
    # Launch Ship button is 100 columns to the left of Travel button.
    launch_ship_idx = [travel_button_idx[0], travel_button_idx[1] - 100]
    swg_utils.click(button='left', start_delay=0, return_delay=14, interval_delay=0, window=None, region=region, coords_idx=launch_ship_idx)
    
    
def empty_function():
    pass


def go_to_first_G9():
    dir_path = os.path.join(git_path, 'land_ui_dir')
    search_arr = swg_utils.get_search_arr('manage_locations_200', dir_path=dir_path)
    num_attempts = 30
    for i in range(num_attempts):
        # G9 should be the 0 button (toolbarSlot09)
        pdi.press('0')
        time.sleep(3)
        # Open invetory
        pdi.press('i')
        time.sleep(1.5)
        swg_utils.chat('/tar Instant', return_delay=1.5)
        swg_utils.chat('/ui action defaultAction', return_delay=4)
        # Close inventory
        pdi.press('i')
        time.sleep(1.5)
        manage_locations_idx, img_arr = swg_utils.find_arr_on_region(search_arr, region=region, img_arr=None, start_row=0, start_col=0, end_row=None, end_col=None, fail_gracefully=True, sharpen_threshold=200)
        if manage_locations_idx is None:
            swg_utils.stealth_on()
            time.sleep(3)
            pdi.keyDown('w')
            time.sleep(15)
            pdi.keyUp('w')
            direction = ['w','e'][random.randint(0,1)]
            pdi.keyDown(direction)
            time.sleep(random.random() * 20)
            pdi.keyUp(direction)
            swg_utils.stealth_off()
            time.sleep(0.2)
            continue
        pdi.press('up', presses=4, start_delay=4, return_delay=0.1)
        pdi.press('down', start_delay=0.1, return_delay=0.1)
        pdi.press('enter', return_delay=0)
        # If land coords do not disappear within 6 seconds then probably we are in combat which necessitates cloaking and running away.
        start_time = time.time()
        while time.time() - start_time < 6 and gtc.get_land_coords(region, fail_gracefully=True) is not None:
            time.sleep(0.5)
        if time.time() - start_time >= 6:
            swg_utils.stealth_on()
            time.sleep(3)
            pdi.keyDown('w')
            time.sleep(15)
            pdi.keyUp('w')
            direction = ['w','e'][random.randint(0,1)]
            pdi.keyDown(direction)
            time.sleep(random.random() * 20)
            pdi.keyUp(direction)
            swg_utils.stealth_off()
            time.sleep(0.2)
            continue
        else:
            time.sleep(max(0, 14 - (time.time() - start_time)))
            return
            
    raise Exception('Could not use G9 in', num_attempts, 'attempts.')
    
    
def go_to_second_G9():
    dir_path = os.path.join(git_path, 'land_ui_dir')
    search_arr = swg_utils.get_search_arr('manage_locations_200', dir_path=dir_path)
    num_attempts = 30
    for i in range(num_attempts):
        # G9 should be the 0 button (toolbarSlot09)
        pdi.press('0')
        time.sleep(3)
        # Open invetory
        pdi.press('i')
        time.sleep(1.5)
        swg_utils.chat('/tar Instant', return_delay=1.5)
        swg_utils.chat('/ui action defaultAction', return_delay=4)
        # Close inventory
        pdi.press('i')
        time.sleep(1.5)
        manage_locations_idx, img_arr = swg_utils.find_arr_on_region(search_arr, region=region, img_arr=None, start_row=0, start_col=0, end_row=None, end_col=None, fail_gracefully=True, sharpen_threshold=200)
        if manage_locations_idx is None:
            swg_utils.stealth_on()
            time.sleep(3)
            pdi.keyDown('w')
            time.sleep(15)
            pdi.keyUp('w')
            direction = ['w','e'][random.randint(0,1)]
            pdi.keyDown(direction)
            time.sleep(random.random() * 20)
            pdi.keyUp(direction)
            swg_utils.stealth_off()
            time.sleep(0.2)
            continue
        pdi.press('up', presses=4, start_delay=4, return_delay=0.1)
        pdi.press('down', presses=2, start_delay=0.1, return_delay=0.1)
        pdi.press('enter', return_delay=0)
        # If land coords do not disappear within 6 seconds then probably we are in combat which necessitates cloaking and running away.
        start_time = time.time()
        while time.time() - start_time < 6 and gtc.get_land_coords(region, fail_gracefully=True) is not None:
            time.sleep(0.5)
        if time.time() - start_time >= 6:
            swg_utils.stealth_on()
            time.sleep(3)
            pdi.keyDown('w')
            time.sleep(15)
            pdi.keyUp('w')
            direction = ['w','e'][random.randint(0,1)]
            pdi.keyDown(direction)
            time.sleep(random.random() * 20)
            pdi.keyUp(direction)
            swg_utils.stealth_off()
            time.sleep(0.2)
            continue
        else:
            time.sleep(max(0, 14 - (time.time() - start_time)))
            return
            
    raise Exception('Could not use G9 in', num_attempts, 'attempts.')


def go_to_chassis_dealer(calibrate_to_north=True, waypoint_csv_path=os.path.join(git_path, 'waypoint_paths', 'likeCinnamon_house_to_chassis_dealer.csv')):
    arrow_rect_csv_fpath = os.path.join(git_path, 'arrow_rect.csv')
    rwp.main(swg_window_i, waypoint_csv_path, function_list=[empty_function, instant_travel_vehicle, swg_utils.stealth_on, sell_to_chassis_dealer, space_travel, swg_utils.stealth_off, go_to_first_G9], arrow_rect_csv_fpath=arrow_rect_csv_fpath, calibrate_to_north=calibrate_to_north)


def main():
    swg_window.set_focus()
    time.sleep(0.5)
    go_to_chassis_dealer()
    
swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
swg_window = swm.swg_windows[swg_window_i]
region = swm.swg_window_regions[swg_window_i]
config.get_config_dct()
toon_name = swg_utils.get_toon_name(region)
chatbar_idx = config.config_dct[toon_name + '_sort_space_components']['chatbar_idx']
if __name__ == '__main__':
    main()