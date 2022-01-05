# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 20:35:01 2021

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
import numpy as np
import get_land_coords as glc
import waypoint_path as wpp
swg_windows = glc.swm.swg_windows


def empty_function():
    pass


def main(swg_window_idx, waypoint_csv_path, num_loops=1, function_list=[], arrow_rect_csv_fpath='arrow_rect.csv', calibrate_to_north=True):
    '''
    Parameters
    ----------
    swg_window_idx: int
       Index of the list of swg_windows. See glc.swm docs.
       
    waypoint_csv_path: str
        File path of the csv file which as recorded waypoints. See wpp docs.
        
    num_loops: int
        Number of times to execute the waypoint path.
        
    function_list: list of functions
        List of functions such that their order in this list corresponds to the indices they are found in the waypoint_csv_path file given that empty_function will be prepended to function_list.
        
    arrow_rect_csv_fpath: str
        Path of the file that contains image data for the North arrow on the radar minimap.
        
    calibrate_to_north: bool
        True: run glc.north_calibrate
        False: skip north calibration.

    Returns
    -------
    None

    Purpose
    -------
    Run a previously recorded waypoint path possibly many times in a loop and optionally initially calibrate orientation to be facing North.
    '''
    swg_window = swg_windows[swg_window_idx]
    swg_window.set_focus()
    waypoint_list = list(map(list, np.array(file_utils.read_csv(waypoint_csv_path)).astype(np.int)))
    if calibrate_to_north:
        glc.north_calibrate(swg_window, arrow_rect_csv_fpath=arrow_rect_csv_fpath)
    function_list = [empty_function] + function_list
    for _ in range(num_loops):
        wpp.move_along(swg_window, waypoint_list, function_list=function_list)