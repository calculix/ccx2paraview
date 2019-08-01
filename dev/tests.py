# -*- coding: utf-8 -*-

"""
    © Ihor Mirzov, April 2019
    Distributed under GNU General Public License, version 2.

    python3 tests.py
"""

import subprocess, os, sys
import multiprocessing as mp


# Cleaning methods to remove temporary/unused files/folders
class Clean:
    # Clean screen
    @staticmethod
    def screen():
        os.system('cls' if os.name=='nt' else 'clear')

    # Delete cached files
    @staticmethod
    def cache():
        os.system('py3clean .')

    # Cleaup trash files in startFolder and all subfolders
    @staticmethod
    def files(startFolder):
        extensions = (  '.12d', '.cvg', '.dat', '.vwf', '.out', '.nam', '.inp1', '.inp2',
                        '.sta', '.log', '.equ', '.eig', '.stm', '.mtx', '.net', '.inp0'  )
        for f in os.listdir(startFolder):
            f = os.path.abspath(startFolder + '/' + f)
            if os.path.isdir(f): # if folder
                Clean.files(f)
            elif f.endswith(extensions):
                try:
                    os.remove(f)
                    sys.__stdout__.write('Delelted: ' + f + '\n')
                except:
                    sys.__stdout__.write(f + ': ' + sys.exc_info()[1][1] + '\n')


# List all .inp-files here and in all subdirectories
def listAllFiles(startFolder, fmt):
    all_files = []
    for f in os.listdir(startFolder): # iterate over files and folders in current directory
        f = os.path.abspath(startFolder + '/' + f)
        if os.path.isdir(f): # if folder
            for ff in listAllFiles(f, fmt):
                all_files.append(ff)
        elif f[-4:] == fmt:
            all_files.append(f[:-4])
    return all_files


if (__name__ == '__main__'):
    Clean.screen()

    # Enable multithreading
    cpu_count = str(mp.cpu_count()) # amount of cores
    os.environ['OMP_NUM_THREADS'] = cpu_count

    # Run analysis
    # for modelname in listAllFiles('.', '.inp'):
    #     print(modelname)
    #     subprocess.run('ccx -i ' + modelname + ' > ' + modelname + '.log', shell=True)

    # Convert calculation results
    # for modelname in listAllFiles('.', '.frd'):
    #     subprocess.run('python3 ccx2paraview.py -frd ' + modelname + ' -fmt vtk', shell=True)
    #     subprocess.run('python3 ccx2paraview.py -frd ' + modelname + ' -fmt vtu', shell=True)
        # break # one file only

    Clean.cache()
    Clean.files('.')
