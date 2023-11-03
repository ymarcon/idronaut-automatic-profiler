# -*- coding: utf-8 -*-
import os
import math
import json
import warnings
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from datetime import datetime, timedelta, timezone
from general.functions import GenericInstrument, json_converter


class IdronautD1(GenericInstrument):
    def __init__(self, *args, **kwargs):
        super(IdronautD1, self).__init__(*args, **kwargs)
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
            'Chl2': {'var_name': 'Chl2', 'dim': ('time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'PhycoEr': {'var_name': 'PhycoEr', 'dim': ('time',), 'unit': '', 'long_name': 'phycoerythrin'},
            'PhycoCy': {'var_name': 'PhycoCy', 'dim': ('time',), 'unit': '', 'long_name': 'phycocyanin'}
        }

        self.grid_dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            'Press': {'dim_name': 'Press', 'dim_size': None}
        }

        self.grid_variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00',
                     'long_name': 'time'},
            'Press': {'var_name': 'Press', 'dim': ('Press',), 'unit': 'm', 'long_name': 'Pressure'},
            'Temp': {'var_name': 'Temp', 'dim': ('Press', 'time',), 'unit': 'degC', 'long_name': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('Press', 'time',), 'unit': 'mS/cm', 'long_name': 'conductivity'},
            'Cond20': {'var_name': 'Cond20', 'dim': ('Press', 'time',), 'unit': 'mS/cm', 'long_name': 'conductivity at 20deg'},
            'Sal': {'var_name': 'Sal', 'dim': ('Press', 'time',), 'unit': 'ppt', 'long_name': 'salinity'},
            'OPTO%': {'var_name': 'OPTO%', 'dim': ('Press', 'time',), 'unit': '%', 'long_name': 'oxygen saturation'},
            'OPTOppm': {'var_name': 'OPTOppm', 'dim': ('Press', 'time',), 'unit': 'ppm', 'long_name': 'oxygen concentration'},
            'pH': {'var_name': 'pH', 'dim': ('Press', 'time',), 'unit': '', 'long_name': 'pH'},
            'eH': {'var_name': 'eH', 'dim': ('Press', 'time',), 'unit': 'mV', 'long_name': 'Potential Redox'},
            'PAR': {'var_name': 'PAR', 'dim': ('Press', 'time',), 'unit': 'Wm-2',
                    'long_name': 'photosynthetically active radiation'},
            'Chl': {'var_name': 'Chl', 'dim': ('Press', 'time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'Chl2': {'var_name': 'Chl2', 'dim': ('Press', 'time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'PhycoEr': {'var_name': 'PhycoEr', 'dim': ('Press', 'time',), 'unit': '', 'long_name': 'phycoerythrin'},
            'PhycoCy': {'var_name': 'PhycoCy', 'dim': ('Press', 'time',), 'unit': '', 'long_name': 'phycocyanin'}
        }
        self.depths = np.concatenate((np.linspace(0, 30, 151), np.linspace(30.5, 90, 60)))

    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, delim_whitespace=True)
            df.columns = ['Press', 'Temp', 'Cond', 'Sal', 'O2%', 'O2ppm', 'pH', 'eH', 'PAR', 'OPTO%', 'OPTOppm', 'Chl', 'PhycoEr', 'PhycoCy', 'ACQ.', 'DATE', '&', 'TIME']
            df['time'] = list(pd.to_datetime(df["ACQ."] + " " + df["DATE"], format='%d/%m/%Y %H:%M:%S.%f', utc=True).values.astype(float) / 10 ** 9)
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
            raise e
        return True


class IdronautD2(GenericInstrument):
    def __init__(self, *args, **kwargs):
        super(IdronautD2, self).__init__(*args, **kwargs)
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
            'Chl2': {'var_name': 'Chl2', 'dim': ('time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'PhycoEr': {'var_name': 'PhycoEr', 'dim': ('time',), 'unit': '', 'long_name': 'phycoerythrin'},
            'PhycoCy': {'var_name': 'PhycoCy', 'dim': ('time',), 'unit': '', 'long_name': 'phycocyanin'}
        }

        self.grid_dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            'Press': {'dim_name': 'Press', 'dim_size': None}
        }

        self.grid_variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00',
                     'long_name': 'time'},
            'Press': {'var_name': 'Press', 'dim': ('Press',), 'unit': 'm', 'long_name': 'Pressure'},
            'Temp': {'var_name': 'Temp', 'dim': ('Press', 'time',), 'unit': 'degC', 'long_name': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('Press', 'time',), 'unit': 'mS/cm', 'long_name': 'conductivity'},
            'Cond20': {'var_name': 'Cond20', 'dim': ('Press', 'time',), 'unit': 'mS/cm',
                       'long_name': 'conductivity at 20deg'},
            'Sal': {'var_name': 'Sal', 'dim': ('Press', 'time',), 'unit': 'ppt', 'long_name': 'salinity'},
            'OPTO%': {'var_name': 'OPTO%', 'dim': ('Press', 'time',), 'unit': '%', 'long_name': 'oxygen saturation'},
            'OPTOppm': {'var_name': 'OPTOppm', 'dim': ('Press', 'time',), 'unit': 'ppm',
                        'long_name': 'oxygen concentration'},
            'pH': {'var_name': 'pH', 'dim': ('Press', 'time',), 'unit': '', 'long_name': 'pH'},
            'eH': {'var_name': 'eH', 'dim': ('Press', 'time',), 'unit': 'mV', 'long_name': 'Potential Redox'},
            'PAR': {'var_name': 'PAR', 'dim': ('Press', 'time',), 'unit': 'Wm-2',
                    'long_name': 'photosynthetically active radiation'},
            'Chl': {'var_name': 'Chl', 'dim': ('Press', 'time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'Chl2': {'var_name': 'Chl2', 'dim': ('Press', 'time',), 'unit': 'µg/L', 'long_name': 'chlorophyll A'},
            'PhycoEr': {'var_name': 'PhycoEr', 'dim': ('Press', 'time',), 'unit': '', 'long_name': 'phycoerythrin'},
            'PhycoCy': {'var_name': 'PhycoCy', 'dim': ('Press', 'time',), 'unit': '', 'long_name': 'phycocyanin'}
        }
        self.depths = np.concatenate((np.linspace(0, 30, 151), np.linspace(30.5, 90, 60)))

    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, delim_whitespace=True)
            df.columns = ['Press', 'Temp', 'Cond', 'Cond20', 'OPTO%', 'OPTOppm', 'pH', 'eH', 'Chl2', 'Chl', 'PhycoEr', 'PhycoCy', 'ACQ.', 'DATE', '&', 'TIME']
            df['time'] = list(pd.to_datetime(df["ACQ."] + " " + df["DATE"], format='%d/%m/%Y %H:%M:%S.%f', utc=True).values.astype(float) / 10 ** 9)
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
            raise e
        return True
