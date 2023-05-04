import pandas as pd
import numpy as np
import pickle as pkl
import os
import matplotlib.pyplot as plt
from time import sleep

from frghardware.plqy.sr830 import SR830
from frghardware.plqy.ldc502 import LDC502
from frghardware.plqy.ell6_slider import FilterSlider
from frghardware.plqy.stepper_control import Stepper

from tqdm.auto import tqdm
import requests
import io
import json

class PLQY:

    """The control class for taking PLQY using the integrating sphere and lock-in
    amplifier in SERF156.
    """
    def __init__(self, emission_wl):
        """init for the PLQY class

        Args:
            emission_wl (float): mean emisssion wavelength of the sample
        """

        self.filterslider = FilterSlider('COM19')
        print('\nConnected to Filter Slider')

        self.lia = SR830('GPIB0::8::INSTR') # connect to the lock-in amplifier
        print('\nConnected to Lock-in Amplifier')

        self.ldc = LDC502('COM24')
        print('\nConnected to Laser Diode Driver')

        self.stepper = Stepper('COM23')
        print('\nConnected to Stepper Motor')
        
        self.scan_types = {
            'in_lp' : '\nPut sample in beam',
            'in_nolp' : '\nKeep sample in beam, remove longpass',
            'out_lp' : '\nPut sample out of beam',
            'out_nolp' : '\nKeep sample out of beam, remove longpass',
            'empty_lp' : '\nRemove sample from integrating sphere',
            'empty_nolp' : '\nKeep sample out of integrating sphere, remove longpass'
        }

        self.sample_wl = emission_wl
        self.sample_resp = self._get_responsivity(self.sample_wl)

        self.laser_wl = 532
        self.laser_resp = self._get_responsivity(self.laser_wl)

        self.plus_minus = u"\u00B1" # this is the plus/minus unicode symbol. Makes printing this character easier
        self.data = {}

        self.frequency = self.lia.frequency
        self.peak_voltage = self.lia.sine_voltage*(2**0.5)
        self.laser_current = self.ldc.get_laser_current()
        self.laser_temp = self.ldc.get_laser_temp()
        self.time_constant = self.lia.time_constant
        self.sensitivity  = self.lia.sensitivity

        self.stage_positions = {
            'in' :  0.0,
            'out' : 10.0,
            'empty' : 30.0
        }
        self.LASERSTABILIZETIME = 30.0

    def _take_meas(self, sample_name, scan_type, n_avg, time_constant):

        self.lia.time_constant = time_constant
        sleep(15*time_constant)

        self.lia.quick_range()
        sleep(15*time_constant)

        if self.lia.sensitivity == 2e-9:
            print('QuickRange failed, trying again...')
            self.lia.quick_range()

            if self.lia.sensitivity != 2e-9:
                print('Sensitivity is now: ', self.lia.sensitivity)
            else:
                print('QuickRange failed a second time, setting sensitivity to 1V')
                self.lia.sensitivity = 1

        raw = []
        with tqdm(total=n_avg, position=0, leave=True) as pbar:
            for m in tqdm(range(n_avg), position = 0, leave = True):
                raw.append(self.lia.get_magnitude())
                sleep(time_constant)
                pbar.update() 

        self.data[sample_name][scan_type] = np.array(raw)
    

    def take_PLQY(self, sample_name, max_current = 400.0, n_avg = 15, time_constant = 0.03, frequency_setpt = 993.0):

        voltage_setpt, current_setpt = self.current_mod(max_current)
        self.lia.sine_voltage = voltage_setpt
        self.lia.frequency = frequency_setpt

        print('\nSetting Laser Current and waiting to stabilize...')
        if np.abs(self.ldc.get_laser_current() - current_setpt) > 10:
            self.ldc.set_laserCurrent(current_setpt)
            sleep(self.LASERSTABILIZETIME)
        else:
            self.ldc.set_laserCurrent(current_setpt)

        print('\nLaser Current Set and Stable.')

        self.data[sample_name] = {}
        # os.mkdir(os.path.join(os.getcwd(), sample_name))

        for scan_type in self.scan_types.keys():

            if '_lp' in scan_type:
                self.filterslider.right()
            elif '_nolp' in scan_type:
                self.filterslider.left()
            else:
                pass

            if 'in_lp' in scan_type:
                self.stepper.moveto(self.stage_positions['in'])
                sleep(6)
            elif 'out_lp' in scan_type:
                self.stepper.moveto(self.stage_positions['out'])
                sleep(2)
            elif 'empty_lp' in scan_type:
                self.stepper.moveto(self.stage_positions['empty'])
                sleep(4)
            else:
                pass

            self._take_meas(sample_name, scan_type, n_avg, time_constant)
            self.filterslider.right()

        metadata = {
          'frequency': self.lia.frequency,
          'sine_voltage': self.lia.sine_voltage,
          'time_constant': self.lia.time_constant,
          'laser_current': self.ldc.get_laser_current(),
          'laser_temp': self.ldc.get_laser_temp()
        }
        self.data[sample_name]['metadata'] = metadata
        self.data[sample_name]['plqy'], self.data[sample_name]['plqy_error'] = self._calc_plqy(self.data[sample_name])

        temp = pd.DataFrame()
        for k in self.scan_types.keys():
            temp[k] = self.data[sample_name][k]
        temp.to_csv(f'{sample_name}.csv', index = False)

        with open(f'{sample_name}.json', 'w') as f:
            json.dump(metadata, f, indent=4)


    def current_mod(self, max_current):
        turn_on = 294.3
        diff = max_current-turn_on
        setpoint = 0.5*(turn_on+max_current)
        voltage = (2**-0.5)*(diff*0.5)/100
        return voltage, setpoint

    def _calc_plqy(self, data):
        """A function to calculate the PLQY based in a publication by de Mello et al.
        The most widely used method for calculating PLQY.
        https://doi.org/10.1002/adma.19970090308

        Args:
            data (dict): a dictionary containing the data. Data will be an atttribute of self

        Returns:
            tuple: (PLQY, PLQY error), reported as fractional, not percentage
        """

        E_in = data['in_lp'].mean()
        E_in_err = data['in_lp'].std()/E_in

        E_out = data['out_lp'].mean()
        E_out_err = data['out_lp'].std()/E_out

        X_in = data['in_nolp'].mean() - E_in
        X_in_err = (data['in_nolp'].std()/X_in) + E_in_err

        X_out = data['out_nolp'].mean() - E_out
        X_out_err = (data['out_nolp'].std()/X_out) + E_out_err

        X_empty = data['empty_nolp'].mean() - data['empty_lp'].mean()
        X_empty_err = (data['empty_nolp'].std()/data['empty_nolp'].mean()) + (data['empty_lp'].std()/data['empty_lp'].mean())

        E_in = E_in*(self.sample_wl/self.sample_resp)
        E_out = E_out*(self.sample_wl/self.sample_resp)

        X_in = X_in*(self.laser_wl/self.laser_resp)
        X_out = X_out*(self.laser_wl/self.laser_resp)
        X_empty = X_empty*(self.laser_wl/self.laser_resp)

        a = (X_out-X_in)/X_out
        a_err = np.sqrt(((X_out_err + X_in_err)**2) + (X_out_err**2))

        plqy = (E_in-(1-a)*E_out)/(X_empty*a)
        plqy_err = np.sqrt((E_in_err**2) + ((E_out_err + a_err)**2) + (X_empty_err**2))
        print(f"PLQY = {plqy}{self.plus_minus}{plqy_err}")

        return plqy, plqy_err*plqy

    def _get_responsivity(self, emission_wl):
        """internal function to get the respnsivity of the detector at the emission wavelength

        Args:
            emission_wl (float): the mean emission wavelength of the sample

        Returns:
            float: the responsivity, arbitrary units
        """
        try: # check to make sure the file is in the directory
            # url = "https:/raw.githubusercontent.com/fenning-research-group/Python-Utilities/master/FrgTools/frgtools/Detector_Responsivity.csv"
            # download = requests.get(url).content
            fid = 'C:\\Users\\PVGroup\\Documents\\GitHub\\Python-Utilities\\FrgTools\\frgtools\\Detector_Responsivity.csv'
            # resp = pd.read_csv(url)
            resp = pd.read_csv(fid)


            return float(resp['Responsivity'][resp['Wavelength'] == emission_wl])

        except: # if not, tell the user to do so
            print(f'Detector_Responsivity.csv not able to load...check download link in code or internet connectivity:\n{url}')



    # def save(self):
    #     """Save the raw data from each sample to an individual '.csv' file for later use
    #     """
    #     for k in self.data.keys():
    #         temp = pd.DataFrame()
    #         for kk in self.data[k].keys():
    #             if 'plqy' not in kk:
    #                 temp[kk] = self.data[k][kk]
    #             temp.to_csv(f'{k}.csv', index = False)