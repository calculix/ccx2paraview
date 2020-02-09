#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, February 2020
Distributed under GNU General Public License v3.0

Converts CalculiX .frd resutls file to ASCII .vtk or XML .vtu format:
python3 ccx2paraview.py ./tests/other/Ihor_Mirzov_baffle_2D.frd vtk
python3 ccx2paraview.py ./tests/other/Ihor_Mirzov_baffle_2D.frd vtu

TODO It would be a killer feature if Paraview could visualize
     gauss point results from the dat file...

TODO XDMF format """

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
        relpath = os.path.relpath(self.file_name, start=os.path.dirname(__file__))
        logging.info('Parsing ' + relpath)
        p = FRDParser.Parse(self.file_name)

        # If file isn't empty
        if p.node_block and p.elem_block:
            times_names = {} # {increment time: file name, ...}
            times = sorted(set([b.value for b in p.result_blocks])) # list of increment times
            width = len(str(len(times))) # max length of string designating step number
            logging.info('{} time increments'.format(len(times)))

            counter = 1
            for t in sorted(times):
                if len(times) > 1:
                    # Include step number in file_name, pad with zero
                    ext = '.{:0{width}}.{}'.format(counter, self.fmt, width=width)
                    file_name = p.file_name.replace('.frd', ext)
                else:
                    ext = '.{}'.format(self.fmt)
                    file_name = p.file_name.replace('.frd', ext)
                times_names[t] = file_name
                counter += 1

            # For each time increment generate separate .vt* file
            # Output file name will be the same as input
            for t, file_name in times_names.items():
                logging.info('Writing {}'.format(file_name))
                if self.fmt == 'vtk':
                    VTKWriter.writeVTK(p, file_name, t)
                if self.fmt == 'vtu':
                    VTUWriter.writeVTU(p, file_name, t)

            # Write ParaView Data (PVD) for series of VTU files.
            if len(times) > 1 and self.fmt == 'vtu':
                PVDWriter.writePVD(p.file_name.replace('.frd', '.pvd'), times_names)

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
