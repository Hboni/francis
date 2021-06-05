# Francis

![pytest](https://github.com/Hboni/francis/actions/workflows/python-app.yml/badge.svg)
[![codecov](https://codecov.io/gh/Hboni/francis/branch/main/graph/badge.svg?token=3ZTYZBL9NS)](https://codecov.io/gh/Hboni/francis)

Francis is a friendly image analysis interface system.

## Features

It allows pipeline creation with simple image analysis processes
(erosion, threshold, ...).

You can import _nifti_ data into Francis to make some basics operations
and save the result.

## How to use

Clone this repository

```bash
git clone git@github.com:Hboni/francis.git
```

Install python requirements

```bash
pip install -r ./requirements.txt
```

Launch the application

```bash
python ./main.py
```

## Requirements

- PyQt5
- scikit-image
- nibabel
- pandas

## How to contribute

To contribute to this project, you must clone this repository on you Windows
or Ubuntu computer (other linux distros are not tested).

```bash
git clone https://github.com/Hboni/francis.git
```

It is recommended to use a python virtualenv to install dependencies:

```bash
cd francis
pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

To develop in this project, it is also recommended to use [pre-commit](https://pre-commit.com/).

```bash
pip instal -r tests/requirements.txt
```

## Known issues

As Francis uses PyQt5 for its interface, it happens that on linux some library
are missing, it can be needed to install them. (only tested on recent ubuntu)

For debian:

```bash
sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
```
