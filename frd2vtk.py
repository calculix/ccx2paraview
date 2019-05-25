# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019

"""
    Converts CalculiX .frd resutls file to ASCII .vtk format
    Run with commands:
        python3 frd2vtk.py -frd jobname
        python3 frd2vtk.py -frd jobname -skip 1
        python3 frd2vtk.py -frd jobname -skip 0
"""

import sys, argparse, os
from FRDParser import *
from VTKWriter import *

if __name__ == '__main__':

    # Command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("--frd", "-frd",
                        help="FRD-file name",
                        type=str, default='job')
    parser.add_argument("--skip", "-skip",
                        help="Skip ERROR field: 0 or 1",
                        type=int, default=1)
    args = parser.parse_args()

    p = FRDParser(args.frd + '.frd')
    VTKWriter(p, args.skip)

    # Delete cached files
    os.system('py3clean .')

print('END')
