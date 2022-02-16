# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 15:43:12 2021

@author: trose
"""

import pandas as pd
import os
import numpy as np

for component_type in ['armor', 'booster', 'capacitor', 'droid_interface', 'engine', 'reactor', 'shield', 'weapon']:
    stc_fpath = os.path.join(r'D:\python_scripts\swg\STC', component_type + '_stc.csv')
    stc_df = pd.read_csv(stc_fpath, dtype=np.float)
    stc_df.dropna(inplace=True)
    stc_df.loc[:, 'stc_percentile'] = stc_df.stc_percentile.values.astype(int)
    stc_df = stc_df.replace({'stc_percentile': {95: 0.95, 96: 0.96, 97: 0.97, 98: 0.98, 99: 0.99, 100: 0.999, 101: 0.9999, 102: 0.99999}})
    stc_df.to_csv(stc_fpath, index=False)