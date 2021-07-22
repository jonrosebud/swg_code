# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 12:07:28 2021

@author: rosebud
"""
from configparser import ConfigParser
config = ConfigParser()
import socket
config_file_name = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config.read(config_file_name)
import sys
python_utils_path = config.get('main', 'python_utils_path')
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils

import numpy as np

# import keyboard
import pynput as pnp
import get_land_coords as glc
import waypoint_path as wpp
import os
import swg_window_management as swm


class Waypoint_manager:
    def __init__(self):
        self.file_name = 'undefined_path'
        self.waypoint_list = []
        self.current_waypoint = []
        self.wait_time = 0
        self.index = 0
    
waypoint_manager = Waypoint_manager()

swm.calibrate_window_position(swm.swg_windows)
swg_window = swm.swg_windows[2]
# glc.north_calibrate(swg_window, arrow_rect_csv_fpath='arrow_rect.csv')


def selection(waypoint_manager):
    # ask user for what they would like to do
    option = input("Enter 1 for create_file, 2 for edit_file, or 3 for delete_file: ")
    
    if option == '1':
        # create_file (then edit)
        create_file(waypoint_manager)
    elif option == '2':
        # edit_file
        edit_file(waypoint_manager)
    elif option == '3':
        # delete_file
        delete_file(waypoint_manager)
    else:
        print('invalid response')
        return
    

def create_file(waypoint_manager):
    # ask user for file_name
    waypoint_manager.file_name = input("Enter file_name to create: ")
    
    # begin editing
    path_plan(waypoint_manager)
    
    
def edit_file(waypoint_manager):
    # ask user for file_name
    waypoint_manager.file_name = input("Enter file_name to edit: ")    
    # waypoint_manager.waypoint_list = file_utils.read_csv(waypoint_manager.file_name)
    waypoint_manager.waypoint_list = list(map(list,np.array(file_utils.read_csv(waypoint_manager.file_name)).astype(np.int)))
    print('waypoint_list: ', waypoint_manager.waypoint_list)
    # print('index: ', waypoint_manager.index)
    # begin editing
    path_plan(waypoint_manager)
    

def delete_file(waypoint_manager):
    # ask user for file_name
    waypoint_manager.file_name = input("Enter file_name to delete: ")
    
    # delete this csv
    if os.path.exists(waypoint_manager.file_name):
      os.remove(waypoint_manager.file_name)
    else:
      print("file name does not exist")
      

def insert_waypoint(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    current_waypoint = glc.get_land_coords(swg_window)
    waypoint_manager.waypoint_list.insert(waypoint_manager.index + 1, current_waypoint)
    
    # print('current waypoint: ', current_waypoint)
    # print('waypoint list: ', waypoint_manager.waypoint_list)
    # print('index: ', waypoint_manager.index)
    

def delete_waypoint(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    del waypoint_manager.waypoint_list[waypoint_manager.index]
    
    
def run_waypoint_list_forward(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    wpp.move_along(swg_window, waypoint_manager.waypoint_list)
    
    
def run_waypoint_list_backward(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    wpp.move_along(swg_window, waypoint_manager.waypoint_list[::-1])


def step_next_waypoint(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    if(waypoint_manager.index + 1 < len(waypoint_manager.waypoint_list)):
        waypoint_manager.index += 1
        wpp.move_along(swg_window, [waypoint_manager.waypoint_list[waypoint_manager.index]])
    
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    
    
def step_previous_waypoint(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    waypoint_manager.index -= 1
    # check if index was already 0
    if(waypoint_manager.index < 0):
        waypoint_manager.index = 0
    else:
        wpp.move_along(swg_window, [waypoint_manager.waypoint_list[waypoint_manager.index]])
        return
    
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    

def stop_listening(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    sys.exit()


def add_wait_to_current_waypoint(waypoint_manager):    
    print('file_name: ',waypoint_manager.file_name)
    waypoint_manager.waypoint_list[waypoint_manager.index][2] += 15


def subtract_wait_from_current_waypoint(waypoint_manager):
    print('file_name: ',waypoint_manager.file_name)
    waypoint_manager.waypoint_list[waypoint_manager.index][2] = max(waypoint_manager.waypoint_list[waypoint_manager.index][2] - 15, 0)


def on_press(key):
    if hasattr(key, 'name'):
        name = key.name
    else:
        name = key.char
    #hotkey 1: insert current waypoint
    if name == 'f1':
        print('f1 pressed')
        insert_waypoint(waypoint_manager)
    #hotkey 2: delete current waypoint
    if name == 'f2':
        print('f2 pressed')
        delete_waypoint(waypoint_manager)
    #hotkey 3: run waypoint list from beginning
    if name == 'f3':
        print('f3 pressed')
        run_waypoint_list_forward(waypoint_manager)
    #hotkey 4: run waypoint list backwards from end
    if name == 'f4':
        print('f4 pressed')
        run_waypoint_list_backward(waypoint_manager)
    #hotkey 5: step once to next waypoint
    if name == 'f5':
        print('f5 pressed')
        step_next_waypoint(waypoint_manager)
    #hotkey 6: step once back to previous waypoint
    if name == 'f6':
        print('f6 pressed')
        step_previous_waypoint(waypoint_manager)
    #hotkey 7: stop path planning
    if name == 'f7':
        print('f7 pressed')
        print(waypoint_manager.file_name)
        print(waypoint_manager.waypoint_list)
        file_utils.write_rows_to_csv(waypoint_manager.file_name, waypoint_manager.waypoint_list)
        stop_listening(waypoint_manager)
        return
    #hotkey 8: step once back to previous waypoint
    if name == 'f8':
        print('f8 pressed')
        edit_file(waypoint_manager)
    #hotkey 10: step once back to previous waypoint
    if name == 'f10':
        print('f10 pressed')
        add_wait_to_current_waypoint(waypoint_manager)
    #hotkey 11: step once back to previous waypoint
    if name == 'f11':
        print('f11 pressed')
        subtract_wait_from_current_waypoint(waypoint_manager)
  
    
def path_plan(waypoint_manager):
    # print hotkey list
    print(            
    '''
    hotkey list:
    hotkey 1: insert current waypoint
    hotkey 2: delete current waypoint
    hotkey 3: run waypoint list from beginning
    hotkey 4: run waypoint list backwards from end
    hotkey 5: step once to next waypoint
    hotkey 6: step once back to previous waypoint
    hotkey 7: stop path planning
    hotkey 8: select new list
    hotkey 10: add step wait
    hotkey 11: subtract step wait
    '''
        )
    
    # listen for a hotkey
    with pnp.keyboard.Listener(on_press=on_press, on_release=None) as listener:
        listener.join()
        
        
def main():
    selection(waypoint_manager)
    print(waypoint_manager.file_name)
    
    
if __name__ == '__main__':
    main()