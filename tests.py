#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, January 2020
Distributed under GNU General Public License v3.0
Test ccx2paraview converter on all the CalculiX examples
Ctrl + F5 to Run """

# TODO multiprocessing
# TODO cgx and mkraska examples

import os
import sys
import time
import subprocess
import multiprocessing
import glob
import logging

import clean
import FRDParser

log_file = os.path.join(os.path.dirname(__file__), 'tests.log')
dir_test = os.path.join(os.path.dirname(__file__), 'tests')
limit = 10


# Configure logging to emit messages via 'print' method
class myHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    def emit(self, LogRecord):
        msg_text = self.format(LogRecord)
        print(msg_text)


# Redefine print method to write logs to file
def print(*args):
    line = ' '.join([str(arg) for arg in args]) + '\n'
    with open(log_file, 'a') as f:
        f.write(line)
    sys.stdout.write(line)


# List all .ext-files here and in all subdirectories
def scan_all_files_in(start_folder, ext):
    all_files = []
    for f in os.scandir(start_folder):
        if f.is_dir():
            for ff in scan_all_files_in(f.path, ext):
                all_files.append(ff)
        elif f.is_file() and f.name.endswith(ext):
            all_files.append(f.path)
    return sorted(all_files)


# Submits all INP models starting from folder
def run_all_analyses_in(folder):
    start = time.perf_counter() # start time
    counter = 1
    start_folder = os.curdir
    for file_name in scan_all_files_in(folder, '.inp'):

        # Skip already calculated models
        if not os.path.isfile(file_name[:-4] + '.frd'):
            relpath = os.path.relpath(file_name, start=__file__)
            sys.stdout.write('{} {}\n'.format(counter, relpath))
            counter += 1
            os.chdir(folder)
            subprocess.run('ccx -i ' + file_name[:-4] + ' > ' + file_name[:-4] + '.log', shell=True)

        if counter > limit: break

    os.chdir(start_folder)
    clean.files(folder)
    sys.stdout.write('Total {:.1f} seconds\n'\
                     .format(time.perf_counter() - start))


# Test FRDParser only
def test_frd_parser_on_models_in(folder):
    start = time.perf_counter() # start time
    counter = 1
    for file_name in scan_all_files_in(folder, '.frd'):
        relpath = os.path.relpath(file_name, start=__file__)
        sys.stdout.write('{} {}\n'.format(counter, relpath))
        FRDParser.Parse(file_name)
        counter += 1
        if counter > limit: break
    print('Total {:.1f} seconds'.format(time.perf_counter() - start))


# Convert calculation results
def convert_calculation_results_in(folder):
    start = time.perf_counter() # start time
    counter = 1
    for file_name in scan_all_files_in(folder, '.frd'):
        # TODO Compare log with ccx_cae tests

        # Skip already converted models
        # if not len(glob.glob(file_name[:-4] + '*.vt[ku]')):
        print('\n==================================================')
        subprocess.run('python3 ./ccx2paraview.py ' + file_name + ' vtk', shell=True)
        print('\n==================================================')
        subprocess.run('python3 ./ccx2paraview.py ' + file_name + ' vtu', shell=True)

        counter += 1
        if counter > limit: break

    print('Total {:.1f} seconds'.format(time.perf_counter() - start))


# Check if created binaries work fine
def check_binaries(folder):
    counter = 1
    for file_name in scan_all_files_in(folder, '.frd'):
        if os.name == 'nt':
            subprocess.run('ccx2paraview.exe ' + file_name + ' vtk', shell=True)
            subprocess.run('ccx2paraview.exe ' + file_name + ' vtu', shell=True)
        else:
            subprocess.run('./ccx2paraview ' + file_name + ' vtk', shell=True)
            subprocess.run('./ccx2paraview ' + file_name + ' vtu', shell=True)
        counter += 1
        if counter > limit: break


if (__name__ == '__main__'):
    clean.screen()

    # Prepare logging
    if os.path.isfile(log_file): os.remove(log_file)
    logging.getLogger().addHandler(myHandler())
    logging.getLogger().setLevel(logging.INFO)

    # Enable multithreading for CalculiX
    os.environ['OMP_NUM_THREADS'] = str(multiprocessing.cpu_count())

    # run_all_analyses_in(dir_test)
    convert_calculation_results_in(dir_test)
    # test_frd_parser_on_models_in(dir_test)
    # check_binaries(dir_test)

    clean.cache()
