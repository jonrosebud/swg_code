# -*- coding: utf-8 -*-
"""
Created on Fri Jan 28 14:52:11 2022

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
import time
import numpy as np
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import swg_window_management as swm
import run_waypoint_path as rwp
import swg_utils
import pandas as pd
import pydirectinput_tmr as pdi
swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
swg_window = swm.swg_windows[swg_window_i]
swg_region = swm.swg_window_regions[swg_window_i]

# 2671504 initial iron
# 2470320 left at level 70
def manual():
    swg_window.set_focus()
    time.sleep(0.5)
    resource_idx = [135, 50]
    assemble_idx = [440, 578]
    while True:
        for toolbarSlot in range(10):
            pdi.press(str(toolbarSlot))
            time.sleep(1)
            pdi.press('=')
            time.sleep(1)
            for _ in range(3):
                swg_utils.click(presses=2, start_delay=0, return_delay=0.1, window=swg_window, region=swg_region, coords_idx=resource_idx, activate_window=False)
            swg_utils.click(presses=2, start_delay=1.2, return_delay=1.2, window=swg_window, region=swg_region, coords_idx=assemble_idx, activate_window=False)
            pdi.press('=')
            time.sleep(0.4)
            swg_utils.click(presses=1, start_delay=0, return_delay=0.1, window=swg_window, region=swg_region, coords_idx=resource_idx, activate_window=False)
            pdi.press('=')
            time.sleep(2.4)
            pdi.press('esc', presses=4)
        
        
def main():
    swg_window.set_focus()
    time.sleep(0.5)
    # Enter free-moving mouse mode
    pdi.press('alt')
    resource_idx = [135, 50]
    # Make it so only the window that requires double clicking resource has a part of it that goes to the upper left corner
    pixel_sum_region = {'left': swg_region['left'], 'top': swg_region['top'], 'width': 5, 'height': 5}
    img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=pixel_sum_region, set_focus=False, sharpen=False)
    # Be in a building so the pixels don't change in the upper left corner
    # Get initial pixel sum
    background_pixel_sum = img_arr.sum()
    # Start the grindCraft macro
    pdi.press('-')
    while True:
        # Make sure the header of the assemble item window is in the upper left corner so the sum is higher than the background.
        while img_arr.sum() <= background_pixel_sum:
            time.sleep(0.02)
            img_arr = swg_utils.take_grayscale_screenshot(window=swg_window, region=pixel_sum_region, set_focus=False, sharpen=False)
        time.sleep(0.05)
        swg_utils.click(presses=8, start_delay=0, return_delay=0, interval_delay=0.05, duration=0, window=swg_window, region=swg_region, coords_idx=resource_idx, activate_window=False)
    
    
if __name__ == '__main__':
    main()