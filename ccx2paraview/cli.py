#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0

CalculiX to Paraview converter (frd to vtk/vtu).
Makes possible to view and postprocess CalculiX
analysis results in Paraview. Generates Mises and
Principal components for stress and strain tensors.
"""

from .common import Converter

# Standard imports
import argparse
import logging
import os


def clean_screen():
    """Clean screen."""
    os.system('cls' if os.name=='nt' else 'clear')


def filename_type(filename):
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError("The given file doesn't exist.")
    if not os.path.splitext(filename)[1].lower() == ".frd":
        raise argparse.ArgumentTypeError("The given file isn't a .frd file.")
    return filename


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('filename', type=filename_type, help='FRD file name with extension')
    ap.add_argument('format', type=str, nargs='+', help='Output format', choices=['vtk', 'vtu'])
    args = ap.parse_args()

    # Create converter and run it
    ccx2paraview = Converter(args.filename, args.format)
    ccx2paraview.run()


def main_with_format(format):
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('filename', type=filename_type, help='FRD file name with extension')
    args = ap.parse_args()

    # Create converter and run it
    ccx2paraview = Converter(args.filename, [format])
    ccx2paraview.run()


def ccx_to_vtk():
    main_with_format("vtk")


def ccx_to_vtu():
    main_with_format("vtu")


#if __name__ == '__main__':
#    clean_screen()
#    main()
