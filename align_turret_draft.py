# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 20:05:27 2022

@author: timcr
"""
import numpy as np

def get_RDU_1(crosshairs):
    row = crosshairs[0]
    col = crosshairs[1]
    return (np.array([
        (row - 515.0) / 892.006,
        1.0,
        (202.0 - col) / 1241.45
        ])
        / np.sqrt(
1.0 + ((row - 515.0)**2) / 795675.0 + ((202.0 - col)**2) / 1541197.0))


def rotate_about_z_axis(vector, theta):
    return np.dot(np.array([
[np.cos(theta), np.sin(theta), 0],
[-np.sin(theta), np.cos(theta), 0],
[0, 0, 1]
]), vector)


def rotate_point_about_axis_by_angle(point, axis, theta):
    a = np.cos(theta / 2.0)
    b = np.sin(theta / 2.0) * point[0]
    c = np.sin(theta / 2.0) * point[1]
    d = np.sin(theta / 2.0) * point[2]
    rotation_matrix = np.array([
[(a**2) + (b**2) - (c**2) - (d**2), 2.0 * b * c - 2.0 * a * d, 2.0 * b * d + 2.0 * a * c],
[2.0 * b * c + 2.0 * a * d, (a**2) - (b**2) + (c**2) - (d**2), 2.0 * c * d - 2.0 * a * b],
[2.0 * b * d - 2.0 * a * c, 2.0 * c * d + 2.0 * a * b, (a**2) - (b**2) - (c**2) + (d**2)]
])
    return np.dot(rotation_matrix, point)


def get_RDU_0(crosshairs, gamma_01, phi_01):
    RDU_1 = get_RDU_1(crosshairs)
    RDU_1_gamma_rotated = rotate_about_z_axis(RDU_1, gamma_01)
    rotated_x_axis = np.array([np.cos[gamma_01], np.sin(gamma_01), 0.0])
    return rotate_point_about_axis_by_angle(RDU_1_gamma_rotated, rotated_x_axis, phi_01)


def arctan_0(vector):
    x = float(vector[0])
    y = float(vector[1])
    if x == 0 and y == 0:
        return 0
    if x >= 0:
        return np.arctan((y / x) - (np.pi / 2.0))
    else:
        return np.arctan((y / x) + (np.pi / 2.0))


def get_remaining_gamma_phi(RDU_0, gamma_01, phi_01):
    gamma_02 = np.arcsin(RDU_0[2])
    phi_02 = arctan_0(RDU_0)
    gamma_12 = gamma_02 - gamma_01
    phi_12 = phi_02 - phi_01
    return gamma_12, phi_12


def convert_angles_to_movements(gamma, phi):
    pass
    # return horizontal_movements, vertical_movements
    
    
def convert_movements_to_angles(horizontal_movements, vertical_movements):
    pass
    # return gamma_01, phi_01
    

def get_aligning_movements(gamma_01, phi_01, gamma_12, phi_12):
    max_horizontal_movements = 
    min_horizontal_movements = 
    max_vertical_movements = 
    min_vertical_movements = 
    horizontal_movements_01, vertical_movements_01 = convert_angles_to_movements(gamma_01, phi_01)
    horizontal_movements_12, vertical_movements_12 = convert_angles_to_movements(gamma_12, phi_12)
    if horizontal_movements_12 > 0:
        horizontal_movements_12 = min(horizontal_movements_12, max_horizontal_movements - horizontal_movements_01)
    else:
        horizontal_movements_12 = max(horizontal_movements_12, min_horizontal_movements - horizontal_movements_01)
    if vertical_movements_12 > 0:
        vertical_movements_12 = min(vertical_movements_12, max_vertical_movements - vertical_movements_01)
    else:
        vertical_movements_12 = max(vertical_movements_12, min_vertical_movements - vertical_movements_01)
    return int(horizontal_movements_12), int(vertical_movements_12)


def get_trained_RDU_0(RDU_lst):
    p = 2.0 * RDU_lst[1] - RDU_lst[0]
    return p / np.linalg.norm(p)


def main():
    horizontal_movements_cum, vertical_movements_cum = 0, 0
    gamma_01 = np.pi / 2.0
    phi_01 = 0.0
    RDU_lst = []
    for _ in range(2):
        crosshairs = get_crosshairs()
        if crosshairs is None:
            return
        RDU_lst.append(get_RDU_0(crosshairs, gamma_01, phi_01))
    num_none_crosshairs_max = 5
    num_none_crosshairs = 0
    while num_none_crosshairs < num_none_crosshairs_max:
        RDU_0 = get_trained_RDU_0(RDU_lst)
        gamma_12, phi_12 = get_remaining_gamma_phi(RDU_0, gamma_01, phi_01)
        horizontal_movements, vertical_movements = get_aligning_movements(gamma_01, phi_01, gamma_12, phi_12)
        move_and_fire(horizontal_movements, vertical_movements)
        horizontal_movements_cum += horizontal_movements
        vertical_movements_cum += vertical_movements
        gamma_01, phi_01 = convert_movements_to_angles(horizontal_movements_cum, vertical_movements_cum)
        crosshairs = get_crosshairs()
        while crosshairs is None:
            num_none_crosshairs += 1
            if num_none_crosshairs >= num_none_crosshairs_max:
                break
            crosshairs = get_crosshairs()
        if num_none_crosshairs >= num_none_crosshairs_max:
            break
        num_none_crosshairs = 0
        del RDU_lst[0]
        RDU_lst.append(get_RDU_0(crosshairs, gamma_01, phi_01))
    
    
if __name__ == '__main__':
    main()