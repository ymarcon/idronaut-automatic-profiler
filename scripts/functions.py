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

