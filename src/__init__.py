import os

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
MAIN_DIR = os.path.join(SRC_DIR, "..")
RESOURCE_DIR = os.path.join(MAIN_DIR, "resources")
DATA_DIR = os.path.join(RESOURCE_DIR, "data")
DESIGN_DIR = os.path.join(RESOURCE_DIR, "design")
CONFIG_DIR = os.path.join(MAIN_DIR, "config")
UI_DIR = os.path.join(MAIN_DIR, "src", "view", "ui")
OUT_DIR = os.path.join(DATA_DIR, "out")

# contain raw images
_IMAGES_STACK = {}

# contain viewable images (pixel values between 0 and 255)
IMAGES_STACK = {}
