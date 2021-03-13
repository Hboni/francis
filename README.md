# Francis

![pytest](https://github.com/Hboni/francis/actions/workflows/python-app.yml/badge.svg)

Francis is a friendly image analysis interface system.

# Features

It allows pipeline creation with simple image analysis processes (erosion, threshold, ...). 

You can import _nifti_ data into Francis to make some basics operations and save the result.

# How to use

Clone this repository

    git clone git@github.com:Hboni/francis.git
    
Install python requirements

    pip install -r ./requirements.txt
    
Launch the application

    python ./main.py

# Requirements

- PyQt5
- scikit-image
- nibabel
- pandas

# Known issues

As Francis uses PyQt5 for its interface, it happens that on linux some library are missing, it can be needed to install them. (only tested on recent ubuntu)

For debian:

    sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
    
