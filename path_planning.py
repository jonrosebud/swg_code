# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 12:07:28 2021

@author: rosebud
"""
import keyboard
import pynput as pnp

class Hi:
    def __init__(self):
        self.path_name = 'undefined_path'
    
yay = Hi()


def selection(yay):
    # ask user for what they would like to do
    option = input("Enter 1 for create_path, 2 for edit_path, or 3 for delete_path: ")
    
    if option == '1':
        # create_path (then edit)
        create_path(yay)
    elif option == '2':
        # edit_path
        edit_path()
    elif option == '3':
        # delete_path
        delete_path()
    else:
        print('invalid response')
        return
    

def create_path(yay):
    # ask user for path_name
    yay.path_name = input("Enter path_name to create: ")

    # begin editing
    path_plan(yay)
    
    
def edit_path(yay):
    # ask user for path_name
    yay.path_name = input("Enter path_name to edit: ")    
    
    # begin editing
    path_plan(yay)
    

def delete_path(yay):
    # ask user for path_name
    yay.path_name = input("Enter path_name to delete: ")


def insert_waypoint(yay):
    print('path_name: ',yay.path_name)
    

def delete_waypoint(yay):
    print('path_name: ',yay.path_name)
    
    
def run_waypoint_list_forward(yay):
    print('path_name: ',yay.path_name)
 
    
def run_waypoint_list_backward(yay):
    print('path_name: ',yay.path_name)
    
    
def step_next_waypoint(yay):
    print('path_name: ',yay.path_name)    
    
    
def step_previous_waypoint(yay):
    print('path_name: ',yay.path_name)    


def stop_listening(yay):
    print('path_name: ',yay.path_name)
    return
    
    
def on_press(key):
    try:
        name = key.name
        #hotkey 1: insert current waypoint
        if name == 'f1':
            print('f1 pressed')
            insert_waypoint(yay)
        #hotkey 2: delete current waypoint
        if name == 'f2':
            print('f2 pressed')
            delete_waypoint(yay)
        #hotkey 3: run waypoint list from beginning
        if name == 'f3':
            print('f3 pressed')
            run_waypoint_list_forward(yay)
        #hotkey 4: run waypoint list backwards from end
        if name == 'f4':
            print('f4 pressed')
            run_waypoint_list_backward(yay)
        #hotkey 5: step once to next waypoint
        if name == 'f5':
            print('f5 pressed')
            step_next_waypoint(yay)
        #hotkey 6: step once back to previous waypoint
        if name == 'f6':
            print('f6 pressed')
            step_previous_waypoint(yay)
        #hotkey 7: stop path planning
        if name == 'f7':
            print('f7 pressed')
            stop_listening(yay)
    except:
        name = key.char
        if name == 'a':
            pass
        if name == 'b':
            pass
  
    
def path_plan(yay):
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
    '''
        )
    
    # listen for a hotkey
    with pnp.keyboard.Listener(on_press=on_press, on_release=None) as listener:
        listener.join()
        
        
def main():
    selection(yay)
    print(yay.path_name)
    
    
if __name__ == '__main__':
    main()