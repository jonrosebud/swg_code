# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 13:42:59 2022

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
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import pydirectinput_tmr as pdi
import swg_window_management as swm
import run_waypoint_path as rwp
import swg_utils
import pandas as pd
os = file_utils.os
import random
import sort_space_components as ssc


class SWG:
    def __init__(self, swg_window_i=0):
        self.swg_window = swm.swg_windows[swg_window_i]
        self.swg_region = swm.swg_window_regions[swg_window_i]
        # SETUP
        swm.calibrate_window_position(swm.swg_windows)
        self.swg_window.set_focus()
        time.sleep(0.5)
        

class Space(SWG):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir')):
        super(Space, self).__init__(swg_window_i=swg_window_i)
        self.dir_path = dir_path
        self.target_closest_enemy_hotkey = target_closest_enemy_hotkey
        self.space_target_distance_digits = {digit: swg_utils.get_search_arr('space_target_distance_digit_' + str(digit), dir_path=self.dir_path, mask_int=0) for digit in range(10)}
        # INITIAL VALUES
        self.target_dist_idx = None
        
        
    def get_target_dist(self, fail_gracefully=False):
        if self.target_dist_idx is None:
            target_dist_right_arr = swg_utils.get_search_arr('target_dist_right_parenthesis', dir_path=self.dir_path, mask_int=0)
            target_right_parenthesis_idx, img_arr = swg_utils.find_arr_on_region(target_dist_right_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=255)
            target_dist_left_arr = swg_utils.get_search_arr('target_dist_left_parenthesis', dir_path=self.dir_path, mask_int=0)
            target_left_parenthesis_idx, img_arr = swg_utils.find_arr_on_region(target_dist_left_arr, region=self.swg_region, start_row=target_right_parenthesis_idx[0], start_col=target_right_parenthesis_idx[1] - 100, end_row=target_right_parenthesis_idx[0], end_col=target_right_parenthesis_idx[1], fail_gracefully=False, sharpen_threshold=255)
            self.target_dist_idx = [target_left_parenthesis_idx[0], target_left_parenthesis_idx[1] + target_dist_left_arr.shape[1] + 1]
        line_region = {'left': self.swg_region['left'] + self.target_dist_idx[1], 'top': self.swg_region['top'] + self.target_dist_idx[0], 'width': 6 * 6, 'height': 7}
        line_arr = swg_utils.take_grayscale_screenshot(window=swm.swg_windows[0], region=line_region, sharpen_threshold=255,
                scale_to=255, set_focus=False, sharpen=True)
        
        return swg_utils.get_int_from_line_arr(line_arr, self.space_target_distance_digits, fail_gracefully=fail_gracefully)
        

class Turret(Space):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
        super(Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path)
        self.max_movements = max_movements
        self.num_none_target_max = num_none_target_max
        # INITIAL VALUES
        self.horizontal_movements_cum, self.vertical_movements_cum = 0, 0
        # CONSTANTS
        self.b = 0
        self.g = 1
        self.r = 2
        self.green_dot = [204, 515]
        # Red target color (vertical crosshairs)
        self.b_target_lower_bound = 98
        self.g_target_lower_bound = 96
        self.r_target_lower_bound = 243
        self.b_target_upper_bound = 104
        self.g_target_upper_bound = 103
        self.r_target_upper_bound = 255
        # SETUP
        
        
    def run_droid_commands(self):
        swg_utils.chat('/macro dcs')
        
        
    def get_RDU_1(self):
        v = np.array([
                    (self.target[1] - self.green_dot[1]) / 892.006, 
                    1.0,
                    (self.green_dot[0] - self.target[0]) / 932.786
                    ])
        
        self.RDU_1 =  v / np.linalg.norm(v)
    
    
    def rotate_about_z_axis(self, vector, theta):
        return np.dot(np.array([
    [np.cos(theta), -np.sin(theta), 0],
    [np.sin(theta), np.cos(theta), 0],
    [0, 0, 1]
    ]), vector)
    
    
    def rotate_point_about_axis_by_angle(self, point, axis, theta):
        ux = axis[0]
        uy = axis[1]
        uz = axis[2]
        uxx = ux**2
        uyy = uy**2
        uzz = uz**2
        uxy = ux * uy
        uxz = ux * uz
        uyz = uy * uz
        c = np.cos(theta)
        s = np.sin(theta)
        t = 1.0 - c
        rotation_matrix = np.array([
    [t * uxx + c, t * uxy - s * uz, t * uxz + s * uy],
    [t * uxy + s * uz, t * uyy + c, t * uyz - s * ux],
    [t * uxz - s * uy, t * uyz + s * ux, t * uzz + c]
    ])
        return np.dot(rotation_matrix, point)
    
    
    def get_RDU_0(self):
        self.get_RDU_1()
        self.RDU_1_gamma_rotated = self.rotate_about_z_axis(self.RDU_1, self.gamma_01)
        rotated_x_axis = np.array([np.cos(self.gamma_01), np.sin(self.gamma_01), 0.0])
        self.RDU_0 = self.rotate_point_about_axis_by_angle(self.RDU_1_gamma_rotated, rotated_x_axis, self.phi_01)
    
    
    def arctan_0(self, vector):
        x = float(vector[0])
        y = float(vector[1])
        if x == 0:
            return 0
        if x == 0 and y == 0:
            return 0
        if x >= 0:
            return np.arctan(y / x) - (np.pi / 2.0)
        else:
            return np.arctan(y / x) + (np.pi / 2.0)
        
        
    def get_remaining_gamma_phi(self):
        self.gamma_02 = self.arctan_0(self.RDU_0)
        self.phi_02 = np.arcsin(self.RDU_0[2])
        self.gamma_12 = self.gamma_02 - self.gamma_01
        self.phi_12 = self.phi_02 - self.phi_01

    
    def convert_angles_to_movements(self, gamma, phi):
        horizontal_movements = -507.0 * gamma / (np.pi / 2.0)
        vertical_movements = -949.0 * phi / (np.pi / 2.0)
        return horizontal_movements, vertical_movements
        
        
    def convert_movements_to_angles(self, horizontal_movements, vertical_movements):
        gamma = -(np.pi / 2.0) * (horizontal_movements / 507.0)
        phi = -(np.pi / 2.0) * (vertical_movements / 949.0)
        return gamma, phi
    
    def get_aligning_movements(self):
        self.horizontal_movements_01, self.vertical_movements_01 = self.convert_angles_to_movements(self.gamma_01, self.phi_01)
        self.horizontal_movements_12, self.vertical_movements_12 = self.convert_angles_to_movements(self.gamma_12, self.phi_12)
        if self.horizontal_movements_12 > 0:
            self.horizontal_movements_12 = min(self.horizontal_movements_12, self.max_horizontal_movements - self.horizontal_movements_01)
        else:
            self.horizontal_movements_12 = max(self.horizontal_movements_12, self.min_horizontal_movements - self.horizontal_movements_01)
        if self.vertical_movements_12 > 0:
            self.vertical_movements_12 = min(self.vertical_movements_12, self.max_vertical_movements - self.vertical_movements_01)
        else:
            self.vertical_movements_12 = max(self.vertical_movements_12, self.min_vertical_movements - self.vertical_movements_01)
        # if not at the edge, fire
        self.fire = not (self.horizontal_movements_12 == self.max_horizontal_movements - self.horizontal_movements_01 or
            self.horizontal_movements_12 == self.min_horizontal_movements - self.horizontal_movements_01 or
            self.vertical_movements_12 == self.max_vertical_movements - self.vertical_movements_01 or 
            self.vertical_movements_12 == self.min_vertical_movements - self.vertical_movements_01)

            
    def get_trained_RDU_0(self):
        if len(self.RDU_lst) == 1:
            self.RDU_0 = self.RDU_lst[0]
        else:
            p = self.RDU_lst[-1] + 0.75 * (self.RDU_lst[-1] - self.RDU_lst[-2])
            self.RDU_0 = p / np.linalg.norm(p)


    def move_to_align(self):
        pdi.moveRel_fast(xOffset=int(np.sign(self.horizontal_movements_12)), loops=int(np.abs(self.horizontal_movements_12)))
        pdi.moveRel_fast(yOffset=int(np.sign(self.vertical_movements_12)), loops=int(np.abs(self.vertical_movements_12)))
        
        
    def fire_weapon(self):
        if self.fire:
            # FIRE!!!
            swg_utils.click(start_delay=0.025, return_delay=0)
            
        
    def get_crosshairs(self):
        crosshairs = [None, None]
        img_arr = swg_utils.take_screenshot(region=self.swg_region)
        # Find the indices of the matrix that correspond to the reticle's upper and lower hairs (vertical).
        # We are using the vertical hairs because they seem to be a constant color value as opposed to the horizontal
        # hairs which appear to have a range of values for R, G, and B.
        where_arr = np.where((img_arr[:,:,self.b] >= self.b_target_lower_bound) & (img_arr[:,:,self.g] >= self.g_target_lower_bound) & (img_arr[:,:,self.r] >= self.r_target_lower_bound)
                             & (img_arr[:,:,self.b] <= self.b_target_upper_bound) & (img_arr[:,:,self.g] <= self.g_target_upper_bound) & (img_arr[:,:,self.r] <= self.r_target_upper_bound))
        
        unique_cols_found = sorted(list(set(where_arr[1])))
        num_unique_cols_found = len(unique_cols_found)
        crosshairs[1] = None
        crosshairs[0] = None
        if num_unique_cols_found == 0:
            self.target = None
            return img_arr
        elif num_unique_cols_found == 1:
            # See if this column has 7 or 8 consecutively (rows) of the target color. If so, you've found one hair. See if there are pixels of the target color 29 pixels
            # rows after the last one of the hair (and the following 7 for that next hair). If so, use the half-way point as the row value of the center red dot and
            # assume the column value is the one found (you'll only be off by a little).
            # If none of these things are true, then pan a little to the right and try again with another screenshot.
            num_consecutive = 1
            for i in range(1, len(where_arr[0])):
                if where_arr[0][i] == where_arr[0][i - 1] + 1:
                    num_consecutive += 1
                    if num_consecutive > 6:
                        if 33 + where_arr[0][i] in where_arr[0]:
                            crosshairs[1] = int(unique_cols_found[0])
                            crosshairs[0] = int(np.mean([where_arr[0][i] - 6, where_arr[0][i] + 33]))
                        break
                else:
                    num_consecutive = 1
        elif num_unique_cols_found == 2:
            # Make sure that they are 5 rows apart. If so, this is likely the reticle. Use the column value that is halfway between them and use the row value that is
            # halfway between the top of each vertical hair.
            if unique_cols_found[1] - unique_cols_found[0] == 5:
                crosshairs[1] = int(unique_cols_found[0] + 2)
                crosshairs[0] = int(np.mean(where_arr[0]))
        elif num_unique_cols_found > 2:
            # See if there are two of them that are 5 rows apart. This is likely to be the reticle. If you really wanted to be sure you could also check to see if 
            # the ones that are 5 rows apart have more of the target color further down the column (for the other two vertical hairs).
            found_potential_hairs = False
            for u in range(num_unique_cols_found - 1):
                for v in range(u + 1, num_unique_cols_found):
                    if unique_cols_found[v] - unique_cols_found[u] == 5:
                        found_potential_hairs = True
                        break
            if found_potential_hairs:
                crosshairs[1] = int(unique_cols_found[u] + 2)
                df = pd.DataFrame({'row': where_arr[0], 'col': where_arr[1]})
                df = df.groupby('col').mean().reset_index()
                df.index = df['col'].values
                crosshairs[0] = int(np.mean([df.loc[unique_cols_found[u]]['row'], df.loc[unique_cols_found[v]]['row']]))
        if crosshairs[0] is None or crosshairs[1] is None:
            # The reticle is not visible at all.
            self.target = None
            return img_arr
        self.target = crosshairs
        return img_arr


    def find_white_arrow(self, img_arr):
        '''
        The white arrow which is on screen when an enemy is targeted but not in 
        view is somewhere radially around the green dot at a euclidean distance of 
        approximately 118 pixels to the center of the arrow. The arrow is some shade
        of grey and thus the B, G, and R values should all be pretty close to 
        each other.
        
        Notes
         Remove system messages in options
        '''
        r = 118
        theta = 0
        while theta < 2 * np.pi:
            y = int(self.green_dot[0] - r * np.sin(theta))
            x = int(self.green_dot[1] + r * np.cos(theta))
            if img_arr[y, x, 0] > 130 and img_arr[y, x, 0] == img_arr[y, x, 2] and np.abs(img_arr[y, x, 0] - img_arr[y, x, 1]) < 5:
                # Found it
                return y, x, theta
            theta += 0.008
        return None, None, None


    def conditional_move(self, left_condition, up_condition):
        if left_condition:
            num_horizontal_movements = max(self.min_horizontal_movements - self.horizontal_movements_cum, -self.max_movements)
        else:
            num_horizontal_movements = min(self.max_horizontal_movements - self.horizontal_movements_cum, self.max_movements)
        pdi.moveRel_fast(xOffset=int(np.sign(num_horizontal_movements)), loops=int(abs(num_horizontal_movements)))
        self.horizontal_movements_cum += num_horizontal_movements
        if up_condition:
            num_vertical_movements = max(self.min_vertical_movements - self.vertical_movements_cum, -self.max_movements)
        else:
            num_vertical_movements = min(self.max_vertical_movements - self.vertical_movements_cum, self.max_movements)
        pdi.moveRel_fast(yOffset=int(np.sign(num_vertical_movements)), loops=int(abs(num_vertical_movements)))
        self.vertical_movements_cum += num_vertical_movements
        

    def hunt_white_arrow(self):
        img_arr = swg_utils.take_screenshot(region=self.swg_region)
        y, x, theta = self.find_white_arrow(img_arr)
        if y is None:
            return
        self.conditional_move(theta > 0.5 * np.pi and theta <= 1.5 * np.pi, theta <= np.pi)

    
    def get_target(self, target_type='crosshairs'):
        self.crosshairs_found = False
        if target_type == 'crosshairs':
            img_arr = self.get_crosshairs()
            if self.target is not None:
                self.crosshairs_found = True
        return img_arr
    
    
    def hunt_target(self, target_type='crosshairs'):
        self.gamma_01, self.phi_01 = self.convert_movements_to_angles(self.horizontal_movements_cum, self.vertical_movements_cum)
        self.RDU_lst = []
        img_arr = self.get_target(target_type=target_type)
        if self.target is None:
            return
        self.get_RDU_0()
        self.RDU_lst.append(self.RDU_0)
        num_none_target = 0
        hunt_start_time = time.time()
        found_white_arrow, _, _ = self.find_white_arrow(img_arr)
        while num_none_target < self.num_none_target_max and time.time() - hunt_start_time < 20 and found_white_arrow is None:
            self.get_trained_RDU_0()
            self.get_remaining_gamma_phi()
            self.get_aligning_movements()
            self.move_to_align()
            if self.crosshairs_found:
                # Later could also fire when brown_avg found if target is within range (which depends on distance and speed and is usually sooner than the crosshairs light up)
                self.fire_weapon()
            self.horizontal_movements_cum += self.horizontal_movements_12
            self.vertical_movements_cum += self.vertical_movements_12
            self.gamma_01, self.phi_01 = self.convert_movements_to_angles(self.horizontal_movements_cum, self.vertical_movements_cum)
            img_arr = self.get_target(target_type)
            while self.target is None:
                num_none_target += 1
                if num_none_target >= self.num_none_target_max:
                    break
                img_arr = self.get_target(target_type)
            if num_none_target >= self.num_none_target_max:
                break
            if num_none_target > 0 and len(self.RDU_lst) > 0:
                del self.RDU_lst[0]
            num_none_target = 0
            # Ensure RDU_lst is always 1 or 2 in length but could rewrite things so this isn't necessary (could just use the last two elements and just keep tacking on new elements (target)).
            if len(self.RDU_lst) == 3:
                del self.RDU_lst[0]
            self.get_RDU_0()
            self.RDU_lst.append(self.RDU_0)
            found_white_arrow, _, _ = self.find_white_arrow(img_arr)

    
    def operate_turret(self):
        while True:
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            self.hunt_target(target_type='crosshairs')
            self.hunt_white_arrow()

        
class Rear_Turret(Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
        super(Rear_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)
        # CONSTANTS
        self.max_horizontal_movements = 507
        self.min_horizontal_movements = -507
        self.max_vertical_movements = 949
        self.min_vertical_movements = -949
        

class Deck_Turret(Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
        super(Deck_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)
        # CONSTANTS
        self.max_horizontal_movements = np.inf
        self.min_horizontal_movements = -np.inf
        #self.max_vertical_movements = 949
        #self.min_vertical_movements = -949
        
        
class Duty_Mission_Turret(Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
        super(Duty_Mission_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)
        
        
    def find_brown_from_duty_mission_enemy(self):
        # B, G, R against black background is constant 0, 32, 64
        img_arr = swg_utils.take_screenshot(window=self.swg_window, region=self.swg_region, set_focus=False)
        where_arr = swg_utils.find_pixels_on_BGR_arr(img_arr, b=0, g=32, r=64)
        if len(where_arr) > 0 and len(where_arr[0]) > 0:
            # Use average found pixel row and column
            self.target = [int(np.mean(where_arr[0])), int(np.mean(where_arr[1]))]
            return img_arr
        else:
            self.target = None
            return img_arr
        
        
    def get_target(self, target_type):
        self.crosshairs_found = False
        if target_type == 'crosshairs':
            img_arr = self.get_crosshairs()
            if self.target is not None:
                self.crosshairs_found = True
        elif target_type == 'brown_avg':
            img_arr = self.get_crosshairs()
            if self.target is None:
                img_arr = self.find_brown_from_duty_mission_enemy()
            else:
                self.crosshairs_found = True
        return img_arr
    
    
    def operate_turret(self):
        while True:
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            self.hunt_target(target_type='crosshairs')
            self.hunt_white_arrow()
            self.hunt_target(target_type='brown_avg')
        
        
class Duty_Mission_Rear_Turret(Duty_Mission_Turret, Rear_Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
        super(Duty_Mission_Rear_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)
        
        
class Duty_Mission_Deck_Turret(Duty_Mission_Turret, Deck_Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
        super(Duty_Mission_Deck_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)

        
class Pilot(Space):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843, full_speed=1350, enemy_full_speed=600):
        super(Pilot, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path)
        self.full_speed_when_booster_on = full_speed_when_booster_on
        self.full_speed = full_speed
        self.enemy_full_speed = enemy_full_speed
        # CONSTANTS
        self.ship_details_reactor_idx = np.array([65, 923])
        self.ship_details_spacing = 24
        self.num_components = 16
        self.ship_details_line_arr_additions = [8, 175]
        self.ship_details_armor_value_idx = np.array([550, 815])
        # INITIAL VALUES
        self.active_waypoint_idx = None
        self.active_wp_dct = {'Target_Location': {'idx': None, 'autopilot_to_idx': None}, 'zeros': {'idx': None, 'autopilot_to_idx': None}}
        self.mission_critical_dropdown_idx = None
        self.autopilot_to_enemy_idx = None
        self.target_dist_idx = None
        # SETUP
        pdi.press('n')
        time.sleep(0.5)
        
        
    def is_damaged(self):
        # Open component details window
        pdi.press('v')
        time.sleep(1)
        # Iterate through components and check if armor is not equal to max armor
        for component_i in range(self.num_components):
            component_idx = self.ship_details_reactor_idx + np.array([component_i * self.ship_details_spacing, 0])
            swg_utils.click(coords_idx=component_idx, region=self.swg_region, window=self.swg_window)
            img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=130,
                        scale_to=255, set_focus=False, sharpen=True)
            
            line_arr = img_arr[self.ship_details_armor_value_idx[0] : self.ship_details_armor_value_idx[0] + self.ship_details_line_arr_additions[0], 
                               self.ship_details_armor_value_idx[1] : self.ship_details_armor_value_idx[1] + self.ship_details_line_arr_additions[1]]
            
            current_armor, max_armor = ssc.get_number_from_arr(line_arr, numeric_type=float)
            if current_armor != max_armor:
                return True
            
        
    def boost_to_target(self):
        # Approximately 100m per second for 1000 speed.
        # So 1 speed = 0.1 m/s
        # Subtract off length of time to go from booster speed to 0
        target_dist = self.get_target_dist(fail_gracefully=True)
        if target_dist is None:
            return
        booster_duration = max((target_dist / (self.full_speed_when_booster_on * 0.1)) - 14, 0)
        if booster_duration < 1:
            return
        pdi.press('b')
        time.sleep(booster_duration)
        pdi.press('b')
        
        
    def go_to_space_station(self, space_station_name='Rori'):
        swg_utils.chat('/tar ' + space_station_name)
        time.sleep(0.2)
        if self.get_target_dist() < 1000:
            return
        swg_utils.chat('/fol')
        time.sleep(0.1)
        swg_utils.chat('/tar ' + space_station_name)
        while self.get_target_dist() > self.distance_to_start_winding_down:
            swg_utils.chat('/fol')
            self.boost_to_target()
        swg_utils.chat('/throttle 0.1')
        while self.get_target_dist() > self.distance_to_go_slow:
            time.sleep(0.5)
            while self.get_target_dist() > self.distance_to_start_winding_down:
                swg_utils.chat('/fol')
                self.boost_to_target()
                swg_utils.chat('/throttle 0.1')
        # Never go 0 speed due to swg bug that can make distances be extremely off.
        swg_utils.chat('/throttle 0.01')
        while self.get_target_dist() > 1000:
            time.sleep(0.5)
            
            
    def mission_critical_dropdown_gone(self):
        if self.active_waypoint_idx is None:
            active_wp_arr = swg_utils.get_search_arr('Active_Waypoints', dir_path=self.dir_path, mask_int=None)
            self.active_waypoint_idx, img_arr = swg_utils.find_arr_on_region(active_wp_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=194)
        img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=194,
                    scale_to=255, set_focus=False, sharpen=True)
        
        if self.mission_critical_dropdown_idx is None:
            self.mission_critical_dropdown_idx = [self.active_waypoint_idx[0] - 22, self.active_waypoint_idx[1] - 14]
        if self.mission_critical_dropdown_idx[0] < 0 or self.mission_critical_dropdown_idx[1] < 0:
            raise Exception('Mission Critical window not visible enough or at all.')
        # If 0 then mission critical dropdown arrow is gone (because no more enemies)
        return img_arr[self.mission_critical_dropdown_idx[0], self.mission_critical_dropdown_idx[1]] == 0
    
    
    def get_active_wp_idx(self, active_wp_name):
        get_active_wp_i = 0
        if self.active_wp_dct[active_wp_name]['idx'] is None:
            active_wp_arr = swg_utils.get_search_arr(active_wp_name, dir_path=self.dir_path, mask_int=None)
        while self.active_wp_dct[active_wp_name]['idx'] is None and get_active_wp_i < 2:
            if self.active_waypoint_idx is None:
                start_row = 0
                start_col = 0
            else:
              start_row = self.active_waypoint_idx[0]
              start_col = self.active_waypoint_idx[1]
            self.active_wp_dct[active_wp_name]['idx'], img_arr = swg_utils.find_arr_on_region(active_wp_arr, region=self.swg_region, start_row=start_row, start_col=start_col, fail_gracefully=True, sharpen_threshold=194)
            if self.active_wp_dct[active_wp_name]['idx'] is None:
                if self.active_waypoint_idx is None:
                    active_wp_arr = swg_utils.get_search_arr('Active_Waypoints', dir_path=self.dir_path, mask_int=None)
                    self.active_waypoint_idx, img_arr = swg_utils.find_arr_on_region(active_wp_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=194)
                # If Active Waypoints dropdown is closed, open it
                self.dropdown_arrow_idx = [self.active_waypoint_idx[0], self.active_waypoint_idx[1] - 4]
                if img_arr[self.dropdown_arrow_idx[0], self.dropdown_arrow_idx[1]] == 0:
                    swg_utils.click(button='left', start_delay=0.02, return_delay=0.3, window=self.swg_window, region=self.swg_region, coords_idx=self.dropdown_arrow_idx, activate_window=False)
                    time.sleep(0.3)
            get_active_wp_i += 1
                    
                    
    def autopilot_to_wp(self, active_wp_name):
        time.sleep(0.2)
        self.get_active_wp_idx(active_wp_name)
        self.target_location_clickable_idx = [self.active_wp_dct[active_wp_name]['idx'][0] + 7, self.active_wp_dct[active_wp_name]['idx'][1] + 25]
        swg_utils.click(button='right', start_delay=0.02, return_delay=0.3, window=self.swg_window, region=self.swg_region, coords_idx=self.target_location_clickable_idx, activate_window=False)
        if self.active_wp_dct[active_wp_name]['autopilot_to_idx'] is None:
            autopilot_to_arr = swg_utils.get_search_arr('Autopilot_To', dir_path=self.dir_path, mask_int=None)
            self.active_wp_dct[active_wp_name]['autopilot_to_idx'], img_arr = swg_utils.find_arr_on_region(autopilot_to_arr, region=self.swg_region, start_row=max(self.active_wp_dct[active_wp_name]['idx'][0] - 100, 0), start_col=max(self.active_wp_dct[active_wp_name]['idx'][1] - 100, 0), fail_gracefully=False, sharpen_threshold=194)
        swg_utils.click(button='left', start_delay=0.1, return_delay=0.4, window=self.swg_window, region=self.swg_region, coords_idx=self.active_wp_dct[active_wp_name]['autopilot_to_idx'], activate_window=False)
        pdi.moveTo(x=self.swg_region['left'] + 51, y=self.swg_region['top'] + 51)
        time.sleep(0.3)
        
        
    def get_away_from_space_station(self):
        self.autopilot_to_wp('Target_Location')
        time.sleep(7)
        while self.mission_critical_dropdown_gone():
            swg_utils.chat('/throttle 1.0')
            swg_utils.press('b')
            time.sleep(7)
            self.autopilot_to_wp('Target_Location')
            time.sleep(7)
            
            
    def got_mission(self):
        if self.active_wp_dct['Target_Location']['idx'] is None:
            self.get_active_wp_idx('Target_Location')
        if self.active_wp_dct['Target_Location']['idx'] is None:
            return False
        target_location_arr = swg_utils.get_search_arr('Target_Location', dir_path=self.dir_path, mask_int=None)
        img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=194, scale_to=255, set_focus=False, sharpen=True)
        # If the "Target Location" isn't there anymore, then the duty mission is over. Get new mission.
        if not np.all(img_arr[self.active_wp_dct['Target_Location']['idx'][0] : self.active_wp_dct['Target_Location']['idx'][0] + target_location_arr.shape[0], 
                self.active_wp_dct['Target_Location']['idx'][1] : self.active_wp_dct['Target_Location']['idx'][1] + target_location_arr.shape[1]] ==
                target_location_arr):
            
            # Wait a bit to make sure
            time.sleep(3)
        else:
            return True
            
        return (np.all(img_arr[self.active_wp_dct['Target_Location']['idx'][0] : self.active_wp_dct['Target_Location']['idx'][0] + target_location_arr.shape[0], 
                self.active_wp_dct['Target_Location']['idx'][1] : self.active_wp_dct['Target_Location']['idx'][1] + target_location_arr.shape[1]] ==
                target_location_arr) or 
                
                swg_utils.find_arr_on_region(target_location_arr, region=self.swg_region, start_row=max(self.active_wp_dct['Target_Location']['idx'][0] - 200, 0), start_col=max(self.active_wp_dct['Target_Location']['idx'][1] - 200, 0), fail_gracefully=True, sharpen_threshold=194)[0] is not None
                )
            
    
    def get_duty_mission_from_space_station(self):
        if self.got_mission():
            return
        self.go_to_space_station()
        if self.is_damaged():
            swg_utils.chat('/macro repairAndGetMission')
        else:
            swg_utils.chat('/macro GetMission')
        time.sleep(10)
        self.get_away_from_space_station()
        
        
    def mission_critical_dropped_down(self):
        if self.active_waypoint_idx is None:
            active_wp_arr = swg_utils.get_search_arr('Active_Waypoints', dir_path=self.dir_path, mask_int=None)
            self.active_waypoint_idx, img_arr = swg_utils.find_arr_on_region(active_wp_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=194)
        img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=194,
                    scale_to=255, set_focus=False, sharpen=True)
        
        if self.mission_critical_dropdown_idx is None:
            self.mission_critical_dropdown_idx = [self.active_waypoint_idx[0] - 22, self.active_waypoint_idx[1] - 14]
        if self.mission_critical_dropdown_idx[0] < 0 or self.mission_critical_dropdown_idx[1] < 0:
            raise Exception('Mission Critical window not visible enough or at all.')
        return img_arr[self.mission_critical_dropdown_idx[0], self.mission_critical_dropdown_idx[1] + 10] == 255
    
    
    def autopilot_to_enemy(self):
        if self.mission_critical_dropdown_gone():
            return
        if not self.mission_critical_dropped_down():
            swg_utils.click(button='left', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
        enemy_idx = [self.mission_critical_dropdown_idx[0] + 30, self.mission_critical_dropdown_idx[1] + 25]
        for _ in range(self.num_times_to_click_autopilot_to_enemy):
            swg_utils.click(button='right', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=enemy_idx, activate_window=False)
            if self.autopilot_to_enemy_idx is None:
                autopilot_to_enemy_arr = swg_utils.get_search_arr('Autopilot_To', dir_path=self.dir_path, mask_int=None)
                self.autopilot_to_enemy_idx, img_arr = swg_utils.find_arr_on_region(autopilot_to_enemy_arr, region=self.swg_region, start_row=max(enemy_idx[0] - 100, 0), start_col=max(enemy_idx[1] - 100, 0), fail_gracefully=False, sharpen_threshold=194)
            swg_utils.click(button='left', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=self.autopilot_to_enemy_idx, activate_window=False)
            time.sleep(self.interval_delay)
        if self.mission_critical_dropped_down():
            swg_utils.click(button='left', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
        
        
class Fighter_Pilot(Pilot):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843, full_speed=1350, enemy_full_speed=600):
        super(Fighter_Pilot, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on, full_speed=full_speed, enemy_full_speed=enemy_full_speed)
        # CONSTANTS
        self.distance_to_start_winding_down = 1300
        self.distance_to_go_slow = 1050
        self.num_times_to_click_autopilot_to_enemy = 10
        self.interval_delay = 0.1
        self.time_to_reach_full_speed = 3
        
        
class POB_Pilot(Pilot):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843, full_speed=1350, enemy_full_speed=600):
        super(POB_Pilot, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on, full_speed=full_speed, enemy_full_speed=enemy_full_speed)
        # CONSTANTS
        self.distance_to_start_winding_down = 2400
        self.distance_to_go_slow = 1100
        self.num_times_to_click_autopilot_to_enemy = 3
        self.interval_delay = 1
        self.time_to_reach_full_speed = 5
        
    
class Duty_Mission_Pilot(Pilot):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843, full_speed=1350, enemy_full_speed=600):
        super(Duty_Mission_Pilot, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on, full_speed=full_speed, enemy_full_speed=enemy_full_speed)
        
        
class Duty_Mission_Fighter_Pilot(Duty_Mission_Pilot, Fighter_Pilot):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843, full_speed=1350, enemy_full_speed=600):
        super(Duty_Mission_Fighter_Pilot, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on, full_speed=full_speed, enemy_full_speed=enemy_full_speed)
        
        
class Duty_Mission_POB_Pilot(Duty_Mission_Pilot, POB_Pilot):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843, full_speed=1350, enemy_full_speed=600):
        super(Duty_Mission_POB_Pilot, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on, full_speed=full_speed, enemy_full_speed=enemy_full_speed)
        
    
    def optimize_speed(self):
        start_time = time.time()
        while not self.mission_critical_dropdown_gone():  
            if time.time() - start_time > 45:
                self.autopilot_to_wp('zeros')
                start_time = time.time()
            pdi.press(self.target_closest_enemy_hotkey)
            # Get distance from enemy so you know whether to slow down or speed up
            dist_to_enemy = self.get_target_dist(fail_gracefully=True)
            if dist_to_enemy is None:
                continue
            if dist_to_enemy > 700:
                pdi.press('s')
            elif dist_to_enemy > 500:
                # Don't press s every iteration in order to not slow down too quickly.
                pdi.press('m')
                if self.enemy_full_speed < self.full_speed:
                    pdi.press('s', presses=2)
            else:
                pdi.press('w')
            if dist_to_enemy > 2000:
                # Possibly disabled, autopilot to the enemy
                for _ in range(10):
                    self.autopilot_to_enemy()
                swg_utils.chat('/throttle 1.0')
        
        
    def pilot_main(self):
        while True:
            if not self.got_mission():
                self.get_duty_mission_from_space_station()
            i = 1
            while self.mission_critical_dropdown_gone():
                self.autopilot_to_wp('Target_Location')
                if i % 10 == 0:
                    swg_utils.chat('/throttle 1.0')
                i += 1
            # Enemies enaging
            if self.mission_critical_dropped_down():
                swg_utils.click(button='left', start_delay=0.02, return_delay=0.1, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
            self.optimize_speed()
            swg_utils.click(button='left', start_delay=0.02, return_delay=0.1, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
            self.autopilot_to_wp('Target_Location')

    
def main_duty_mission_rear_turret(swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
    turret = Duty_Mission_Rear_Turret(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)
    # For now, assume only need to run commands once (which assumes the ship doesn't get destroyed etc)
    #turret.run_droid_commands()
    turret.operate_turret()


def main_duty_mission_deck_turret(swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), max_movements=70, num_none_target_max=5):
    turret = Duty_Mission_Deck_Turret(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, max_movements=max_movements, num_none_target_max=num_none_target_max)
    # For now, assume only need to run commands once (which assumes the ship doesn't get destroyed etc)
    turret.run_droid_commands()
    turret.operate_turret()
    

def main_duty_mission_POB_pilot(swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843):
    pilot = Duty_Mission_POB_Pilot(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on)
    pilot.pilot_main()
    
    
def main_duty_mission_fighter_pilot(swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), full_speed_when_booster_on=1843):
    pilot = Duty_Mission_POB_Pilot(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, full_speed_when_booster_on=full_speed_when_booster_on)
    pilot.pilot_main() 
    
    
def main(task_type='duty_mission', turret_type='None', pilot_type='None'):
    swg_window_i = config.get_value('main', 'swg_window_i', desired_type=int, required_to_be_in_conf=False, default_value=0)
    if task_type == 'duty_mission':
        if turret_type == 'rear':
            main_duty_mission_rear_turret(swg_window_i=swg_window_i)
        elif turret_type == 'deck':
            main_duty_mission_deck_turret(swg_window_i=swg_window_i)
        elif pilot_type == 'POB':
            main_duty_mission_POB_pilot(swg_window_i=swg_window_i)
        elif pilot_type == 'fighter':
            main_duty_mission_fighter_pilot(swg_window_i=swg_window_i)
        else:
            raise Exception('Invalid turret_type or pilot_type')
    else:
        raise Exception('Invalid task_type')
    
if __name__ == '__main__':
    task_type = config.get_value('main', 'task_type', desired_type=str, required_to_be_in_conf=False, default_value='duty_mission')
    turret_type = config.get_value('main', 'turret_type', desired_type=str, required_to_be_in_conf=False, default_value='None')
    pilot_type = config.get_value('main', 'pilot_type', desired_type=str, required_to_be_in_conf=False, default_value='None')
    main(task_type=task_type, turret_type=turret_type, pilot_type=pilot_type)
    