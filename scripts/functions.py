# -*- coding: utf-8 -*-
import json
import numpy as np
from envass import qualityassurance
from datetime import datetime
import math
import os
from shutil import copyfile


def copy_files(outfolder, infolder):
    files = os.listdir(infolder)
    copied = []
    for file in files:
        if "status" not in file and not os.path.isfile(os.path.join(outfolder, file)) and ".txt" in file:
            copyfile(os.path.join(infolder, file), os.path.join(outfolder, file))
            copied.append(os.path.join(outfolder, file))
    return copied

def retrieve_new_files(folder, creds, server_location="data", filetype=".csv", remove=False, overwrite=False, log=logger()):
    files = []
    log.info("Connecting to {}.".format(creds["ftp"]), indent=1)
    ftp = ftplib.FTP(creds["ftp"], timeout=100)
    ftp.login(creds["user"], creds["password"])
    server_files = ftp.nlst(server_location)
    local_files = os.listdir(folder)
    for file in server_files:
        file_name = os.path.basename(file)
        if file.endswith(filetype) and (overwrite or file_name not in local_files):
            log.info("Downloading file {}".format(file), indent=2)
            download_file(file, os.path.join(folder, file_name), ftp)
            if remove:
                ftp.delete(file)
            files.append(os.path.join(folder, file_name))
    files.sort()
    return files


def download_file(server, local, ftp):
    with open(local, "wb") as f:
        ftp.retrbinary("RETR " + server, f.write)


