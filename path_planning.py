# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 12:07:28 2021

@author: rosebud
"""
from config_utils import Instruct
import socket
config_fpath = 'swg_config_file_for_' + socket.gethostname() + '.conf'
config = Instruct(config_fpath)
config.get_config_dct()
import sys
python_utils_path = config.config_dct['main']['python_utils_path']
planning_mode = False#config.get_value('main', 'planning_mode', desired_type=bool, required_to_be_in_conf=False, default_value=True)
sys.path.append(r"" + python_utils_path)
from python_utils import file_utils

import numpy as np

# import keyboard
import pynput as pnp
import get_land_coords as glc
import waypoint_path as wpp
import os
import swg_window_management as swm


def empty_function():
    pass


class Waypoint_manager:
    def __init__(self):
        self.file_name = 'undefined_path'
        self.waypoint_list = []
        self.current_waypoint = []
        self.wait_time = 0
        self.index = -1
        self.planning_mode = planning_mode
    
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
    '''
    input parameters:
    waypoint_manager: Waypoint_manager
        contains all the parameters required for making a waypoint path
        
    returns: none
    
    purpose: prompts user for name of file to be created. file type will be a csv
    this file stores all the waypoint path information (waypoint_list)
    after this, it will start listening for hotkeys
    
    notes:
    file will be stored in the same path as path_planning.py
    '''
    # ask user for file_name
    waypoint_manager.file_name = input("Enter file_name to create: ") + '.csv'
    
    # begin editing
    path_plan(waypoint_manager)
    
    
def edit_file(waypoint_manager):
    '''
    returns: none
    
    purpose: prompts the user for a name of file to be editted. reads in an existing waypoint_list
    after this, it will start listening for hotkeys
    
    notes:
    none
    '''
    # ask user for file_name
    waypoint_manager.file_name = input("Enter file_name to edit: ") + ".csv"    
    # waypoint_manager.waypoint_list = file_utils.read_csv(waypoint_manager.file_name)
    waypoint_manager.waypoint_list = list(map(list,np.array(file_utils.read_csv(waypoint_manager.file_name)).astype(np.int)))
    print('waypoint_list: ', waypoint_manager.waypoint_list)
    # print('index: ', waypoint_manager.index)
    # begin editing
    path_plan(waypoint_manager)
    

def delete_file(waypoint_manager):
    '''
    returns: none
    
    purpose: prompts the user for a name of file to be deleted. deletes an existing waypoint_list
    
    notes:
    none
    '''
    # ask user for file_name
    waypoint_manager.file_name = input("Enter file_name to delete: ") + ".csv"
    
    # delete this csv
    if os.path.exists(waypoint_manager.file_name):
      os.remove(waypoint_manager.file_name)
    else:
      print("file name does not exist")
      

def insert_waypoint(waypoint_manager):
    '''
    returns: none
    
    purpose: inserts a new waypoint AFTER the current waypoint. if it is a new list, it will be the first waypoint.
    
    notes:
    none
    '''    
    current_waypoint = glc.get_land_coords(swg_window)
    # Initialize wait time and function index to 0 by default.
    current_waypoint += [0, 0]
    waypoint_manager.index += 1
    waypoint_manager.waypoint_list.insert(waypoint_manager.index, current_waypoint)
    print('inserted waypoint: ', waypoint_manager.waypoint_list[min([waypoint_manager.index, len(waypoint_manager.waypoint_list) - 1])])
    
    # print('current waypoint: ', current_waypoint)
    # print('waypoint list: ', waypoint_manager.waypoint_list)
    # print('index: ', waypoint_manager.index)
    

def delete_waypoint(waypoint_manager):
    '''
    returns: none
    
    purpose: deletes current waypoint from waypoint_list
    
    notes:
    none
    '''    
    print('deleted waypoint: ',waypoint_manager.waypoint_list[waypoint_manager.index])
    del waypoint_manager.waypoint_list[waypoint_manager.index]
    
    
def run_waypoint_list_forward(waypoint_manager):
    '''
    returns: none
    
    purpose: runs all waypoints in waypoint_list from beginning of list
    
    notes:
    none
    '''  
    print('file_name: ',waypoint_manager.file_name)
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    wpp.move_along(swg_window, waypoint_manager.waypoint_list, planning_mode=waypoint_manager.planning_mode, function_list=[empty_function] * 500)
    
    
def run_waypoint_list_backward(waypoint_manager):
    '''
    returns: none
    
    purpose: runs all waypoints in waypoint_list from the end of the list to the beginning
    
    notes:
    none
    ''' 
    print('file_name: ',waypoint_manager.file_name)
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    wpp.move_along(swg_window, waypoint_manager.waypoint_list[::-1], planning_mode=waypoint_manager.planning_mode, function_list=[empty_function] * 500)


def step_next_waypoint(waypoint_manager):
    '''
    returns: none
    
    purpose: increment index by one and go to that waypoint.
    
    notes:
    assumes you are still at the previous waypoint
    assumes you are still oriented north
    ''' 
    if(waypoint_manager.index + 1 < len(waypoint_manager.waypoint_list)):
        waypoint_manager.index += 1
        print('moving to waypoint: ',waypoint_manager.waypoint_list[waypoint_manager.index])
        wpp.move_along(swg_window, [waypoint_manager.waypoint_list[waypoint_manager.index]], planning_mode=waypoint_manager.planning_mode, function_list=[empty_function] * 500)
    
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    
    
def step_previous_waypoint(waypoint_manager):
    '''
    returns: none
    
    purpose: increment index by one and go to that waypoint.
    
    notes:
    assumes you are still at the previous waypoint
    assumes you are still oriented north
    ''' 
    waypoint_manager.index -= 1
    print('current waypoint: ',waypoint_manager.waypoint_list[waypoint_manager.index])
    # check if index was already 0
    if(waypoint_manager.index < 0):
        waypoint_manager.index = 0
    else:
        print('moving to waypoint: ',waypoint_manager.waypoint_list[waypoint_manager.index])
        wpp.move_along(swg_window, [waypoint_manager.waypoint_list[waypoint_manager.index]], planning_mode=waypoint_manager.planning_mode, function_list=[empty_function] * 500)
        return
    
    print('waypoint list: ', waypoint_manager.waypoint_list)
    print('index: ', waypoint_manager.index)
    

def stop_listening(waypoint_manager):
    '''
    returns: none
    
    purpose: stops listening to keyboard inputs
    
    notes:
    none
    ''' 
    print('file_name: ',waypoint_manager.file_name)
    sys.exit()


def add_wait_to_current_waypoint(waypoint_manager): 
    '''
    returns: none
    
    purpose: adds wait time to current waypoint. takes effect after travelling to waypoint
    adds wait time in increments of 1 second
    
    notes:
    must have at least 1 waypoint in list before using this function
    ''' 
    waypoint_manager.waypoint_list[waypoint_manager.index][2] += 1
    print('current waypoint after adding wait: ',waypoint_manager.waypoint_list[waypoint_manager.index])


def subtract_wait_from_current_waypoint(waypoint_manager):
    '''
    returns: none
    
    purpose: subtracts wait time from current waypoint. takes effect after travelling to waypoint
    removes wait time in increments of 1 second
    will not go negative
    
    notes:
    must have at least 1 waypoint in list before using this function
    ''' 
    waypoint_manager.waypoint_list[waypoint_manager.index][2] = max(waypoint_manager.waypoint_list[waypoint_manager.index][2] - 1, 0)
    print('current waypoint after subtracting wait: ',waypoint_manager.waypoint_list[waypoint_manager.index])
    
    
def set_function_index(waypoint_manager):
    '''
    Returns
    -------
    None
    
    Purpose
    -------
    Input a integer corresponding to the index in function_list of the
    function to run once you arrive at this waypoint. function_list is a
    parameter in wpp.move_along.
    
    notes:
    must have at least 1 waypoint in list before using this function
    ''' 
    print('waypoint_manager.waypoint_list', waypoint_manager.waypoint_list)
    waypoint_manager.waypoint_list[waypoint_manager.index][3] = int(input('Enter the index of the function_list specifying the function to execute at this waypoint: '))
    print('current waypoint after adding function index: ',waypoint_manager.waypoint_list[waypoint_manager.index])


def on_press(key):
    '''
    input parameters:
    key:
        for function keys: enum 'Key'
        for letter keys: pynput.keyboard._win32.KeyCode
        
    returns: none
    
    purpose:
    
    notes:
    see pynput documentation for more on key
    ''' 
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
    #hotekey 12: Set the function index
    if name == 'f12': 
        set_function_index(waypoint_manager)
  
    
def path_plan(waypoint_manager):
    '''
    returns: none
    
    purpose: starts listening for hotkey commands
    
    notes:
    none
    ''' 
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
    hotkey 12: set function index
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