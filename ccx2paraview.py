#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, February 2020
    Distributed under GNU General Public License v3.0

    Converts CalculiX .frd resutls file to ASCII .vtk or XML .vtu format.

    Example:
    python3 ccx2paraview.py ./tests/other/Ihor_Mirzov_baffle_2D.frd vtk
    python3 ccx2paraview.py ./tests/other/Ihor_Mirzov_baffle_2D.frd vtu
"""

import os
import logging
import argparse

import FRDParser
import VTKWriter
import VTUWriter
import PVDWriter
import clean


class Converter:

    def __init__(self, file_name, fmt):
        self.file_name = file_name
        self.fmt = fmt

    def run(self):

        # Parse FRD-file
        relpath = os.path.relpath(self.file_name, start=__file__)
        logging.info('Parsing ' + relpath)
        p = FRDParser.Parse(self.file_name)

        # If file isn't empty
        if p.node_block and p.elem_block:

            # Create list of time steps
            steps = sorted(set([b.numstep for b in p.result_blocks])) # list of step numbers
            width = len(str(len(steps))) # max length of string designating step number
            steps = ['{:0{width}}'.format(s, width=width) for s in steps] # pad with zero
            if not len(steps): steps = ['1'] # to run converter at least once
            times = sorted(set([b.value for b in p.result_blocks])) # list of step times
            names = []

            # For each time step generate separate .vt* file
            relpath = os.path.relpath(self.file_name, start=__file__)
            logging.info('Writing {}.{}'.format(relpath[:-4], self.fmt))
            for s in steps:
                # Output file name will be the same as input
                if len(steps) > 1: # include step number in file_name
                    file_name = p.file_name.replace('.frd', '.{}.{}'.format(s, self.fmt))
                    names.append(os.path.basename(file_name))
                else: # exclude step number from file_name
                    file_name = p.file_name.replace('.frd', '.{}'.format(self.fmt))

                # Call converters
                if self.fmt == 'vtk':
                    VTKWriter.writeVTK(p, file_name, s)
                if self.fmt == 'vtu':
                    VTUWriter.writeVTU(p, file_name, s)

            # Write ParaView Data (PVD) for series of VTU files.
            if len(times) > 1 and self.fmt == 'vtu':
                PVDWriter.writePVD(p.file_name.replace('.frd', '.pvd'), times, names)

        else:
            logging.warning('File is empty!')


if __name__ == '__main__':

    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s')

    # Command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str,
                        help='FRD file name with extension')
    parser.add_argument('format', type=str,
                        help='output format: vtu or vtk')
    args = parser.parse_args()

    # Create converter and run it
    ccx2paraview = Converter(args.filename, args.format)
    ccx2paraview.run()

    # Delete cached files
    clean.cache()
