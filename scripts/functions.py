# -*- coding: utf-8 -*-
import os
import copy
import json
import ftplib
import numpy as np
import pandas as pd
from shutil import move
from datetime import datetime, timedelta
from envass import qualityassurance
from general.functions import logger


def copy_files(outfolder, infolder):
    files = os.listdir(infolder)
    copied = []
    for file in files:
        if "status" not in file and not os.path.isfile(os.path.join(outfolder, file)) and ".txt" in file:
            copyfile(os.path.join(infolder, file), os.path.join(outfolder, file))
            copied.append(os.path.join(outfolder, file))
    return copied


def retrieve_new_files(folder, creds, log=logger(), server_location="data", filetype=".dat"):
    files = []
    log.info("Connecting to {}.".format(creds["ftp"]), indent=1)
    ftp = ftplib.FTP(creds["ftp"], creds["user"], creds["password"], timeout=100)
    server_files = ftp.nlst(server_location)
    server_files.sort()
    local_files = os.listdir(folder)
    for file in server_files:
        file_name = os.path.basename(file)
        if file_name not in local_files and file.endswith(filetype) and "status" not in file_name:
            log.info("Downloading file {}".format(file), indent=2)
            download_file(os.path.join(file), os.path.join(folder, file_name), ftp)
            files.append(os.path.join(folder, file_name))
        try:
            if (datetime.now() - datetime.strptime(file_name[:10], "%Y-%m-%d")) > timedelta(days=30):
                log.info("Remove old file {} from server".format(file), indent=2)
                ftp.delete(file)
        except Exception as e:
            log.info("Couldn't detect date of {}".format(file), indent=2)
    files.sort()
    log.info("{} new files found on the server.".format(len(files)), indent=1)
    return files


def download_file(server, local, ftp):
    with open(local, "wb") as f:
        ftp.retrbinary("RETR " + server, f.write)


