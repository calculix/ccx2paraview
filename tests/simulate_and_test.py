# -*- coding: utf-8 -*-

"""
Solve Calculix examples using ccx first...
then test ccx2paraview converter on the CalculiX examples' frd-output

Setup of the conda environment is handled by conda wingman extension: 
(You need to open the ccx2paraview_simulate_and_test.yaml in ./tests)
Show and Run Commands > Conda Wingman: Build Conda Environment from YAML file
Show and Run Commands > Conda Wingman: Activate Conda Environment from YAML file

Set the Python Interpreter for VS Code to the environment's one:
Show and Run Commands > Python: Select Interpreter

Ctrl+F5 to run in VSCode. 
"""

# Standard imports
import os
import sys
import time
import shutil
import logging
import subprocess

# make files in ../ccx2paraview available for import
sys_path = os.path.abspath(__file__)
sys_path = os.path.dirname(sys_path)
sys_path = os.path.join(sys_path, '..')
sys_path = os.path.realpath(sys_path)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

# local imports
# pylint: disable=wrong-import-position
from log import LoggingHandler
from ccx2paraview.common import Converter
from ccx2paraview.cli import clean_screen
# pylint: enable=wrong-import-position

file_path = os.path.abspath(__file__)
dir_path = os.path.dirname(file_path)
dir_path_logs = os.path.realpath(os.path.join(dir_path, 'test_logs'))
dir_path_frds = os.path.realpath(os.path.join(dir_path, 'sim_frds'))

# Number of cores to use for simulation
N_CORE = int(8)

def clean_cache(folder:str=None):
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
        logging.error('Insufficient permissions for %s', dir)

def clean_results_keep_vtx(folder:str=None):
    """Cleaup old result files keeping the interesting results."""
    if folder is None:
        folder = os.getcwd()
    extensions = ('.dat', '.cvg', '.sta', '.out', '.12d')
    for f in os.scandir(folder):
        if f.is_dir():
            clean_results(f.path)
        if f.name.endswith(extensions):
            try:
                os.remove(f.path)
                sys.__stdout__.write('Deleted ' + f.path + '\n')
            except OSError:
                sys.__stdout__.write(f.path + ': ' + sys.exc_info()[1][1] + '\n')

def clean_results(folder:str=None):
    """Cleaup old result files."""
    if folder is None:
        folder = os.getcwd()
    extensions = ('.vtk', '.vtu', '.vtkhdf', '.pvd', '.dat', '.cvg', '.sta', '.out', '.12d')
    for f in os.scandir(folder):
        if f.is_dir():
            clean_results(f.path)
        if f.name.endswith(extensions):
            try:
                os.remove(f.path)
                sys.__stdout__.write('Deleted ' + f.path + '\n')
            except OSError:
                sys.__stdout__.write(f.path + ': ' + sys.exc_info()[1][1] + '\n')

def get_time_delta(delta):
    """Return spent time delta in format mm:ss.s."""
    return f'{int(delta%3600/60):d}m {delta%3600%60:.1f}s'

def ccx_and_convert_single_file(modelname, inp_path:str=None):
    """solve and convert a single model"""
    ccx_single_file(modelname, inp_path)
    convert_single_file(modelname)

def ccx_single_file(modelname, inp_path:str=None):
    """solve a single model"""

    if inp_path is not None:
        try:
            shutil.copy(\
                os.path.realpath(os.path.join(os.getcwd(), f'{inp_path}', f'{modelname}.inp')), \
                    os.path.realpath(os.path.join(f'{dir_path_frds}', f'{modelname}.inp')))
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            logging.error(e)

    log_file = os.path.realpath(os.path.join(dir_path_logs, f'{modelname}.ccx.log'))
    try:
        # Prepare logging
        lhs = LoggingHandler(log_file)
        logging.getLogger().addHandler(lhs)
        logging.getLogger().setLevel(logging.DEBUG)
        lhs.println('SIMULATE')
        lhs.println('')
        lhs.println(f'INFO: Reading {modelname}.inp')
        lhs.println(f'INFO: run ccx with {N_CORE} core(s)')
        start = time.perf_counter()

        # run ccx
        env = os.environ
        env['OMP_NUM_THREADS'] = str(N_CORE)
        with subprocess.Popen([shutil.which('ccx'), '-i', modelname],\
                              stdin=subprocess.PIPE,\
                              stdout=subprocess.PIPE,\
                              stderr=subprocess.STDOUT,\
                              cwd=dir_path_frds,\
                              env=env) as sim_process:
            lhs.read_and_log(sim_process.stdout)
        delta = time.perf_counter() - start
        lhs.println(get_time_delta(delta))
        # end logging
        logging.getLogger().removeHandler(lhs)
        lhs.stop_read_and_log()
        del lhs
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        logging.error(e)

def convert_single_file(modelname):
    """test conversion of a single file into all possible formats"""
    frd_file = os.path.realpath(os.path.join(dir_path_frds, f'{modelname}.frd'))
    log_file = os.path.realpath(os.path.join(dir_path_logs, f'{modelname}.convert.log'))
    try:
        # Prepare logging
        lhf = LoggingHandler(log_file)
        logging.getLogger().addHandler(lhf)
        logging.getLogger().setLevel(logging.DEBUG)
        lhf.println('CONVERTER TEST')
        lhf.println('')
        start = time.perf_counter()
        ccx2paraview = Converter(frd_file, ['vtk', 'vtu'])
        ccx2paraview.run()
        delta = time.perf_counter() - start
        lhf.println(get_time_delta(delta))
        # end logging
        logging.getLogger().removeHandler(lhf)
        lhf.stop_read_and_log()
        del lhf
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        logging.error(e)

def convert_single_file_vtu(modelname):
    """test conversion of a single file to vtu"""
    frd_file = os.path.realpath(os.path.join(dir_path_frds, f'{modelname}.frd'))
    log_file = os.path.realpath(os.path.join(dir_path_logs, f'{modelname}.convert.log'))
    try:
        # Prepare logging
        lhf = LoggingHandler(log_file)
        logging.getLogger().addHandler(lhf)
        logging.getLogger().setLevel(logging.DEBUG)
        lhf.println('CONVERTER TEST')
        lhf.println('')
        start = time.perf_counter()
        ccx2paraview = Converter(frd_file, ['vtu'])
        ccx2paraview.run()
        delta = time.perf_counter() - start
        lhf.println(get_time_delta(delta))
        # end logging
        logging.getLogger().removeHandler(lhf)
        lhf.stop_read_and_log()
        del lhf
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        logging.error(e)

def convert_single_file_vtk(modelname):
    """test conversion of a single file to vtk"""
    frd_file = os.path.realpath(os.path.join(dir_path_frds, f'{modelname}.frd'))
    log_file = os.path.realpath(os.path.join(dir_path_logs, f'{modelname}.convert.log'))
    try:
        # Prepare logging
        lhf = LoggingHandler(log_file)
        logging.getLogger().addHandler(lhf)
        logging.getLogger().setLevel(logging.DEBUG)
        lhf.println('CONVERTER TEST')
        lhf.println('')
        start = time.perf_counter()
        ccx2paraview = Converter(frd_file, ['vtk'])
        ccx2paraview.run()
        delta = time.perf_counter() - start
        lhf.println(get_time_delta(delta))
        # end logging
        logging.getLogger().removeHandler(lhf)
        lhf.stop_read_and_log()
        del lhf
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        logging.error(e)

def prepare_folders(folders:list=None):
    """Create frd and log folder"""
    for folder in folders:
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

# Run
if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

    # create folders for logs and frds if not present
    try:
        prepare_folders([dir_path_logs, dir_path_frds])
    except PermissionError as e:
        raise RuntimeError("Cannot create directories.") from e

    clean_cache()
    clean_results(dir_path_logs)
    clean_results(dir_path_frds)
    clean_screen()

    # These examples won't run in ccx for me
    #ccx_and_convert_single_file('Csati_Zoltan_many_sets', '../../examples/other')
    #ccx_and_convert_single_file('Kandala_Stepan_Floor', '../../examples/other')
    #ccx_and_convert_single_file('Sergio_Pluchinsky_piston', '../../examples/other')

    # These examples won't convert for me
    #ccx_and_convert_single_file('gears', '../../examples/other')
    # ERROR: 'utf-8' codec can't decode byte 0x9a in position 966: invalid start byte

    # These work...
    #ccx_and_convert_single_file('ball', '../../examples/other')
    #ccx_and_convert_single_file('dichtstoff_2_HE8', '../../examples/other')
    #ccx_and_convert_single_file('Dichtstoff_beam_coupling_compl', '../../examples/other')
    #ccx_and_convert_single_file('Ihor_Mirzov_baffle_2D', '../../examples/other')
    #ccx_and_convert_single_file('Jan_Lukas_modal_dynamic_beammodal', '../../examples/other')
    #ccx_and_convert_single_file('Jan_Lukas_modal_dynamic_staticbeam2', '../../examples/other')
    #ccx_and_convert_single_file('Jan_Lukas_static_structural', '../../examples/other')
    #ccx_and_convert_single_file('John_Mannisto_blade_sector', '../../examples/other')
    #ccx_and_convert_single_file('John_Mannisto_buckling_trick', '../../examples/other')
    #ccx_and_convert_single_file('Kaffeeheblerei_hinge', '../../examples/other')
    #ccx_and_convert_single_file('Nidish_Narayanaa_Balaji', '../../examples/other')
    #ccx_and_convert_single_file('Spanner-in', '../../examples/other/ddjokic-CalculiX-tests-master/Spanner')
    #ccx_and_convert_single_file('contact2e', '../../examples/ccx/structest')
    #ccx_and_convert_single_file('contact2i', '../../examples/ccx/structest')

    # Test conversion
    convert_single_file_vtu('ball')
    # convert_single_file('dichtstoff_2_HE8')
    # convert_single_file('Dichtstoff_beam_coupling_compl')
    # convert_single_file('Ihor_Mirzov_baffle_2D')
    # convert_single_file('Jan_Lukas_modal_dynamic_beammodal')
    # convert_single_file('Jan_Lukas_modal_dynamic_staticbeam2')
    # convert_single_file('Jan_Lukas_static_structural')
    # convert_single_file('John_Mannisto_blade_sector')
    # convert_single_file('John_Mannisto_buckling_trick')
    # convert_single_file('Kaffeeheblerei_hinge')
    # convert_single_file('Nidish_Narayanaa_Balaji')
    # convert_single_file('Spanner-in')
    # convert_single_file('contact2e')
    # convert_single_file('contact2i')

    clean_cache()
    clean_results_keep_vtx(dir_path_frds)
