# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 21:50:52 2021

@author: rosebud
"""

import time
import pydirectinput


pydirectinput.keyDown('alt')
pydirectinput.press('tab')
pydirectinput.keyUp('alt')
time.sleep(1)

# pydirectinput.press('i')
time.sleep(.5)

# window 1
# 6,4,5,3
pydirectinput.rightClick(500, 680)  # right click at x, y coordinates
pydirectinput.press('6')
time.sleep(.2)
pydirectinput.rightClick(500, 680)  # right click at x, y coordinates
pydirectinput.press('4')
time.sleep(.2)
pydirectinput.rightClick(500, 680)  # right click at x, y coordinates
pydirectinput.press('5')
time.sleep(.2)
pydirectinput.rightClick(500, 680)  # right click at x, y coordinates
pydirectinput.press('3')
time.sleep(.2)

# window 2
# 6,4,5,3
pydirectinput.rightClick(1525, 680)  # right click at x, y coordinates
pydirectinput.press('6')
time.sleep(.2)
pydirectinput.rightClick(1525, 680)  # right click at x, y coordinates
pydirectinput.press('4')
time.sleep(.2)
pydirectinput.rightClick(1525, 680)  # right click at x, y coordinates
pydirectinput.press('5')
time.sleep(.2)
pydirectinput.rightClick(1525, 680)  # right click at x, y coordinates
pydirectinput.press('3')
time.sleep(.2)

# window 3
# 6,4,5,3
pydirectinput.rightClick(2550, 680)  # right click at x, y coordinates
pydirectinput.press('6')
time.sleep(.2)
pydirectinput.rightClick(2550, 680)  # right click at x, y coordinates
pydirectinput.press('4')
time.sleep(.2)
pydirectinput.rightClick(2550, 680)  # right click at x, y coordinates
pydirectinput.press('5')
time.sleep(.2)
pydirectinput.rightClick(2550, 680)  # right click at x, y coordinates
pydirectinput.press('3')
time.sleep(.2)


time.sleep(.5)
pydirectinput.keyDown('alt')
pydirectinput.press('esc')
pydirectinput.keyUp('alt')