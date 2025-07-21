# -*- coding: utf-8 -*-
import os
import sys
import yaml
from instruments import IdronautD1, IdronautD2, IdronautD3
from general.functions import logger, maintenance, files_in_directory
from functions import copy_files

log = logger("scripts/logs/temperature")
log.initialise("Processing LéXPLORE Idronaut data")

log.begin_stage("Collecting inputs")
with open("scripts/input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

for directory in directories.values():
    if not os.path.exists(directory):
        os.makedirs(directory)

if len(sys.argv) == 1:
    files = files_in_directory(directories["Level0"])
    files.sort()
    log.info("Reprocessing complete dataset from {}".format(directories["Level0"]))
elif len(sys.argv) == 2:
    files = copy_files(os.path.join(directories["Level0"], "Deployment3"), directories["Raw"])
    log.info("Live processing {} files.".format(len(files)))

log.end_stage()

log.begin_stage("Processing data to L1")
for file in files:
    if "Deployment1" in file:
        deployment = "D1"
        sensor = IdronautD1(log=log)
    elif "Deployment2" in file:
        deployment = "D2"
        interpolate = True
        sensor = IdronautD2(log=log)
    elif "Deployment3" in file:
        deployment = "D3"
        interpolate = True
        sensor = IdronautD3(log=log)
    else:
        continue

    if sensor.read_data(file):
        sensor.quality_assurance(file_path="notes/quality_assurance.json")
        sensor.export(directories["Level1"], "L1_LexploreIdronaut_" + deployment)
        sensor.mask_data()
        sensor.profile_to_timeseries_grid(depth_label="Press")
        sensor.export(directories["Level2"], "L2_LexploreIdronaut_" + deployment, output_period="monthly", profile_to_grid=True)
log.end_stage()

log.begin_stage("Applying Idronaut Maintenance Periods")
effected_files = maintenance(directories["Level1"], file="notes/events.csv", datalakes=[])
for file in effected_files:
    deployment = file.split("_")[-3]
    if deployment == "D1":
        sensor = IdronautD1(log=log)
    elif deployment == "D2":
        sensor = IdronautD2(log=log)
    elif deployment == "D3":
        sensor = IdronautD3(log=log)
    else:
        continue
    sensor.read_netcdf_data(file)
    sensor.mask_data()
    sensor.profile_to_timeseries_grid(depth_label="Press")
    sensor.export(directories["Level2"], "L2_LexploreIdronaut_" + deployment, output_period="monthly", profile_to_grid=True, overwrite=True)
log.end_stage()

