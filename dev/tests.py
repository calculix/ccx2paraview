# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, May 2019

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
        extensions = ('.12d', '.cvg', '.dat', 'vwf', '.out', '.sta', '.log')
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
def listAllInputFiles(startFolder):
    allInputFiles = []
    for f in os.listdir(startFolder): # iterate over files and folders in current directory
        f = os.path.abspath(startFolder + '/' + f)
        if os.path.isdir(f): # if folder
            for inputFile in listAllInputFiles(f):
                allInputFiles.append(inputFile)
        elif f[-4:] == '.inp':
            allInputFiles.append(f[:-4])
    return allInputFiles


if (__name__ == '__main__'):
    Clean.screen()

    # Enable multithreading
    cpu_count = str(mp.cpu_count()) # amount of cores
    os.environ['OMP_NUM_THREADS'] = cpu_count

    for modelname in listAllInputFiles('.'):
        print(modelname)
        
        # Run analysis
        subprocess.run('ccx -i ' + modelname, shell=True)

        # Convert calculation results to VTK format
        subprocess.run('python3 ccx2paraview.py -frd ' + modelname + ' -fmt vtk', shell=True)

        # Convert calculation results to VTU format
        subprocess.run('python3 ccx2paraview.py -frd ' + modelname + ' -fmt vtu', shell=True)

    Clean.cache()
    Clean.files('.')

    print('END')
