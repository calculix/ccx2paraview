#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    © Ihor Mirzov, January 2020
    Distributed under GNU General Public License v3.0

    Usage:
        python3 tests.py
        python3 tests.py > tests.log

    TODO use logging and write everything into logfile
    TODO reduce size of John_Mannisto_blade_sector
    TODO multiprocessing
    TODO os.scandir
"""


import subprocess, os, time, multiprocessing, glob
import clean, FRDParser


# List all .ext-files here and in all subdirectories
def list_all_files_in(start_folder, ext):
    all_files = []
    for f in os.listdir(start_folder): # iterate in current directory
        f = os.path.abspath(start_folder + '/' + f)
        if os.path.isdir(f): # if folder
            for ff in list_all_files_in(f, ext):
                all_files.append(ff)
        elif f.endswith(ext): # if file with needed extension
            all_files.append(f)
    return sorted(all_files)


# Submits all INP models starting from folder
def run_all_analyses_in(folder):
    start = time.perf_counter() # start time
    counter = 1
    start_folder = os.curdir
    for filename in list_all_files_in(folder, '.inp'):

        # Skip already calculated models
        if not os.path.isfile(filename[:-4] + '.frd'):
            relpath = os.path.relpath(filename, start=__file__)
            print(counter, relpath)
            counter += 1
            os.chdir(folder)
            subprocess.run('ccx -i ' + filename[:-4] + ' > ' + filename[:-4] + '.log', shell=True)

    os.chdir(start_folder)
    clean.files(folder)
    print('Total {:.1f} seconds'.format(time.perf_counter() - start))


# Test FRDParser only
def test_frd_parser_on_models_in(folder):
    start = time.perf_counter() # start time
    counter = 1
    for filename in list_all_files_in(folder, '.frd'):
        relpath = os.path.relpath(filename, start=__file__)
        print(counter, relpath)
        counter += 1
        FRDParser.Parse(filename)
    print('Total {:.1f} seconds'.format(time.perf_counter() - start))


# Convert calculation results
def convert_calculation_results_in(folder):
    start = time.perf_counter() # start time
    counter = 1
    for filename in list_all_files_in(folder, '.frd'):
        counter += 1

        # Skip already converted models
        if not len(glob.glob(filename[:-4] + '*.vt[ku]')):
            relpath = os.path.relpath(filename, start=__file__)
            print(counter, relpath)
            subprocess.run('python3 ./ccx2paraview.py ' + filename + ' vtk', shell=True)
            subprocess.run('python3 ./ccx2paraview.py ' + filename + ' vtu', shell=True)


# Check if created binaries work fine
def check_binaries(folder):
    for filename in list_all_files_in(folder, '.frd'):
        relpath = os.path.relpath(filename, start=__file__)
        print(relpath)
        if os.name == 'nt':
            subprocess.run('ccx2paraview.exe ' + filename + ' vtk', shell=True)
            subprocess.run('ccx2paraview.exe ' + filename + ' vtu', shell=True)
        else:
            subprocess.run('./ccx2paraview ' + filename + ' vtk', shell=True)
            subprocess.run('./ccx2paraview ' + filename + ' vtu', shell=True)
        break # one file only


if (__name__ == '__main__'):
    clean.screen()
    folder_tests = os.path.abspath('./tests')

    # Enable multithreading for CalculiX
    os.environ['OMP_NUM_THREADS'] = str(multiprocessing.cpu_count())

    # run_all_analyses_in(folder_tests)
    # convert_calculation_results_in(folder_tests)
    # test_frd_parser_on_models_in(folder_tests)
    check_binaries(folder_tests)

    clean.cache()
