# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 13:42:59 2022

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
from python_utils import file_utils, list_utils, pandas_utils
import time
import numpy as np
git_path = config.config_dct['main']['git_path']
sys.path.append(r"" + git_path)
import pydirectinput_tmr as pdi
import swg_window_management as swm
import run_waypoint_path as rwp
import swg_utils
import pandas as pd
import random
import sort_space_components as ssc
from copy import deepcopy
from scipy.spatial import distance
import matplotlib.pyplot as plt
from pprint import pprint


class SWG:
    def __init__(self, swg_window_i=0):
        self.swg_window = swm.swg_windows[swg_window_i]
        self.swg_region = swm.swg_window_regions[swg_window_i]
        self.ui_dir_path = os.path.join(git_path, 'UI_dir', 'indices_for_ui_items_for_' + socket.gethostname())
        file_utils.mkdir_if_DNE(self.ui_dir_path)
        # SETUP
        swm.calibrate_window_position(swm.swg_windows)
        self.swg_window.set_focus()
        time.sleep(1.5)
        

class Space(SWG):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), 
            ship_loadout={
            'Front_Shield_Hitpoints': 100, 
            'Back_Shield_Hitpoints': 100,
            'Front_Armor_Hitpoints': 100,
            'Back_Armor_Hitpoints': 100,
            'Droid_Command_Speed': 8,
            'Capacitor_Energy': 100},
            droid_commands=[
                'weapcap_powerup_4', 'engine_overload_4', 'weapons_overload_4', 'shield_adjust_rear_4', 'shields_backtofront_1', 'shields_fronttoback_1', 'shield_emergency_rear', 'weapcap_to_shield_1', 'zone_to_kessel'
                ]
            ):
        
        super(Space, self).__init__(swg_window_i=swg_window_i)
        # CONSTANTS
        self.droid_command_df = pd.read_csv(os.path.join(git_path, 'constants', 'droid_command_constants.csv'))
        # PARAMETERS
        self.dir_path = dir_path
        self.target_closest_enemy_hotkey = target_closest_enemy_hotkey
        self.space_target_distance_digits = {digit: swg_utils.get_search_arr('space_target_distance_digit_' + str(digit), dir_path=self.dir_path, mask_int=None) for digit in range(10)}
        self.complete_arr = swg_utils.get_search_arr('complete', dir_path=self.dir_path, mask_int=None)
        self.target_this_arr = swg_utils.get_search_arr('target_this', dir_path=self.dir_path, mask_int=None)
        self.vertical_triangle_side_arr = swg_utils.get_search_arr('vertical_triangle_side_arr', dir_path=self.dir_path, mask_int=None)
        self.horizontal_triangle_side_arr = swg_utils.get_search_arr('horizontal_triangle_side_arr', dir_path=self.dir_path, mask_int=None)
        self.radar_arr = swg_utils.get_search_arr('space_radar', dir_path=self.dir_path, mask_int=None)
        self.front_shield_arr = swg_utils.get_search_arr('front_shields', dir_path=self.dir_path, mask_int=None)
        self.back_shield_arr = swg_utils.get_search_arr('back_shields', dir_path=self.dir_path, mask_int=None)
        self.front_armor_arr = swg_utils.get_search_arr('front_armor', dir_path=self.dir_path, mask_int=None)
        self.back_armor_arr = swg_utils.get_search_arr('back_armor', dir_path=self.dir_path, mask_int=None)
        self.capacitor_arr = swg_utils.get_search_arr('capacitor', dir_path=self.dir_path, mask_int=None)
        self.ship_loadout = ship_loadout
        self.droid_commands = droid_commands
        # SETUP
        self.front_shield_arr_count = self.front_shield_arr.sum()
        self.back_shield_arr_count = self.back_shield_arr.sum()
        self.front_armor_arr_count = self.front_armor_arr.sum()
        self.back_armor_arr_count = self.back_armor_arr.sum()
        self.capacitor_arr_count = self.capacitor_arr.sum()
        # FIND UI ITEMS
        self.find_radar()
        # INITIAL VALUES
        self.droid_ready_time = time.time()
        self.target_dist_idx = None
        self.ship_status = {'Front_Shield_Hitpoints': self.ship_loadout['Front_Shield_Hitpoints'], 
                            'Back_Shield_Hitpoints': self.ship_loadout['Back_Shield_Hitpoints'],
                            'Front_Armor_Hitpoints': self.ship_loadout['Front_Armor_Hitpoints'],
                            'Back_Armor_Hitpoints': self.ship_loadout['Back_Armor_Hitpoints'],
                            'Capacitor_Energy': self.ship_loadout['Capacitor_Energy']}
        
        
    def dc_val(self, value_col_name):
        return pandas_utils.get_value_from_row(self.droid_command_df, 'command_id', self.command_id, value_col_name)
    
    
    def droid_command_is_bulk_runnable(self):
        for bulk_runnable_command_type in ['weapcap_powerup', 'engine_overload', 'reactor_overload', 'weapon_overload', 'shield_adjust']:
            if bulk_runnable_command_type in self.command_id:
                return True
        return False
    
    
    def run_droid_command(self, command_id=None):
        if command_id is not None:
            self.command_id = command_id
        if self.command_id not in self.droid_commands:
            return
        # The following line can be used if you dont have your toolbar setup
        #swg_utils.chat('/droid ' + self.dc_val('command_name'))
        # The following line is ued if you have your toolbar setup (commands are in the order you provided in the droid_commands list)
        pdi.press('f' + str(1 + self.droid_commands.index(self.command_id)))
        self.droid_ready_time = time.time() + self.dc_val('delay') * self.ship_loadout['Droid_Command_Speed']
        
    
    def run_bulk_droid_commands(self):
        pdi.press('esc')
        for self.command_id in self.droid_commands:
            if self.droid_command_is_bulk_runnable():
                self.run_droid_command()
            if 'shield_adjust' in self.command_id:
                self.ship_loadout['Front_Shield_Hitpoints'] = self.ship_loadout['Front_Shield_Hitpoints'] * self.dc_val('front_shield_ratio')
                self.ship_loadout['Back_Shield_Hitpoints'] = self.ship_loadout['Back_Shield_Hitpoints'] * (2 - self.dc_val('front_shield_ratio'))
            time.sleep(self.dc_val('delay') * self.ship_loadout['Droid_Command_Speed'])
            
            
    def manage_shields(self):
        '''
        Purpose
        -------
        Issue shield reinforcement and/or shield shunt droid commands to maintain front and back shield HP without wasting capacitor energy.
        
        Method
        ------
        0. If the droid is not ready for a new command yet, return and assume that this function is called frequently enough for this to not be an issue.
        1. Get current front and back shield hp and capacitor energy
        2. Determine total (front + back) missing hp
        3. The shunt level to use is the highest one that would yield less than the total missing hp
        4. If necessary, use reinforce to enable the shunt to not waste energy
        5. Use the shunt.
        6. Only do 1 command per call to this function, that way you can continue firing while the droid timer cools down. It is assumed that this function is called frequently enough for this to not be an issue.
        
        
        Info
        ----
        1. Only use a shield shunt when no energy would be wasted. i.e. the hp missing in front AND back is enough.
        2. It is usually better to use reinforce to then enabled the highest level shield shunt command loaded due to the short delay for reinforce and long delay for shunt.
        
        Notes
        -----
        1. This function does not give a preference to front or rear shields. In other words, e.g. if the front shield is damaged but not the back, this function will reinforce from the back to the front and then shunt. (thus it does not favor the back at the expense of the front or vice versa)
        2. This function will not do a reinforce nor shunt unless total_hp_missing is >= 25% of current capacitor energy.
        '''
        if time.time() < self.droid_ready_time:
            return
        self.get_shield_hp()
        self.get_capacitor_energy()
        front_hp_missing = self.ship_loadout['Front_Shield_Hitpoints'] - self.ship_status['Front_Shield_Hitpoints']
        back_hp_missing = self.ship_loadout['Back_Shield_Hitpoints'] - self.ship_status['Back_Shield_Hitpoints']
        total_hp_missing = front_hp_missing + back_hp_missing
        capacitor_shuntable_energy = np.array([0, 0.25, 0.5, 0.75, 1]) * self.ship_status['Capacitor_Energy']
        # Determine the best shunt level to use
        hp_vs_available = total_hp_missing - capacitor_shuntable_energy
        hp_vs_available[np.where(hp_vs_available < 0)] = 1e8
        shunt_level = hp_vs_available.argmin()
        if shunt_level == 0:
            return
        # Determine which loaded level is at or below best level
        best_loaded_shunt_level = 0
        for self.command_id in self.droid_commands:
            if 'weapcap_to_shield' in self.command_id:
                current_level = int(self.command_id.split('_')[-1])
                if current_level <= shunt_level and current_level > best_loaded_shunt_level:
                    best_loaded_shunt_level = deepcopy(current_level)
        if best_loaded_shunt_level == 0:
            return
        energy_to_each_shield = capacitor_shuntable_energy[best_loaded_shunt_level] / 2
        if back_hp_missing < energy_to_each_shield:
            # Determine which level shield reinforce to use
            front_shield_reinforcable_energy = np.array([0, 0.2, 0.5, 0.8, 1]) * self.ship_status['Front_Shield_Hitpoints']
            hp_vs_available = back_hp_missing - front_shield_reinforcable_energy
            hp_vs_available[np.where(hp_vs_available < 0)] = 1e8
            reinforce_level = hp_vs_available.argmin()
            if reinforce_level != 0:
                # Determine which loaded level is at or below the best level
                best_loaded_reinforce_level = 0
                for self.command_id in self.droid_commands:
                    if 'shields_fronttoback' in self.command_id:
                        current_level = int(self.command_id.split('_')[-1])
                        if current_level <= reinforce_level and current_level > best_loaded_reinforce_level:
                            best_loaded_reinforce_level = deepcopy(current_level)
                if best_loaded_reinforce_level != 0:
                    self.run_droid_command('shields_fronttoback_' + str(best_loaded_reinforce_level))
                    return
        if front_hp_missing < energy_to_each_shield:
            # Determine which level shield reinforce to use
            back_shield_reinforcable_energy = np.array([0, 0.2, 0.5, 0.8, 1]) * self.ship_status['Back_Shield_Hitpoints']
            hp_vs_available = front_hp_missing - back_shield_reinforcable_energy
            hp_vs_available[np.where(hp_vs_available < 0)] = 1e8
            reinforce_level = hp_vs_available.argmin()
            if reinforce_level != 0:
                # Determine which loaded level is at or below the best level
                best_loaded_reinforce_level = 0
                for self.command_id in self.droid_commands:
                    if 'shields_backtofront' in self.command_id:
                        current_level = int(self.command_id.split('_')[-1])
                        if current_level <= reinforce_level and current_level > best_loaded_reinforce_level:
                            best_loaded_reinforce_level = deepcopy(current_level)
                if best_loaded_reinforce_level != 0:
                    self.run_droid_command('shields_backtofront_' + str(best_loaded_reinforce_level))
                    return
        self.run_droid_command('weapcap_to_shield_' + str(best_loaded_shunt_level))
        
        
    def find_radar(self):
        radar_fpath = os.path.join(self.ui_dir_path, 'radar_idx.csv')
        if os.path.exists(radar_fpath):
            self.radar_idx = file_utils.read_csv(radar_fpath, dtype=int)[0]
            return
        img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, set_focus=False, sharpen=False)
        maximal_similarity_dct = {'idx':[0,0], 'similarity': 0}
        for i in range(img_arr.shape[0]):
            for j in range(img_arr.shape[1]):
                search_arr = img_arr[i : i + self.radar_arr.shape[0], j : j + self.radar_arr.shape[1]]
                if search_arr.shape != self.radar_arr.shape:
                    continue
                similarity = (search_arr == self.radar_arr).sum()
                if similarity > maximal_similarity_dct['similarity']:
                    maximal_similarity_dct['idx'] = [i, j]
                    maximal_similarity_dct['similarity'] = similarity
        if maximal_similarity_dct['similarity'] / self.radar_arr.size < 0.3:
            raise Exception('Could not find radar widget with at least 30% of pixels matching')
        self.radar_idx = maximal_similarity_dct['idx']
        file_utils.write_row_to_csv(radar_fpath, list(self.radar_idx), mode='w')
        
        
    def get_shield_hp(self):
        radar_region = {'top': self.radar_idx[0] + self.swg_region['top'], 'left': self.radar_idx[1] + self.swg_region['left'], 'width': self.front_shield_arr.shape[1], 'height': self.front_shield_arr.shape[0]}
        current_radar_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=radar_region, set_focus=False, sharpen=True, sharpen_threshold=1, scale_to=1)
        # Ratio the current pixels that are 1 with the array that has full shield hp.
        self.ship_status['Front_Shield_Hitpoints'] = self.ship_loadout['Front_Shield_Hitpoints'] * (current_radar_arr * self.front_shield_arr).sum() / self.front_shield_arr_count
        self.ship_status['Back_Shield_Hitpoints'] = self.ship_loadout['Back_Shield_Hitpoints'] * (current_radar_arr * self.back_shield_arr).sum() / self.back_shield_arr_count
        
        
    def get_armor_hp(self):
        radar_region = {'top': self.radar_idx[0] + self.swg_region['top'], 'left': self.radar_idx[1] + self.swg_region['left'], 'width': self.front_armor_arr.shape[1], 'height': self.front_armor_arr.shape[0]}
        current_radar_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=radar_region, set_focus=False, sharpen=False)
        # Ratio the current pixels that are 1 with the array that has full armor hp.
        self.ship_status['Front_Armor_Hitpoints'] = self.ship_loadout['Front_Armor_Hitpoints'] * (current_radar_arr * self.front_armor_arr).sum() / self.front_armor_arr_count
        self.ship_status['Back_Armor_Hitpoints'] = self.ship_loadout['Back_Armor_Hitpoints'] * (current_radar_arr * self.back_armor_arr).sum() / self.back_armor_arr_count
        
        
    def get_capacitor_energy(self):
        radar_region = {'top': self.radar_idx[0] + self.swg_region['top'], 'left': self.radar_idx[1] + self.swg_region['left'], 'width': self.front_armor_arr.shape[1], 'height': self.front_armor_arr.shape[0]}
        current_radar_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=radar_region, set_focus=False, sharpen=False)
        # Ratio the current pixels that are 1 with the array that has full capacitor energy.
        self.ship_status['Capacitor_Energy'] = self.ship_loadout['Capacitor_Energy'] * (current_radar_arr * self.capcitor_arr).sum() / self.capacitor_arr_count
        
        
        
    def get_target_dist(self, fail_gracefully=False):
        if self.target_dist_idx is None:
            # Target group leader to ensure something is within range to target. Group leader should be pilot.
            swg_utils.chat('/tar OddBodkins')
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
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
        super(Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path)
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
        
        
    def reset_station(self):
        '''
        Purpose
        -------
        It is suspected that being in the space view too long can cause issues 
        such as the toon is logged out or crashing. A possible remedy is to 
        exit current station and re-enter it.
        '''
        # Leave turret
        pdi.press('l')
        time.sleep(4.5)
        # Reset turret orientation
        self.horizontal_movements_cum, self.vertical_movements_cum = 0, 0
        # Re-enter turret
        swg_utils.chat('/tar Turret')
        swg_utils.chat('/ui action radialMenu')
        pdi.press('1')
        time.sleep(4.5)
        
        
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
        horizontal_movements = np.around(-507.0 * gamma / (np.pi / 2.0), 3)
        vertical_movements = np.around(-949.0 * phi / (np.pi / 2.0), 3)
        return horizontal_movements, vertical_movements
        
        
    def convert_movements_to_angles(self, horizontal_movements, vertical_movements):
        gamma = -(np.pi / 2.0) * (horizontal_movements / 507.0)
        phi = -(np.pi / 2.0) * (vertical_movements / 949.0)
        return gamma, phi
    
    def get_aligning_movements(self):
        self.horizontal_movements_01, self.vertical_movements_01 = self.convert_angles_to_movements(self.gamma_01, self.phi_01)
        if (self.horizontal_movements_01 > self.max_horizontal_movements or
            self.horizontal_movements_01 < self.min_horizontal_movements or
            self.vertical_movements_01 > self.max_vertical_movements or
            self.vertical_movements_01 < self.min_vertical_movements
            ):
            print('self.horizontal_movements_01 > self.max_horizontal_movements', self.horizontal_movements_01 > self.max_horizontal_movements)
            print('self.horizontal_movements_01 < self.min_horizontal_movements', self.horizontal_movements_01 < self.min_horizontal_movements)
            print('self.vertical_movements_01 > self.max_vertical_movements', self.vertical_movements_01 > self.max_vertical_movements)
            print('self.vertical_movements_01 < self.min_vertical_movements', self.vertical_movements_01 < self.min_vertical_movements)
            print('self.horizontal_movements_01', self.horizontal_movements_01, 'self.max_horizontal_movements', self.max_horizontal_movements, 'self.min_horizontal_movements', self.min_horizontal_movements)
            print('self.vertical_movements_01', self.vertical_movements_01, 'self.max_vertical_movements', self.max_vertical_movements, 'self.min_vertical_movements', self.min_vertical_movements)
            raise Exception('gotten 01 movements were outside max/min bounds which is a bug.')
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
        target_dist = self.get_target_dist(fail_gracefully=True)
        self.fire = target_dist is not None and target_dist < 600 and not (self.horizontal_movements_12 == self.max_horizontal_movements - self.horizontal_movements_01 or
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
        time.sleep(0.1)
        
    def fire_weapon(self):
        if self.fire:
            # FIRE!!!
            swg_utils.click(start_delay=0.025, return_delay=0)
            
        
    def get_crosshairs(self):
        crosshairs = [None, None]
        b_lead_reticle = 212
        g_lead_reticle = 0
        r_lead_reticle = 255
        crosshairs = [None, None]
        img_arr = swg_utils.take_screenshot(region=self.swg_region)
        # Find the indices of the matrix that correspond to the reticle's upper and lower hairs (vertical).
        # We are using the vertical hairs because they seem to be a constant color value as opposed to the horizontal
        # hairs which appear to have a range of values for R, G, and B.
        where_arr = swg_utils.find_pixels_on_BGR_arr(img_arr, b=b_lead_reticle, g=g_lead_reticle, r=r_lead_reticle, fail_gracefully=True)
        if where_arr is None:
            self.target = None
            return img_arr
        
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


    def conditional_move(self, max_left_movements=0, max_right_movements=0, max_up_movements=0, max_down_movements=0):
        num_left_movements = int(abs(max(self.min_horizontal_movements - self.horizontal_movements_cum, -max_left_movements)))
        pdi.moveRel_fast(xOffset=-1, loops=num_left_movements)
        self.horizontal_movements_cum -= num_left_movements
        num_right_movements = int(abs(min(self.max_horizontal_movements - self.horizontal_movements_cum, max_right_movements)))
        pdi.moveRel_fast(xOffset=1, loops=num_right_movements)
        self.horizontal_movements_cum += num_right_movements
        num_up_movements = int(abs(max(self.min_vertical_movements - self.vertical_movements_cum, -max_up_movements)))
        pdi.moveRel_fast(yOffset=-1, loops=num_up_movements)
        self.vertical_movements_cum -= num_up_movements
        num_down_movements = int(abs(min(self.max_vertical_movements - self.vertical_movements_cum, max_down_movements)))
        pdi.moveRel_fast(yOffset=1, loops=num_down_movements)
        self.vertical_movements_cum += num_down_movements
        time.sleep(0.1)
        

    def hunt_target_arrow(self):
        b, g, r = [204, 0, 204]
        square_length_containing_arrow = 255
        half_length = int(255/2)
        max_movements=100
        hunt_target_arrow_start_time = time.time()
        while time.time() - hunt_target_arrow_start_time < 5:
            img_arr = swg_utils.take_screenshot(region=self.swg_region)
            where_arr = swg_utils.find_pixels_on_BGR_arr(img_arr, b=b, g=g, r=r, 
            start_row=self.green_dot[0] - half_length,
            end_row=self.green_dot[0] + half_length, 
            start_col=self.green_dot[1] - half_length, 
            end_col=self.green_dot[1] + half_length,
            return_as_rect_arr=True, fail_gracefully=True)
            
            if where_arr is None or len(where_arr) == 0:
                return
            target_dist = self.get_target_dist(fail_gracefully=True)
            if target_dist is None or target_dist > 1400:
                return
            avg_idx = where_arr.mean(axis=0)
            if avg_idx[0] < half_length:
                if avg_idx[1] < half_length:
                    max_left_movements, max_right_movements, max_up_movements, max_down_movements = [
                            max_movements,0,max_movements,0]
                    
                else:
                    max_left_movements, max_right_movements, max_up_movements, max_down_movements = [
                            0,max_movements,max_movements,0]
            else:
                if avg_idx[1] < half_length:
                    max_left_movements, max_right_movements, max_up_movements, max_down_movements = [
                            max_movements,0,0,max_movements]
                    
                else:
                    max_left_movements, max_right_movements, max_up_movements, max_down_movements = [
                            0,max_movements,0,max_movements]
            self.conditional_move(max_left_movements, max_right_movements, max_up_movements, max_down_movements)
    
    def get_target(self, target_type='crosshairs'):
        pdi.press_key_fast(self.target_closest_enemy_hotkey)
        self.crosshairs_found = False
        if target_type == 'crosshairs':
            img_arr = self.get_crosshairs()
            if self.target is not None:
                self.crosshairs_found = True
        return img_arr
    
    
    def hunt_target(self, target_type='crosshairs'):
        self.gamma_01, self.phi_01 = self.convert_movements_to_angles(self.horizontal_movements_cum, self.vertical_movements_cum)
        self.RDU_lst = []
        _ = self.get_target(target_type=target_type)
        target_dist = self.get_target_dist(fail_gracefully=True)
        if self.target is None or target_dist is None or target_dist > 1200:
            return
        self.get_RDU_0()
        self.RDU_lst.append(self.RDU_0)
        num_none_target = 0
        hunt_start_time = time.time()
        while num_none_target < self.num_none_target_max and time.time() - hunt_start_time < 5:
            self.get_trained_RDU_0()
            self.get_remaining_gamma_phi()
            self.get_aligning_movements()
            self.move_to_align()
            if self.crosshairs_found:
                # Later could also fire when brown_avg found if target is within range (which depends on distance and speed and is usually sooner than the crosshairs light up)
                self.fire_weapon()
            self.horizontal_movements_cum += int(self.horizontal_movements_12)
            self.vertical_movements_cum += int(self.vertical_movements_12)
            self.gamma_01, self.phi_01 = self.convert_movements_to_angles(self.horizontal_movements_cum, self.vertical_movements_cum)
            _ = self.get_target(target_type)
            while self.target is None:
                num_none_target += 1
                if num_none_target >= self.num_none_target_max:
                    break
                _ = self.get_target(target_type)
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

    
    def operate_turret(self):
        time_of_last_reset = time.time()
        while True:
            if time.time() - time_of_last_reset > 600:
                self.reset_station()
                time_of_last_reset = time.time()
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            self.hunt_target(target_type='crosshairs')
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            self.hunt_target_arrow()

        
class Rear_Turret(Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
        super(Rear_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)
        # CONSTANTS
        self.max_horizontal_movements = 507
        self.min_horizontal_movements = -507
        self.max_vertical_movements = 949
        self.min_vertical_movements = -949
        

class Deck_Turret(Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
        super(Deck_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)
        # CONSTANTS
        self.max_horizontal_movements = np.inf
        self.min_horizontal_movements = -np.inf
        #self.max_vertical_movements = 949
        #self.min_vertical_movements = -949
        
        
class Duty_Mission_Turret(Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
        super(Duty_Mission_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)
        
        
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
        time_of_last_reset = time.time()
        while True:
            if time.time() - time_of_last_reset > 600:
                self.reset_station()
                time_of_last_reset = time.time()
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            self.hunt_target(target_type='crosshairs')
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            self.hunt_target_arrow()
            pdi.press_key_fast(self.target_closest_enemy_hotkey)
            
            #self.hunt_target(target_type='brown_avg')

        
class Duty_Mission_Rear_Turret(Duty_Mission_Turret, Rear_Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
        super(Duty_Mission_Rear_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)
        
        
class Duty_Mission_Deck_Turret(Duty_Mission_Turret, Deck_Turret):
    def __init__(self, swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
        super(Duty_Mission_Deck_Turret, self).__init__(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)

        
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
        self.ship_details_armor_value_idx = np.array([549, 815])
        # INITIAL VALUES
        self.active_waypoints_idx = None
        self.active_wp_dct = {'Target_Location': {'idx': None, 'autopilot_to_idx': None}, 'zeros': {'idx': None, 'autopilot_to_idx': None}}
        self.mission_critical_dropdown_idx = None
        self.mission_enemies = [{'idx': None, 'autopilot_to_idx': None, 'target_this_idx': None, 'name': None}]
        self.target_dist_idx = None
        # SETUP
        self.target_mission_enemy_frequency = 0.3
        self.autopilot_to_enemy_frequency = 0.02
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
                pdi.press('v')
                return True
        pdi.press('v')
        return False
            
        
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
        current_dist = self.get_target_dist()
        while current_dist > 1000:
            time.sleep(1)
            if self.get_target_dist() > current_dist:
                # Something is wrong, follow the station
                swg_utils.chat('/tar ' + space_station_name, return_delay=0.3)
                swg_utils.chat('/fol', return_delay=1)
                swg_utils.chat('/throttle 0.01')
            current_dist = self.get_target_dist()
            
            
    def mission_critical_dropdown_gone(self):
        if self.active_waypoints_idx is None:
            active_waypoints_arr = swg_utils.get_search_arr('Active_Waypoints', dir_path=self.dir_path, mask_int=None)
            self.active_waypoints_idx, img_arr = swg_utils.find_arr_on_region(active_waypoints_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=[194,130])
        img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=194,
                    scale_to=255, set_focus=False, sharpen=True)
        
        if self.mission_critical_dropdown_idx is None:
            self.mission_critical_dropdown_idx = [self.active_waypoints_idx[0] - 22, self.active_waypoints_idx[1] - 14]
        if self.mission_critical_dropdown_idx[0] < 0 or self.mission_critical_dropdown_idx[1] < 0:
            raise Exception('Mission Critical window not visible enough or at all.')
        # If 0 then mission critical dropdown arrow is gone (because no more enemies)
        return img_arr[self.mission_critical_dropdown_idx[0], self.mission_critical_dropdown_idx[1]] == 0
    
    
    def get_active_wp_idx(self, active_wp_name):
        get_active_wp_i = 0
        if self.active_wp_dct[active_wp_name]['idx'] is None:
            active_wp_arr = swg_utils.get_search_arr(active_wp_name, dir_path=self.dir_path, mask_int=None)
        while self.active_wp_dct[active_wp_name]['idx'] is None and get_active_wp_i < 2:
            if self.active_waypoints_idx is None:
                start_row = 0
                start_col = 0
            else:
              start_row = self.active_waypoints_idx[0]
              start_col = self.active_waypoints_idx[1]
            self.active_wp_dct[active_wp_name]['idx'], img_arr = swg_utils.find_arr_on_region(active_wp_arr, region=self.swg_region, start_row=start_row, start_col=start_col, fail_gracefully=True, sharpen_threshold=[194,130])
            if self.active_wp_dct[active_wp_name]['idx'] is None:
                if self.active_waypoints_idx is None:
                    active_waypoints_arr = swg_utils.get_search_arr('Active_Waypoints', dir_path=self.dir_path, mask_int=None)
                    self.active_waypoints_idx, img_arr = swg_utils.find_arr_on_region(active_waypoints_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=[194,130])
                # If Active Waypoints dropdown is closed, open it
                self.dropdown_arrow_idx = [self.active_waypoints_idx[0], self.active_waypoints_idx[1] - 4]
                img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=194,
                            scale_to=255, set_focus=False, sharpen=True)
                
                if img_arr[self.dropdown_arrow_idx[0], self.dropdown_arrow_idx[1]] == 0:
                    swg_utils.click(button='left', start_delay=0.02, return_delay=0.3, window=self.swg_window, region=self.swg_region, coords_idx=self.dropdown_arrow_idx, activate_window=False)
                    time.sleep(0.3)
            get_active_wp_i += 1
                    
                    
    def autopilot_to_wp(self, active_wp_name):
        time.sleep(0.2)
        self.get_active_wp_idx(active_wp_name)
        try:
            self.active_wp_clickable_idx = [self.active_wp_dct[active_wp_name]['idx'][0] + 7, self.active_wp_dct[active_wp_name]['idx'][1] + 25]
        except:
            return
        swg_utils.click(button='right', start_delay=0.02, return_delay=0.3, window=self.swg_window, region=self.swg_region, coords_idx=self.active_wp_clickable_idx, activate_window=False)
        if self.active_wp_dct[active_wp_name]['autopilot_to_idx'] is None:
            autopilot_to_arr = swg_utils.get_search_arr('Autopilot_To', dir_path=self.dir_path, mask_int=None)
            self.active_wp_dct[active_wp_name]['autopilot_to_idx'], img_arr = swg_utils.find_arr_on_region(autopilot_to_arr, region=self.swg_region, start_row=max(self.active_wp_dct[active_wp_name]['idx'][0] - 100, 0), start_col=max(self.active_wp_dct[active_wp_name]['idx'][1] - 100, 0), fail_gracefully=False, sharpen_threshold=[194,130])
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
        complete_idx, _ = swg_utils.find_arr_on_region(self.complete_arr, region=self.swg_region, fail_gracefully=True, sharpen_threshold=[194,130])
        if complete_idx is not None:
            swg_utils.click(button='left', start_delay=0.1, return_delay=0.9, window=self.swg_window, region=self.swg_region, coords_idx=complete_idx, activate_window=False, presses=3)
            pdi.press('esc', presses=8)
            pdi.press('n')
            return False
        if self.active_wp_dct['Target_Location']['idx'] is None:
            self.get_active_wp_idx('Target_Location')
        if self.active_wp_dct['Target_Location']['idx'] is None:
            return False
        target_location_arr = swg_utils.get_search_arr('Target_Location', dir_path=self.dir_path, mask_int=None)
        return swg_utils.find_arr_on_region(target_location_arr, region=self.swg_region, start_row=max(self.active_wp_dct['Target_Location']['idx'][0] - 200, 0), start_col=max(self.active_wp_dct['Target_Location']['idx'][1] - 200, 0), fail_gracefully=True, sharpen_threshold=[194,130])[0] is not None
            
    
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
        if self.active_waypoints_idx is None:
            active_waypoints_arr = swg_utils.get_search_arr('Active_Waypoints', dir_path=self.dir_path, mask_int=None)
            self.active_waypoints_idx, img_arr = swg_utils.find_arr_on_region(active_waypoints_arr, region=self.swg_region, fail_gracefully=False, sharpen_threshold=[194,130])
        img_arr = swg_utils.take_grayscale_screenshot(window=self.swg_window, region=self.swg_region, sharpen_threshold=194,
                    scale_to=255, set_focus=False, sharpen=True)
        
        if self.mission_critical_dropdown_idx is None:
            self.mission_critical_dropdown_idx = [self.active_waypoints_idx[0] - 22, self.active_waypoints_idx[1] - 14]
        if self.mission_critical_dropdown_idx[0] < 0 or self.mission_critical_dropdown_idx[1] < 0:
            raise Exception('Mission Critical window not visible enough or at all.')
        return img_arr[self.mission_critical_dropdown_idx[0], self.mission_critical_dropdown_idx[1] + 10] == 255
    
    
    def find_enemy(self, find_task='Autopilot_To'):
        find_task_dct = {'Autopilot_To': {'idx': 'autopilot_to_idx'},
                         'target_this': {'idx': 'target_this_idx'}}
        
        if self.mission_critical_dropdown_gone():
            return
        if not self.mission_critical_dropped_down():
            swg_utils.click(button='left', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
        self.mission_enemies[0]['idx'] = [self.mission_critical_dropdown_idx[0] + 30, self.mission_critical_dropdown_idx[1] + 50]
        swg_utils.click(button='right', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_enemies[0]['idx'], activate_window=False)
        if self.mission_enemies[0][find_task_dct[find_task]['idx']] is None:
            autopilot_to_enemy_arr = swg_utils.get_search_arr(find_task, dir_path=self.dir_path, mask_int=None)
            self.mission_enemies[0][find_task_dct[find_task]['idx']], img_arr = swg_utils.find_arr_on_region(autopilot_to_enemy_arr, region=self.swg_region, start_row=max(self.mission_enemies[0]['idx'][0] - 100, 0), start_col=max(self.mission_enemies[0]['idx'][1] - 100, 0), fail_gracefully=True, sharpen_threshold=[194,130])
            if self.mission_enemies[0][find_task_dct[find_task]['idx']] is None:
                print('Tried to find enemy but couldnt. Possibly the enemy died before getting to click on ', find_task)
                return
        swg_utils.click(button='left', start_delay=0.02, return_delay=0.15, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_enemies[0][find_task_dct[find_task]['idx']], activate_window=False)
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
        
        
    def reset_station(self):
        '''
        Purpose
        -------
        It is suspected that being in the space view too long can cause issues 
        such as the toon is logged out or crashing. A possible remedy is to 
        exit current station and re-enter it.
        '''
        # If you just completed a mission but have not yet clicked the "Complete" button, then leaving pilot station will
        # bug out the completion window such that you cannot click on it anymore.
        if not self.got_mission():
            return
        # Leave pilot station
        pdi.press('l')
        time.sleep(4.5)
        # Enter pilot station
        swg_utils.chat('/pilot')
        time.sleep(4.5)
        
    
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
        prev_dist_to_enemy = 0
        while not self.mission_critical_dropdown_gone():  
            if time.time() - start_time > 40:
                self.autopilot_to_wp('zeros')
                time.sleep(5)
                start_time = time.time()
            if self.mission_critical_dropdown_gone():
                break
            # Target next mission enemy or nearest enemy
            if random.random() < self.target_mission_enemy_frequency:
                # Target next mission enemy
                self.find_enemy(find_task='target_this')
            else:
                # Target nearest enemy
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
            for _ in range(self.num_times_to_click_autopilot_to_enemy):
                dist_to_enemy = self.get_target_dist(fail_gracefully=True)
                if dist_to_enemy is None:
                    continue
                if dist_to_enemy > 2000:
                    autopilot_to_enemy = True
                elif dist_to_enemy > 1000:
                    autopilot_to_enemy = random.random() < self.autopilot_to_enemy_frequency
                else:
                    autopilot_to_enemy = False
                if autopilot_to_enemy:
                    # Possibly disabled, autopilot to the enemy
                    self.find_enemy(find_task='Autopilot_To')
                    swg_utils.chat('/throttle 1.0', start_delay=4)
            # The following is to prevent the situation where the enemy is less than 1000m, but
            # yet stationary for some reason (which would make us stationary as well if also
            # greater than 700m), and so we both sit stationary forever.
            if prev_dist_to_enemy == dist_to_enemy:
                self.autopilot_to_wp('zeros')
                swg_utils.chat('/throttle 1.0', start_delay=4, return_delay=2)
                prev_dist_to_enemy = deepcopy(dist_to_enemy)
        
        
    def pilot_main(self):
        time_of_last_reset = time.time()
        while True:
            if time.time() - time_of_last_reset > 600:
                self.reset_station()
                # CLose out of any windows
                pdi.press('esc', presses=3)
                pdi.press('n')
                time_of_last_reset = time.time()
            if not self.got_mission():
                # CLose out of any windows
                pdi.press('esc', presses=3)
                pdi.press('n')
                time.sleep(1)
                self.get_duty_mission_from_space_station()
            i = 1
            while self.mission_critical_dropdown_gone() and self.got_mission():
                self.autopilot_to_wp('Target_Location')
                if i % 3 == 0:
                    swg_utils.chat('/throttle 1.0')
                    time.sleep(4)
                i += 1
            if not self.got_mission():
                continue
            # Enemies enaging
            if self.mission_critical_dropped_down():
                swg_utils.click(button='left', start_delay=0.02, return_delay=0.1, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
            self.optimize_speed()
            swg_utils.click(button='left', start_delay=0.02, return_delay=0.1, window=self.swg_window, region=self.swg_region, coords_idx=self.mission_critical_dropdown_idx, activate_window=False)
            self.autopilot_to_wp('Target_Location')

    
def main_duty_mission_rear_turret(swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=1):
    turret = Duty_Mission_Rear_Turret(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)
    # For now, assume only need to run commands once (which assumes the ship doesn't get destroyed etc)
    turret.run_bulk_droid_commands()
    turret.operate_turret()


def main_duty_mission_deck_turret(swg_window_i=0, target_closest_enemy_hotkey='j', dir_path=os.path.join(git_path, 'space_ui_dir'), num_none_target_max=25):
    turret = Duty_Mission_Deck_Turret(swg_window_i=swg_window_i, target_closest_enemy_hotkey=target_closest_enemy_hotkey, dir_path=dir_path, num_none_target_max=num_none_target_max)
    # For now, assume only need to run commands once (which assumes the ship doesn't get destroyed etc)
    #turret.run_bulk_droid_commands() # Let rear gunner do it.
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
    
    task_type = config.get_value('space', 'task_type', desired_type=str, required_to_be_in_conf=False, default_value='duty_mission')
    turret_type = config.get_value('space', 'turret_type', desired_type=str, required_to_be_in_conf=False, default_value='None')
    pilot_type = config.get_value('space', 'pilot_type', desired_type=str, required_to_be_in_conf=False, default_value='None')
    main(task_type=task_type, turret_type=turret_type, pilot_type=pilot_type)
    '''
    spacer = Space()
    #spacer.get_red_center_idx()
    start_time = time.time()
    while time.time() - start_time < 0.4:
        target_center_idx = spacer.get_target_center_idx()
    #target_center_idx = spacer.get_target_center_idx()
    print(time.time() - start_time)
    #print(target_center_idx)
    '''