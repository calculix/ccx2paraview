#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2020
Distributed under GNU General Public License v3.0

Test ccx2paraview converter on all the CalculiX examples
Ctrl+F5 to run in VSCode"""

import os
import sys
import time
import logging
import subprocess

sys_path = os.path.abspath(__file__)
sys_path = os.path.dirname(sys_path)
sys_path = os.path.join(sys_path, '..')
sys_path = os.path.normpath(sys_path)
sys.path.insert(0, sys_path)

import ccx2paraview
from ccx2paraview import clean
from ccx2paraview import FRDParser
from log import myHandler, print

# How many files to process
limit = 1000

# List all .ext-files here and in all subdirectories
def scan_all_files_in(start_folder, ext):
    all_files = []
    for f in os.scandir(start_folder):
        if f.is_dir():
            for ff in scan_all_files_in(f.path, ext):
                all_files.append(ff)
        elif f.is_file() and f.name.endswith(ext):
            all_files.append(f.path)
    return sorted(all_files)[:limit]

# Test FRDParser only
def test_frd_parser_on_models_in(folder):
    start = time.perf_counter() # start time
    print('FRD PARSER TEST\n\n')
    counter = 1
    for file_name in scan_all_files_in(folder, '.frd'):
        relpath = os.path.relpath(file_name, start=folder)
        print('\n{}\n{}: {}'.format('='*50, counter, relpath))
        FRDParser.Parse(file_name)
        counter += 1
    print('\nTotal {:.1f} seconds'.format(time.perf_counter() - start))

# Convert calculation results
def convert_calculation_results_in(folder):
    print('FRD CONVERTER TEST\n\n')
    start = time.perf_counter() # start time
    for file_name in scan_all_files_in(folder, '.frd'):
        print('\n' + '='*50)
        ccx2paraview.Converter(file_name, 'vtk').run()
        print('\n' + '='*50)
        ccx2paraview.Converter(file_name, 'vtu').run()
    print('\nTotal {:.1f} seconds'.format(time.perf_counter() - start))

# Convert calculation results with binaries
def test_binary_in(folder):
    print('CONVERTER TEST\n\n')
    start = time.perf_counter() # start time
    for file_name in scan_all_files_in(folder, '.frd'):
        if os.name == 'nt':
            command = '..\\bin\\ccx2paraview.exe'
        else:
            command = '../bin/ccx2paraview'
        for fmt in ['vtk', 'vtu']:
            print('\n' + '='*50)
            subprocess.run('{} {} {}'.format(command, file_name, fmt), shell=True)
    print('\nTotal {:.1f} seconds'.format(time.perf_counter() - start))

# Run
if __name__ == '__main__':
    clean.screen()

    # Prepare logging
    logging.getLogger().addHandler(myHandler())
    logging.getLogger().setLevel(logging.INFO)

    # Enable multithreading for CalculiX
    os.environ['OMP_NUM_THREADS'] = str(os.cpu_count())

    folder = os.path.join(os.path.dirname(__file__), \
        '..', '..', 'examples', 'other')
    # test_frd_parser_on_models_in(os.path.normpath(folder))
    convert_calculation_results_in(folder)
    # test_binary_in(folder)

    clean.cache()
