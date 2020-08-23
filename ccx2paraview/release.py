#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2020
Distributed under GNU General Public License v3.0

Prepare binaries for publishing
Ctrl+F5 from VSCode to run """

import os
import shutil
import datetime
import PyInstaller.__main__
from src import clean

def copy(src, dst, skip):
    for f in os.listdir(src):
        if f!='dist' and not f.endswith(skip):
            src_path = os.path.join(src, f)
            dst_path = os.path.join('dist', src, f)

            if os.path.isdir(src_path):
                if not os.path.isdir(dst_path):
                    os.mkdir(dst_path)
                copy(src_path, dst_path, skip)

            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

if __name__ == '__main__':
    if os.name=='nt':
        op_sys = '_windows'
        extension = '.exe' # binary extension in OS
        TEMP = 'C:\\Windows\\Temp\\'
    else:
        op_sys = '_linux'
        extension = '' # binary extension in OS
        TEMP = '/tmp/'

    skip = (op_sys, )
    PROJECT_NAME = os.path.split(os.getcwd())[-1] # name of project's folder
    DATE = '_' + datetime.datetime.now().strftime('%Y%m%d')
    ARCH = os.path.join('./releases', PROJECT_NAME + DATE + op_sys)

    # Remove prev. trash
    if os.path.isdir('./dist'):
        shutil.rmtree('./dist')

    # Run pyinstaller to create binaries
    args = [
        './src/ccx2paraview.py',
        '--workpath=' + TEMP,   # temp dir
        '-w',                   # no console during app run
        '--onefile',
        ]
    PyInstaller.__main__.run(args)

    # Delete cached files
    clean.cache()

    # Delete .spec file
    if os.path.isfile('ccx2paraview.spec'):
        os.remove('ccx2paraview.spec')

    # Prepare skip list
    with open('.gitignore', 'r') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        skip += (lines[i].rstrip().lstrip('*'), )
    skip += ('.git', '.gitignore', '.py', '.vscode',
        'bin', 'dist', 'releases', 'src', 'tests',
        'examples')

    # Copy files and folders from sources to 'dist'
    copy('.', 'dist', skip)

    # Make archive
    if os.path.isfile(ARCH + '.zip'):
        os.remove(ARCH + '.zip') # delete old

    # Compress whole directory
    shutil.make_archive(ARCH, 'zip', 'dist')

    # Remove unneeded files and folders
    shutil.rmtree(TEMP + 'ccx2paraview')
    shutil.rmtree(os.path.abspath('dist'))
