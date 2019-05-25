# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019

"""
    Converts CalculiX .frd resutls file to ASCII .vtk or XML .vtu format
    Run with command:
        python3 ccx2paraview.py -frd 'jobname' -fmt 'format' -skip 's'
"""

import sys, argparse, os
from FRDParser import *
from VTKWriter import *
from VTUWriter import *

if __name__ == '__main__':

    # Command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("--frd", "-frd",
                        help="FRD-file name",
                        type=str, default='model')
    parser.add_argument("--fmt", "-fmt",
                        help="Output format: vtk or vtu",
                        type=str, default='vtu')
    parser.add_argument("--skip", "-skip",
                        help="Skip ERROR field: 0 or 1",
                        type=int, default=1)
    args = parser.parse_args()

    p = FRDParser(args.frd + '.frd')

    # Create list of time steps
    steps = sorted(set([b.numstep for b in p.result_blocks]))
    width = len(str(len(steps))) # max length of string designating step number
    steps = ['{:0{width}}'.format(s, width=width) for s in steps] # pad with zero
    if not len(steps):
        steps = ['1']

    # For each time step generate separate .vt* file
    for s in steps:
        if args.fmt == 'vtk':
            VTKWriter(p, args.skip, s)
        else:
            VTUWriter(p, args.skip, s)

    # Delete cached files
    os.system('py3clean .')

print('END')
