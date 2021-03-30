import os

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
MAIN_DIR = os.path.join(SRC_DIR, "..")
DATA_DIR = os.path.join(MAIN_DIR, "data")
CONFIG_DIR = os.path.join(MAIN_DIR, "config")
UI_DIR = os.path.join(MAIN_DIR, "src", "view", "ui")
OUT_DIR = os.path.join(MAIN_DIR, "out")

# contain raw images
_IMAGES_STACK = {}

# contain viewable images (pixel values between 0 and 255)
IMAGES_STACK = {}
