#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0

Test ccx2paraview converter on all the CalculiX examples
Ctrl+F5 to run in VSCode.
"""

import os
import sys
import time
import logging
import subprocess
import traceback

sys_path = os.path.abspath(__file__)
sys_path = os.path.dirname(sys_path)
sys_path = os.path.join(sys_path, '..')
sys_path = os.path.normpath(sys_path)
sys.path.insert(0, sys_path)

import ccx2paraview
from ccx2paraview import clean, reader
from log import myHandler, print, read_and_log


# List all .ext-files here and in all subdirectories
def scan_all_files_in(start_folder, ext, limit=10000):
    all_files = []
    for f in os.scandir(start_folder):
        if f.is_dir():
            for ff in scan_all_files_in(f.path, ext):
                all_files.append(ff)
        elif f.is_file() and f.name.endswith(ext):
            ff = os.path.normpath(f.path)
            all_files.append(ff)
    return sorted(all_files)[:limit]


# Test FRD reader only
def test_frd_reader_on_models_in(folder):
    print('FRD READER TEST\n\n')
    counter = 0
    for file_name in scan_all_files_in(folder, '.frd'):
        counter += 1
        relpath = os.path.relpath(file_name, start=folder)
        print('\n{}\n{}: {}'.format('='*50, counter, relpath))
        try:
            reader.FRD(file_name)
        except:
            logging.error(traceback.format_exc())


# Convert calculation results
def convert_calculation_results_in(folder):
    print('CONVERTER TEST\n\n')
    counter = 0
    for file_name in scan_all_files_in(folder, '.frd'):
        counter += 1
        relpath = os.path.relpath(file_name, start=folder)
        print('\n{}\n{}: {}'.format('='*50, counter, relpath))
        try:
            ccx2paraview.Converter(file_name, ['vtk', 'vtu']).run()
        except:
            logging.error(traceback.format_exc())


# Convert calculation results with binaries
def test_binary_in(folder):
    print('CONVERTER TEST\n\n')
    counter = 0
    for file_name in scan_all_files_in(folder, '.frd'):
        counter += 1
        if os.name == 'nt':
            command = 'bin\\ccx2paraview.exe'
        else:
            command = './bin/ccx2paraview'
        relpath = os.path.relpath(file_name, start=folder)
        for fmt in ['vtk', 'vtu']:
            print('\n{}\n{}: {}'.format('='*50, counter, relpath))
            cmd = [command, file_name, fmt]
            try:
                process = subprocess.Popen(cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                read_and_log(process.stdout)
            except:
                logging.error(traceback.format_exc())


def test_single_file(file_path):
    print('\n{}\n{}'.format('='*50, file_path))
    try:
        ccx2paraview.Converter(file_path, ['vtk', 'vtu']).run()
    except:
        logging.error(traceback.format_exc())


# Run
if __name__ == '__main__':
    start = time.perf_counter()
    clean.screen()

    # Prepare logging
    logging.getLogger().addHandler(myHandler())
    logging.getLogger().setLevel(logging.INFO)

    folder = '../examples'

    # Choose what we test
    # test_frd_reader_on_models_in(folder)
    # convert_calculation_results_in(folder)
    test_binary_in(folder)
    # test_single_file('../examples/ccx/test/metalforming.frd')

    print('\nTotal {:.1f} seconds'.format(time.perf_counter() - start))
    clean.cache()
