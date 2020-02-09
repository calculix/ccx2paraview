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
import logging

import clean
import ccx2paraview
import FRDParser
from log import myHandler
from log import print


# How many files to process
limit = 1000000


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

    os.chdir(start_folder)
    clean.files(folder)
    sys.stdout.write('\nTotal {:.1f} seconds\n'\
                     .format(time.perf_counter() - start))


# Test FRDParser only
def test_frd_parser_on_models_in(folder):
    start = time.perf_counter() # start time
    print('FRD PARSER TEST\n\n')
    counter = 1
    for file_name in scan_all_files_in(folder, '.frd'):
        relpath = os.path.relpath(file_name, start=os.getcwd())
        print('\n{}\n{}: {}'.format('='*50, counter, relpath))
        FRDParser.Parse(file_name)
        counter += 1
    print('\nTotal {:.1f} seconds'.format(time.perf_counter() - start))


# Convert calculation results
def convert_calculation_results_in(folder):
    print('CONVERTER TEST\n\n')
    start = time.perf_counter() # start time
    for file_name in scan_all_files_in(folder, '.frd'):
        print('\n' + '='*50)
        ccx2paraview.Converter(file_name, 'vtk').run()
        print('\n' + '='*50)
        ccx2paraview.Converter(file_name, 'vtu').run()
    print('\nTotal {:.1f} seconds'.format(time.perf_counter() - start))


if (__name__ == '__main__'):
    clean.screen()

    # Prepare logging
    logging.getLogger().addHandler(myHandler())
    logging.getLogger().setLevel(logging.INFO)

    # Enable multithreading for CalculiX
    os.environ['OMP_NUM_THREADS'] = str(os.cpu_count())

    folder = os.path.join(os.path.dirname(__file__), 'examples')
    # run_all_analyses_in(folder)
    # test_frd_parser_on_models_in(folder)
    convert_calculation_results_in(folder)

    clean.cache()
