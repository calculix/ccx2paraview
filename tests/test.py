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
import shutil
import logging
import subprocess
import traceback

# make files in ../ccx2paraview available for import
sys_path = os.path.abspath(__file__)
sys_path = os.path.dirname(sys_path)
sys_path = os.path.join(sys_path, '..')
sys_path = os.path.normpath(sys_path)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

# local imports
# pylint: disable=wrong-import-position
from log import LoggingHandler
from ccx2paraview.cli import clean_screen
from ccx2paraview.common import Converter
# pylint: enable=wrong-import-position

# Logging Handler
logging_handler = None # pylint: disable=invalid-name

def clean_cache(folder=None):
    """Recursively delete cached files in all subfolders."""
    if folder is None:
        folder = os.getcwd()
    pycache = os.path.join(folder, '__pycache__')
    if os.path.isdir(pycache):
        shutil.rmtree(pycache) # works in Linux as in Windows

    # Recursively clear cache in child folders
    try:
        for f in os.scandir(folder):
            if f.is_dir():
                clean_cache(f.path)
    except PermissionError:
        logging.error('Insufficient permissions for ' + folder)


def clean_results(folder=None):
    """Cleaup old result files."""
    if folder is None:
        folder = os.getcwd()
    extensions = ('.vtk', '.vtu', '.pvd')
    for f in os.scandir(folder):
        if f.is_dir():
            clean_results(f.path)
        if f.name.endswith(extensions):
            try:
                os.remove(f.path)
                sys.__stdout__.write('Delelted: ' + f.path + '\n')
            except:
                sys.__stdout__.write(f.path + ': ' + sys.exc_info()[1][1] + '\n')


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


def test_my_parser_in(folder):
    """Convert calculation results."""
    for counter, file_path in enumerate(scan_all_files_in(folder, '.frd')):
        relpath = os.path.relpath(file_path, start=folder)
        logging_handler.println('\n{}\n{}: {}'.format('='*50, counter+1, relpath))
        test_my_single_file(file_path)


def test_my_single_file(file_path):
    try:
        start = time.perf_counter()
        # ccx2paraview = Converter(file_path, ['vtk', 'vtu'],
        #                 # parseonly=True, nomises=True, noeigen=True)
        #                 parseonly=False, nomises=False, noeigen=False)
        ccx2paraview = Converter(file_path, ['vtk', 'vtu'])
        ccx2paraview.run()
        delta = time.perf_counter() - start
        logging_handler.println(get_time_delta(delta))
    except:
        logging.error(traceback.format_exc())


def test_freecad_parser_in(folder):
    for counter, file_path in enumerate(scan_all_files_in(folder, '.frd')):
        relpath = os.path.relpath(file_path, start=folder)
        logging_handler.println('\n{}\n{}: {}'.format('='*50, counter+1, relpath))
        test_freecad_single_file(file_path)


def test_freecad_single_file(file_path):
    from freecad import read_frd_result
    try:
        start = time.perf_counter()
        read_frd_result(file_path)
        delta = time.perf_counter() - start
        logging_handler.println(get_time_delta(delta))
    except:
        logging.error(traceback.format_exc())


def test_binary_in(folder):
    """Convert calculation results with binaries."""
    for counter, file_path in enumerate(scan_all_files_in(folder, '.frd')):
        if os.name == 'nt':
            command = 'bin\\ccx2paraview.exe'
        else:
            command = './bin/ccx2paraview'
        relpath = os.path.relpath(file_path, start=folder)
        for fmt in ['vtk', 'vtu']:
            logging_handler.println('\n{}\n{}: {}'.format('='*50, counter, relpath))
            cmd = [command, file_path, fmt]
            try:
                process = subprocess.Popen(cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                logging_handler.read_and_log(process.stdout)
            except:
                logging.error(traceback.format_exc())
        logging_handler.stop_read_and_log()

def test_numpy():
    import numpy as np
    a = np.zeros([10, 2])
    logging_handler.println(a[:, 0])


# def test_NodalPointCoordinateBlock2():
#     from ccx2paraview import NodalPointCoordinateBlock2
#     file_path = os.path.join(os.path.dirname(__file__), 'pd.txt')
#     with open(file_path, 'r') as in_file:
#         node_block = NodalPointCoordinateBlock2(in_file)
#         print(node_block.nodes.head())
#         coords = node_block.get_node_coordinates(5)
#         print(coords)


def test_lin_indexes():
    line = ' -1         1-6.64251E-02-6.64250E-02-1.54991E-01-1.06122E-08-1.43067E-02 3.02626E-02'
    logging_handler.println(line[:5])
    logging_handler.println(line[5:13])
    logging_handler.println(line[13:25])
    logging_handler.println(line[25:37])
    logging_handler.println(line[37:49])
    logging_handler.println(line[49:61])
    logging_handler.println(line[61:73])
    logging_handler.println(line[73:85])


# Run
if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    d = '../../examples'
    clean_cache('..')
    clean_results(d)
    clean_screen()
    start = time.perf_counter()

    log_file = os.path.abspath(__file__)
    log_file = os.path.dirname(log_file)
    log_file = os.path.join(log_file, 'test.log')

    # Prepare logging
    logging_handler = LoggingHandler(log_file)
    logging.getLogger().addHandler(logging_handler)
    logging.getLogger().setLevel(logging.DEBUG)
    logging_handler.println('CONVERTER TEST')
    logging_handler.println(' ')

    # test_numpy()
    # test_NodalPointCoordinateBlock2()
    # test_lin_indexes()
    # raise SystemExit()

    # test_freecad_parser_in(d)
    # test_freecad_single_file(d + '/other/Sergio_Pluchinsky_PLASTIC_2ND_ORDER.frd_')

    test_my_parser_in(d)
    # test_my_single_file(d + '/other/Sergio_Pluchinsky_PLASTIC_2ND_ORDER.frd_')
    # test_my_single_file(d + '/other/Jan_Lukas_modal_dynamic_beammodal.frd')
    # test_my_single_file(d + '/other/John_Mannisto_blade_sector.frd')
    # test_my_single_file(d + '/other/Jan_Lukas_static_structural.frd')
    # test_my_single_file(d + '/other/Ihor_Mirzov_baffle_2D.frd')
    # test_my_single_file(d + '/other/CubeTie/CubeTie.frd')
    # test_my_single_file(d + '/other/ball.frd')
    # test_my_single_file('../../cae/examples/default.frd')
    # test_my_single_file(d + '/ccx/test/achtel2.frd')
    # test_my_single_file(d + '/mkraska/RVE/PlanarSlide/Refs/Zug.frd')
    # test_my_single_file(d + '/mkraska/Contact/CNC/Refs/solve.frd')
    # test_my_single_file(d + '/mkraska/Contact/Eyebar/Refs/eyebar.frd')
    # test_my_single_file(d + '/mkraska/Test/BeamSections/Refs/u1General.frd')

    delta = time.perf_counter() - start
    logging_handler.println(' ')
    logging_handler.println('Total', get_time_delta(delta))
    logging.getLogger().removeHandler(logging_handler)
    logging_handler.stop_read_and_log()
    clean_cache()
