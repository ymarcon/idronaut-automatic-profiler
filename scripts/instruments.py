# -*- coding: utf-8 -*-
import os
import math
import json
import warnings
import numpy as np
import pandas as pd
import pylake
from scipy.interpolate import griddata
from datetime import datetime, timedelta, timezone
from general.functions import GenericInstrument, json_converter


class Idronaut(GenericInstrument):
    def __init__(self, *args, **kwargs):
        super(Idronaut, self).__init__(*args, **kwargs)
        self.general_attributes = {
            "institution": "EPFL",
            "source": "Idronaut",
            "references": "LéXPLORE common instruments Fabio.DosSantosCorreia@unige.ch>",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "Data from Idronaut profiler on Lexplore Platform in Lake Geneva",
            "title": "Lexplore Idronaut CTD"
        }

        self.dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None}
        }

        self.variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00',
                     'long_name': 'time'},
            'depth': {'var_name': 'depth', 'dim': ('time',), 'unit': 'm', 'long_name': 'water depth'},
            'Press': {'var_name': 'Press', 'dim': ('time',), 'unit': 'dbar', 'long_name': 'Pressure'},
            'Temp': {'var_name': 'Temp', 'dim': ('time',), 'unit': 'degC', 'long_name': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('time',), 'unit': 'mS/cm', 'long_name': 'conductivity'},
            'Cond20': {'var_name': 'Cond20', 'dim': ('time',), 'unit': 'mS/cm', 'long_name': 'conductivity at 20deg'},
            'Sal': {'var_name': 'Sal', 'dim': ('time',), 'unit': 'ppt', 'long_name': 'salinity'},
            'O2pc': {'var_name': 'O2pc', 'dim': ('time',), 'unit': '%', 'long_name': 'oxygen saturation'},
            'O2ppm': {'var_name': 'O2ppm', 'dim': ('time',), 'unit': 'ppm', 'long_name': 'oxygen concentration'},
            'OPTO%': {'var_name': 'OPTO%', 'dim': ('time',), 'unit': '%', 'long_name': 'oxygen saturation'},
            'OPTOppm': {'var_name': 'OPTOppm', 'dim': ('time',), 'unit': 'ppm', 'long_name': 'oxygen concentration'},
            'pH': {'var_name': 'pH', 'dim': ('time',), 'unit': '', 'long_name': 'pH'},
            'eH': {'var_name': 'eH', 'dim': ('time',), 'unit': 'mV', 'long_name': 'Potential Redox'},
            'PAR': {'var_name': 'PAR', 'dim': ('time',), 'unit': 'Wm-2',
                    'long_name': 'photosynthetically active radiation'},
            'Chl': {'var_name': 'Chl', 'dim': ('time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'Turb': {'var_name': 'Turb', 'dim': ('time',), 'unit': 'FTU', 'long_name': 'Turbidity'},
            'Chl2': {'var_name': 'Chl2', 'dim': ('time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'PhycoEr': {'var_name': 'PhycoEr', 'dim': ('time',), 'unit': '', 'long_name': 'phycoerythrin'},
            'PhycoCy': {'var_name': 'PhycoCy', 'dim': ('time',), 'unit': '', 'long_name': 'phycocyanin'}
        }

        self.grid_dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            'depth': {'dim_name': 'depth', 'dim_size': None}
        }

        self.grid_variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00',
                     'long_name': 'time'},
            'depth': {'var_name': 'depth', 'dim': ('depth',), 'unit': 'm', 'long_name': 'water depth'},
            'Temp': {'var_name': 'Temp', 'dim': ('depth', 'time',), 'unit': 'degC', 'long_name': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('depth', 'time',), 'unit': 'mS/cm', 'long_name': 'conductivity'},
            'Cond20': {'var_name': 'Cond20', 'dim': ('depth', 'time',), 'unit': 'mS/cm', 'long_name': 'conductivity at 20deg'},
            'Sal': {'var_name': 'Sal', 'dim': ('depth', 'time',), 'unit': 'ppt', 'long_name': 'salinity'},
            'OPTO%': {'var_name': 'OPTO%', 'dim': ('depth', 'time',), 'unit': '%', 'long_name': 'oxygen saturation'},
            'OPTOppm': {'var_name': 'OPTOppm', 'dim': ('depth', 'time',), 'unit': 'ppm', 'long_name': 'oxygen concentration'},
            'pH': {'var_name': 'pH', 'dim': ('depth', 'time',), 'unit': '', 'long_name': 'pH'},
            'eH': {'var_name': 'eH', 'dim': ('depth', 'time',), 'unit': 'mV', 'long_name': 'Potential Redox'},
            'PAR': {'var_name': 'PAR', 'dim': ('depth', 'time',), 'unit': 'Wm-2',
                    'long_name': 'photosynthetically active radiation'},
            'Chl': {'var_name': 'Chl', 'dim': ('depth', 'time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'Turb': {'var_name': 'Turb', 'dim': ('depth', 'time',), 'unit': 'FTU', 'long_name': 'Turbidity'},
            'Chl2': {'var_name': 'Chl2', 'dim': ('depth', 'time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'PhycoEr': {'var_name': 'PhycoEr', 'dim': ('depth', 'time',), 'unit': '', 'long_name': 'phycoerythrin'},
            'PhycoCy': {'var_name': 'PhycoCy', 'dim': ('depth', 'time',), 'unit': '', 'long_name': 'phycocyanin'}
        }
        self.depths = depths = np.concatenate((np.arange(1.4, 30.01, 0.2),np.arange(30.5, 90.01, 0.5)))

    def compute_physical_quantities(self, bathymetry_file="notes/bathymetry.csv"):

        # Pylake
        new_variables = ['mixed_layer_depth', 'thermocline_depth']
        new_units = ['m', 'm']

        for variable, unit in zip(new_variables, new_units):
            self.grid_variables[variable] = {'var_name': variable, 'dim': ('time',), 'unit': unit, 'long_name': variable}
        
        # Check if there are any non-NaN values at depth < 2 m and > 55 m
        has_shallow_data = np.any(~np.isnan(self.grid['Temp'][self.depths <= 2]))
        has_deep_data = np.any(~np.isnan(self.grid['Temp'][self.depths > 55]))

        # Find the indices of non-NaN values
        non_nan_indices = np.where(~np.isnan(self.grid['Temp']))[0]
        if non_nan_indices.size > 0:
            last_valid_index = non_nan_indices[-1]

        if has_shallow_data and has_deep_data:
            self.log.info("Computing physical quantities for profile", indent=2)
            hTH = pylake.robust_thermocline(self.grid['Temp'], self.depths, s=0.2) # Could use measured salinity, but does not seem reliable and mixing depth is not significantly influenced by salinity here
            
            if hTH < min(self.depths):
                hTH = np.nan
            if hTH > max(self.depths):
                hTH = np.nan

            hML = pylake.mixed_layer(self.grid['Temp'], self.depths, s=0.2, threshold=0.01)

            self.grid["thermocline_depth"] = hTH
            self.grid["mixed_layer_depth"] = hML
        else:
            self.log.warning("Profile is short. Products will not be calculated.", indent=2)
            self.grid["thermocline_depth"] = np.nan
            self.grid["mixed_layer_depth"] = np.nan

class IdronautD1(Idronaut):
    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, sep=r"\s+")
            if len(df) < 10:
                self.log.info("File too short, skipping.".format(file), 2)
                return False
            df.columns = ['Press', 'Temp', 'Cond', 'Sal', 'O2%', 'O2ppm', 'pH', 'eH', 'PAR', 'OPTO%', 'OPTOppm', 'Chl', 'PhycoEr', 'PhycoCy', 'ACQ.', 'DATE', '&', 'TIME']
            df['time'] = list(pd.to_datetime(df["ACQ."] + " " + df["DATE"], format='%d/%m/%Y %H:%M:%S.%f', utc=True).values.astype(float) / 10 ** 9)
            df['depth'] = df['Press']/0.981
            df = df.sort_values(by=['time'])
            empty = np.empty((len(df)))
            empty[:] = np.nan
            for variable in self.variables:
                if variable in df.columns:
                    self.data[variable] = np.array(df[variable].values)
                else:
                    self.data[variable] = empty.copy()
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            return False
        return True


class IdronautD2(Idronaut):
    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, sep=r"\s+")
            if len(df) < 10:
                self.log.info("File too short, skipping.".format(file), 2)
                return False
            df.columns = ['Press', 'Temp', 'Cond', 'Cond20', 'OPTO%', 'OPTOppm', 'pH', 'eH', 'Chl2', 'Chl', 'PhycoEr', 'PhycoCy', 'ACQ.', 'DATE', '&', 'TIME']
            df['time'] = list(pd.to_datetime(df["ACQ."] + " " + df["DATE"], format='%d/%m/%Y %H:%M:%S.%f', utc=True).values.astype(float) / 10 ** 9)
            df['depth'] = df['Press']/0.981
            df = df.sort_values(by=['time'])
            df["Cond"] = df["Cond"] / 1000
            df["Cond20"] = df["Cond20"] / 1000
            if df["time"].iloc[0] > 1750255488:
                df["OPTO%"] = (df["OPTO%"] / 29).round(1)
            empty = np.empty((len(df)))
            empty[:] = np.nan
            for variable in self.variables:
                if variable in df.columns:
                    self.data[variable] = np.array(df[variable].values)
                else:
                    self.data[variable] = empty.copy()
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            return False
        return True


class IdronautD3(Idronaut):
    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, sep=r"\s+")
            if len(df) < 10:
                self.log.info("File too short, skipping.".format(file), 2)
                return False
            df.columns = ['Press', 'Temp', 'Cond', 'Cond20', 'OPTO%', 'OPTOppm', 'pH', 'eH', 'Chl2', 'Turb', 'Chl', 'PhycoEr', 'PhycoCy', 'ACQ.', 'DATE', '&', 'TIME']
            df['time'] = list(pd.to_datetime(df["ACQ."] + " " + df["DATE"], format='%d/%m/%Y %H:%M:%S.%f', utc=True).values.astype(float) / 10 ** 9)
            df['depth'] = df['Press']/0.981
            df = df.sort_values(by=['time'])
            df["Cond"] = df["Cond"] / 1000
            df["Cond20"] = df["Cond20"] / 1000
            empty = np.empty((len(df)))
            empty[:] = np.nan
            for variable in self.variables:
                if variable in df.columns:
                    self.data[variable] = np.array(df[variable].values)
                else:
                    self.data[variable] = empty.copy()
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            return False
        return True
