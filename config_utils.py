# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 10:28:26 2021

@author: trose
"""
from configparser import ConfigParser


class Instruct(ConfigParser):
    '''
    This is the class that records the instruction for structural generation
    All of the information is set in the dictionary self.I
    '''
    def __init__(self, config_fpath):
        '''
        config_fpath: str
            Path to .conf file.
            
        Purpose
        -------
        Initialize the ConfigParser object.
        
        Notes
        -----
        A config file is organized like the following example, and has a .conf extension.
        The section names are put in brackets and the options under that section are
        assigned.
        
        [main]
        a = 2
        b = false
        
        [another_section]
        value = 17
        lst = [1, 2, 3]
        char_lst = ['a', 'c']
        '''
        ConfigParser.__init__(self)
        self.read(config_fpath)
        

    def get_value(self, section, option, desired_type=str, required_to_be_in_conf=False, default_value=None):
        '''
        section: str
            Section title in conf file.
            
        option: str
            Variable name under section in conf file.
            
        desired_type: python type function
            This will be the returned type. It must be callable.
            
            e.g. str, int, list, np.array are callable (str(), int()...)
            
        required_to_be_in_conf: bool
            True: raise an error if the option DNE in the given section.
            False: return the default_value if the option DNE in the given section.
            
        default_value: *
            The value to return if the section/option pair is not found in conf file but
            required_to_be_in_conf is False.
            
        Returns
        -------
        the option value with type desired_type.
        
        Purpose
        -------
        Check and see if the section and option exists. If so, return the evaluated and the value
        for the option is required to be in the conf file
        
        Notes
        -----
        1. If providing a bool desired_type, then the option may be true, false without any case sensitivity.
        
        2. This function will use the callable desired_type to cast the type after running the eval function.
            Python will throw an error if this desired_type doesn't work for the option value in the conf file.
        '''
        if self.has_option(section,option):
            value = self.get(section,option)
                
            if desired_type is str:
                return value
            elif desired_type is bool:
                if value.lower() == 'true':
                    return True
                elif value.lower() == 'false':
                    return False
                else:
                    raise ValueError("If present, boolean option must be 'true' or 'false' (non-case-sensitive).",
                            'section:', section, 'option:', option)
            else:
                return desired_type(eval(value))
                
        elif not required_to_be_in_conf:
            # default to False
            return default_value
        else:
            raise ValueError('required_to_be_in_conf is True but the option/section pair was not found in the conf file.',
                        'section:', section, 'option:', option)
            

    def get_config_dct(self):
        '''
        Returns
        -------
        None

        Purpose
        -------
        Read a .conf file and store a key into a dictionary (config_dct) for every section in
        the conf file. The value is a dictionary where the keys are the option
        names and the values are the python-evaluated values.
        
        Method
        ------
        1. Attempts to discern whether the option value is a bool or None and if
            so will use the appropriate value.
            
        2. If not a bool or None then this function will attempt to use the
            eval function on the value. If successful, use that value,
            otherwise, the value was likely supposed to be a string and
            so is left a string.
        '''
        self.config_dct = {}
        for section in self.sections():
            section_dct = {}
            for option in self.options(section):
                value = self.get(section, option)
                if value.lower() == 'true':
                    section_dct[option] = True
                    continue
                elif value.lower() == 'false':
                    section_dct[option] = False
                    continue
                elif value.lower() == 'none':
                    section_dct[option] = None
                    continue
                try:
                    value = eval(value)
                except:
                    pass
                section_dct[option] = value
            self.config_dct[section] = section_dct