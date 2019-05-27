#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019

"""
    Converts CalculiX .frd resutls file to ASCII .vtk or XML .vtu format.

    Run with command:
        python3 ccx2paraview.py -frd 'jobname' -fmt vtk
    or:
        python3 ccx2paraview.py -frd 'jobname' -fmt vtu
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

    # Parse FRD-file
    p = FRDParser(args.frd + '.frd')

    # Calculate amounts of nodes and elements
    try:
        nn = max([len(b.results) for b in p.result_blocks]) # total number of nodes
    except:
        nn = p.node_block.numnod # TODO Wrong amount of nodes - has 18 zero nodes more
    ne = p.elem_block.numelem # total number of elements
    print(nn, 'nodes total')
    print(ne, 'cells total')
    print('Converting FRD to {}...'.format(args.fmt.upper()))

    # Create list of time steps
    steps = sorted(set([b.numstep for b in p.result_blocks])) # list of step numbers
    width = len(str(len(steps))) # max length of string designating step number
    steps = ['{:0{width}}'.format(s, width=width) for s in steps] # pad with zero
    if not len(steps): steps = ['1'] # to run converter at least once

    # For each time step generate separate .vt* file
    for s in steps:
        # Output file name will be the same as input
        if len(steps) > 1: # include step number in file_name
            file_name = p.file_name.replace('.frd', '.{}.{}'.format(s, args.fmt))
        else: # exclude step number from file_name
            file_name = p.file_name.replace('.frd', '.{}'.format(args.fmt))
        print(file_name)

        # Call converters
        if args.fmt == 'vtk':
            VTKWriter(p, args.skip, file_name, s, nn, ne)
        if args.fmt == 'vtu':
            VTUWriter(p, args.skip, file_name, s, nn, ne)

    # Delete cached files
    os.system('py3clean .')

print('END')
