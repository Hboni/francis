import json
import os

# directories
MAIN_DIR = os.path.abspath(".")
RSC_DIR = os.path.join(MAIN_DIR, "resources")
CONFIG_DIR = os.path.join(MAIN_DIR, "config")
TMP_DIR = os.path.join(RSC_DIR, "data", "tmp")

# base key for json session encryption
KEY = "CchfHeEVsE1hMldggpUEXduYH29pUp2ujYE7LPjZhOA="

# load intial default parameters
with open(os.path.join(CONFIG_DIR, "default.json"), "r") as f:
    DEFAULT = json.load(f)

# update with user default parameters
usr_default_path = os.path.join(CONFIG_DIR, "usr_default.json")
if os.path.isfile(usr_default_path):
    with open(usr_default_path, "r") as f:
        DEFAULT.update(json.load(f))


def update_default(**kwargs):
    global DEFAULT
    DEFAULT.update(kwargs)
    with open(os.path.join(CONFIG_DIR, "usr_default.json"), "w") as f:
        json.dump(DEFAULT, f, indent=4)
