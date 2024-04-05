#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0

CalculiX to Paraview converter (frd to vtk/vtu).
Makes possible to view and postprocess CalculiX
analysis results in Paraview. Generates Mises and
Principal components for stress and strain tensors.
"""

from . import common

# Standard imports
import argparse
import logging
import os


def clean_screen():
    """Clean screen."""
    os.system('cls' if os.name=='nt' else 'clear')


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('filename', type=str, help='FRD file name with extension')
    ap.add_argument('format', type=str, nargs='+', help='output format: vtk, vtu')
    args = ap.parse_args()

    # Check arguments
    assert os.path.isfile(args.filename), 'FRD file does not exist.'
    for a in args.format:
        msg = 'Wrong format "{}". '.format(a) + 'Choose between: vtk, vtu.'
        assert a in ('vtk', 'vtu'), msg

    # Create converter and run it
    ccx2paraview = Converter(args.filename, args.format)
    ccx2paraview.run()


if __name__ == '__main__':
    clean_screen()
    main()
