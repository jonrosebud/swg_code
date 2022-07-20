# -*- coding: utf-8 -*-
"""
Created on Sun Jul 10 11:16:48 2022

@author: trose
"""

import swg_utils
import swg_window_management as swm
import time
swm.swg_windows[0].set_focus()
time.sleep(4)
swg_utils.stealth_on()
print(swg_utils.stealth_is_on())
swg_utils.stealth_off()