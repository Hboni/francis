import os
import json


# directories
MAIN_DIR = os.path.abspath(".")
RSC_DIR = os.path.join(MAIN_DIR, "resources")
CONFIG_DIR = os.path.join(MAIN_DIR, "config")

# base key for json session encryption
KEY = 'CchfHeEVsE1hMldggpUEXduYH29pUp2ujYE7LPjZhOA='

# true results
# RESULT_STACK = {}

# load default global parameters
with open(os.path.join(CONFIG_DIR, "default.json"), "r") as f:
    DEFAULT = json.load(f)


def update_default(**kwargs):
    global DEFAULT
    DEFAULT.update(kwargs)
    with open(os.path.join(CONFIG_DIR, "default.json"), "w") as f:
        json.dump(DEFAULT, f, indent=4)
