# -*- coding: utf-8 -*-


"""
    © Ihor Mirzov, August 2019
    Distributed under GNU General Public License v3.0

    Routine methods for cleaning up temporary/unused files/folders.
"""


import os, sys, shutil


# Clean screen
def screen():
    os.system('cls' if os.name=='nt' else 'clear')


# Delete cached files
def cache():
    # os.system('py3clean .')
    if os.path.isdir('__pycache__'):
        shutil.rmtree('__pycache__') # works in Linux as in Windows


# Cleaup trash files in startFolder and all subfolders
def files(startFolder):
    extensions = (  '.12d', '.cvg', '.dat', '.vwf', '.out', '.nam', '.inp1', '.inp2',
                    '.sta', '.log', '.equ', '.eig', '.stm', '.mtx', '.net', '.inp0',
                    '.rin', '.fcv'  )
    for f in os.listdir(startFolder):
        f = os.path.abspath(startFolder + '/' + f)
        if os.path.isdir(f): # if folder
            files(f)
        elif f.endswith(extensions):
            try:
                os.remove(f)
                sys.__stdout__.write('Delelted: ' + f + '\n')
            except:
                sys.__stdout__.write(f + ': ' + sys.exc_info()[1][1] + '\n')
