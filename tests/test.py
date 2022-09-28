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
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from ccx2paraview import clean_screen, clean_cache, Converter
from log import myHandler, print, read_and_log


def get_time_delta(delta):
    """Return spent time delta in format mm:ss.s."""
    return '{:d}m {:.1f}s'\
        .format(int(delta%3600/60), delta%3600%60)


def scan_all_files_in(start_folder, ext, limit=10000):
    """List all .ext-files here and in all subdirectories."""
    all_files = []
    for f in os.scandir(start_folder):
        if f.is_dir():
            for ff in scan_all_files_in(f.path, ext):
                all_files.append(ff)
        elif f.is_file() and f.name.endswith(ext):
            ff = os.path.normpath(f.path)
            all_files.append(ff)
    return sorted(all_files)[:limit]


def convert_calculation_results_in(folder):
    """Convert calculation results."""
    for counter, file_name in enumerate(scan_all_files_in(folder, '.frd')):
        relpath = os.path.relpath(file_name, start=folder)
        print('\n{}\n{}: {}'.format('='*50, counter+1, relpath))
        try:
            Converter(file_name, ['vtk', 'vtu']).run()
        except:
            logging.error(traceback.format_exc())


def test_binary_in(folder):
    """Convert calculation results with binaries."""
    for counter, file_name in enumerate(scan_all_files_in(folder, '.frd')):
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
        Converter(file_path, ['vtk', 'vtu']).run()
    except:
        logging.error(traceback.format_exc())


# Run
if __name__ == '__main__':
    start = time.perf_counter()
    clean_screen()

    # Prepare logging
    logging.getLogger().addHandler(myHandler())
    logging.getLogger().setLevel(logging.INFO)
    print('CONVERTER TEST\n\n')

    folder = '../examples'

    # for file_path in [
    #     # 'other/Sergio_Pluchinsky_PLASTIC_2ND_ORDER.frd',
    #     'mkraska/Contact/Shell0/Refs/qu4_pc-ns/pc-ns.frd',
    #     'mkraska/Contact/Shell0/Refs/qu8_pc-ns/pc-ns.frd',
    #     'mkraska/Contact/Shell0/Refs/qu8r_pc-ns/pc-ns.frd',
    #     'mkraska/Dynamics/Discrete/Refs/MS.frd',
    #     'mkraska/Linear/L-Plate/Refs/solve.frd',
    #     'mkraska/Test/Supports/Refs/solve.frd',
    #     'other/John_Mannisto_blade_sector.frd',
    #     ]:
    #     file_path = os.path.join(folder, file_path)
    #     test_single_file(file_path)

    convert_calculation_results_in(folder)
    # test_binary_in(folder)

    delta = time.perf_counter() - start
    print('\nTotal', get_time_delta(delta))
    clean_cache()
