# -*- coding: utf-8 -*-
import os
import sys
import yaml
import json
import time
import argparse
import requests
from instruments import IdronautD1, IdronautD2, IdronautD3
from general.functions import logger, files_in_directory
from functions import retrieve_new_files

def main(server=False, logs=False):
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if logs:
        log = logger(os.path.join(repo, "logs/idronaut"))
    else:
        log = logger()
    log.initialise("Processing LéXPLORE Idronaut data")
    directories = {f: os.path.join(repo, "data", f) for f in ["Level0", "Level1", "Level2"]}
    for directory in directories:
        os.makedirs(directories[directory], exist_ok=True)
    edited_files = []

    log.begin_stage("Collecting inputs")
    if server:
        log.info("Processing files from sftp server")
        directories["Level0"] = os.path.join(directories["Level0"], "Deployment3")
        if not os.path.exists(os.path.join(repo, "creds.json")):
            raise ValueError("Credential file required to retrieve live data from the fstp server.")
        with open(os.path.join(repo, "creds.json"), 'r') as f:
            creds = json.load(f)
        files = retrieve_new_files(directories["Level0"], creds, server_location="data/Idronaut", filetype=".txt")
        edited_files = edited_files + files
    else:
        files = files_in_directory(directories["Level0"])
        files.sort()
        log.info("Reprocessing complete dataset from {}".format(directories["Level0"]))
    log.end_stage()

    log.begin_stage("Processing data to L1")
    for file in files:
        if "Deployment1" in file:
            deployment = "D1"
            sensor = IdronautD1(log=log)
        elif "Deployment2" in file:
            deployment = "D2"
            sensor = IdronautD2(log=log)
        elif "Deployment3" in file:
            deployment = "D3"
            sensor = IdronautD3(log=log)
        else:
            continue

        if sensor.read_data(file):
            sensor.quality_assurance(file_path="notes/quality_assurance.json", maintenance_file="notes/events.csv")
            edited_files.extend(sensor.export(directories["Level1"], "L1_LexploreIdronaut_" + deployment))
            sensor.mask_data()
            sensor.profile_to_timeseries_grid(depth_label="depth")
            sensor.compute_physical_quantities()
            edited_files.extend(sensor.export(directories["Level2"], "L2_LexploreIdronaut_" + deployment, output_period="monthly",
                          profile_to_grid=True))
    log.end_stage()

    return edited_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', help="Collect and process new files from FTP server", action='store_true')
    parser.add_argument('--logs', '-l', help="Write logs to file", action='store_true')
    args = vars(parser.parse_args())
    main(server=args["server"], logs=args["logs"])