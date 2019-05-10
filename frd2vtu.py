# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019

"""
    Converts CalculiX .frd resutls file to XML .vtu format
    Run with commands:
        python3 frd2vtu.py -frd jobname
        python3 frd2vtu.py -frd jobname -skip 1
        python3 frd2vtu.py -frd jobname -skip 0
"""

import sys, argparse
from FRDParser import *
from VTUWriter import *

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

    # Create list of time steps
    steps = sorted(set([b.numstep for b in p.frd.result_blocks]))
    width = int(len(steps) / 10) + 1 # max length of string designating step number
    steps = ['{:0{width}}'.format(s, width=width) for s in steps] # pad with zero

    # For each time step generate separate .vtu file
    for s in steps:
        VTUWriter(p, args.skip, s)

print('END')
