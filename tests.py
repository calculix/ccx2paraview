# -*- coding: utf-8 -*-

"""
    © Ihor Mirzov, August 2019
    Distributed under GNU General Public License v3.0

    Usage:
        python3 tests.py
        python3 tests.py > tests.log
"""


import subprocess, os, time, logging
import clean


# List all .ext-files here and in all subdirectories
def listAllFiles(startFolder, ext):
    all_files = []
    for f in os.listdir(startFolder): # iterate over files and folders in current directory
        f = os.path.abspath(startFolder + '/' + f)
        if os.path.isdir(f): # if folder
            for ff in listAllFiles(f, ext):
                all_files.append(ff)
        elif f.endswith(ext):
            all_files.append(f) # with extension
    return all_files


if (__name__ == '__main__'):
    clean.screen()
    start = time.perf_counter() # start time

    # Configure logging
    test_file = './tests.log'
    if os.path.isfile(test_file):
        os.remove(test_file)
    logging.basicConfig(level=logging.INFO,
                        filename=test_file, filemode='a',
                        format='%(levelname)s: %(message)s')

    # # Enable multithreading
    # import multiprocessing as mp
    # cpu_count = str(mp.cpu_count()) # amount of cores
    # os.environ['OMP_NUM_THREADS'] = cpu_count

    # # Run analysis
    # for filename in listAllFiles('./tests', '.inp'):
    #     print(filename)
    #     subprocess.run('ccx -i ' + filename + ' > ' + filename + '.log', shell=True)

    # Convert calculation results
    for filename in listAllFiles('./tests', '.frd'):
        subprocess.run('python3 ccx2paraview.py ' + filename + ' vtk', shell=True)
        subprocess.run('python3 ccx2paraview.py ' + filename + ' vtu', shell=True)
        # break # one file only

    # # Test FRDParser only
    # import FRDParser
    # for filename in sorted(listAllFiles('./tests', '.frd')):
    #     FRDParser.Parse(filename)

    clean.cache()
    clean.files('./tests')
    logging.info('Total {:.1f} seconds'.format(time.perf_counter()-start))
