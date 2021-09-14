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
from python_utils import file_utils
import time
import numpy as np
import pydirectinput as pdi
import get_land_coords as glc
import waypoint_path as wpp
import swg_window_management as swm
from destroy_junk import press_destroy
import random


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
        if random.random() < 0.5:
            pdi.press('2')
            time.sleep(0.05)
        pdi.press('1')
        time.sleep(0.05)
        pdi.press('4')
        time.sleep(0.05)
        pdi.press('5')
        time.sleep(0.05)
        pdi.press('6')
        time.sleep(0.05)
        pdi.press('7')
        time.sleep(0.05)
        pdi.press('9')
        time.sleep(0.05)
        pdi.press('-')
        time.sleep(0.05)
        pdi.press('0')
        time.sleep(0.05)
        if random.random() < 0.3:
            pdi.press('8')
            time.sleep(0.05)
        time.sleep(1)
        

def destroy_for_all_windows():
    num_items_to_destroy = [7, 10, 19]
    item_to_destroy_coord_list = [[443, 537], [1411, 607], [2979, 734]]
    for i in range(len(swm.swg_windows)):
        swm.swg_windows[i].set_focus()
        time.sleep(0.5)
        for _ in range(10):
            pdi.press('esc', presses=2)
            pdi.press('i')
            time.sleep(0.5)
            press_destroy(item_to_destroy_coord_list[i], spin=(i != 2))


def main():
    time.sleep(1)
    swg_window = swm.swg_windows[2]
    swg_window.set_focus()
    waypoint_list = list(map(list, np.array(file_utils.read_csv('aclo.csv')).astype(np.int)))
    glc.north_calibrate(swg_window, arrow_rect_csv_fpath='arrow_rect.csv')
    for _ in range(1):
        wpp.move_along(swg_window, waypoint_list, function_list=[empty_function, attack, destroy_for_all_windows])
    
    
if __name__ == '__main__':
    main()