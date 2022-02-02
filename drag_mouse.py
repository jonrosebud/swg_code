# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 10:29:38 2021

@author: trose
"""
import time
import pyautogui as pag
import numpy as np
import sys
sys.path.append(r'C:\Users\trose\Documents\python_packages')
from python_utils import file_utils
os = file_utils.os


def drag_mouse(autoit_dir='.', start_coords=None, end_coords=None, num_drags=None, delay_start=0.3, delay_return=0.05):
    '''
    Parameters
    ----------
    autoit_dir: str
        Path of directory that contains drag_mouse.exe autoit script.
    
    start_coords: list of int or None
        [x, y] coordinates on the monitor where the object to be dragged is.
        If None, the user will be prompted to provide the coordinates by hovering
        the mouse over the start location.
        
    end_coords: list of int
        [x. y] coordinate on the monitor where the object will be dragged to.
        If None, the user will be prompted to provide the coordinates by hovering
        the mouse over the end location.
        
    num_drags: int
        Number of times to drag an object from start_x, start_y to end_x, end_y

    delay_start: float
        Amount of time to sleep before beginning each drag.
        
    delay_return: float
        Amount of time to sleep before returning from this function.
        
    Returns
    -------
    None.
    
    Purpose
    -------
    Use autoit to drag and drop from one screen location to another num_drags
    number of times. Useful for things like swg where once you drag an item,
    another item takes its place.
    '''
    drag_mouse_fpath = os.path.join(autoit_dir, 'drag_mouse.exe')
    if not os.path.exists(drag_mouse_fpath):
        raise FileNotFoundError(
                'drag_mouse.exe not found in autoit_dir which was: "' + autoit_dir + '"')
                
    if start_coords is None:
        input('Hover your mouse over the desired start location, press enter, and dont move the mouse for half a second.')
        start_x, start_y = pag.position()
        print('start_x:', start_x, 'start_y:', start_y)
    else:
        start_x, start_y = start_coords
    if end_coords is None:
        input('Hover your mouse over the desired end location, press enter, and dont move the mouse for half a second.')
        end_x, end_y = pag.position()
        print('end_x:', end_x, 'end_y:', end_y)
    else:
        end_x, end_y = end_coords
    if num_drags is None:
        num_drags = int(input('Input the number of times to drag/drop: '))
    file_utils.write_rows_to_csv(os.path.join(autoit_dir, 'drag_coords.csv'), 
            [[start_x, start_y], [end_x, end_y]])
    
    for _ in range(num_drags):
        time.sleep(delay_start)
        os.system(drag_mouse_fpath)
    time.sleep(delay_return)
    

def main():
    autoit_dir=r'D:\autoit\swg\REing'
    start_x = 2653
    start_y = 80
    end_x = 2960
    end_y = 373
    num_drags = 15
    drag_mouse(autoit_dir=autoit_dir, start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, num_drags=num_drags)
    
    
if __name__ == '__main__':
    #main()
    drag_mouse(autoit_dir=r'D:\autoit\swg\REing')
    