#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2020
Distributed under GNU General Public License v3.0

Converts CalculiX .frd-file to .vtk (ASCII) or .vtu (XML) format:
python3 ./ccx2paraview/__init__.py ../examples/other/Ihor_Mirzov_baffle_2D.frd vtk
python3 ./ccx2paraview/__init__.py ../examples/other/Ihor_Mirzov_baffle_2D.frd vtu """

import os
import sys
import logging
import argparse

sys_path = os.path.abspath(__file__)
sys_path = os.path.dirname(sys_path)
sys.path.insert(0, sys_path)

import FRDParser
from writer import Writer
import PVDWriter
import clean


class Converter:

    def __init__(self, file_name, fmt_list):
        self.file_name = file_name
        self.fmt_list = fmt_list

    def run(self):

        # Parse FRD-file
        base_name = os.path.basename(self.file_name)
        logging.info('Parsing ' + base_name)
        p = FRDParser.Parse(self.file_name)

        # If file contains mesh data
        if p.node_block and p.elem_block:
            for fmt in self.fmt_list:
                times = sorted(set([b.value for b in p.result_blocks]))
                l = len(times)
                if l:
                    msg = '{} time increment{}'.format(l, 's'*min(1, l-1))
                    logging.info(msg)

                    """ If model has many time steps - many output files
                    will be created. Each output file's name should contain
                    increment number padded with zero """
                    counter = 1
                    times_names = {} # {increment time: file name, ...}
                    for t in sorted(times):
                        if l > 1:
                            ext = '.{:0{width}}.{}'\
                                .format(counter, fmt, width=len(str(l)))
                            file_name = self.file_name.replace('.frd', ext)
                        else:
                            ext = '.{}'.format(fmt)
                            file_name = self.file_name.replace('.frd', ext)
                        times_names[t] = file_name
                        counter += 1

                    # For each time increment generate separate .vt* file
                    # Output file name will be the same as input
                    for t, file_name in times_names.items():
                        base_name = os.path.basename(file_name)
                        logging.info('Writing ' + base_name)
                        w = Writer(p, file_name, t)
                        if fmt == 'vtk': w.write_vtk()
                        if fmt == 'vtu': w.write_vtu()

                    # Write ParaView Data (PVD) for series of VTU files
                    if l > 1 and fmt == 'vtu':
                        PVDWriter.writePVD(self.file_name\
                            .replace('.frd', '.pvd'), times_names)

                else:
                    logging.warning('No time increments!')
                    file_name = self.file_name[:-3] + fmt
                    w = Writer(p, file_name, None)
                    if fmt == 'vtk': w.write_vtk()
                    if fmt == 'vtu': w.write_vtu()
        else:
            logging.warning('File is empty!')


if __name__ == '__main__':
    clean.screen()

    # Configure logging
    logging.basicConfig(level=logging.INFO,
        format='%(levelname)s: %(message)s')

    # Command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str,
        help='FRD file name with extension')
    parser.add_argument('format', type=str, nargs='+',
        help='output format: vtk, vtu')
    args = parser.parse_args()

    # Check arguments
    ok = True
    for a in args.format:
        if a not in ('vtk', 'vtu'):
            ok = False
            break

    # Create converter and run it
    if ok:
        ccx2paraview = Converter(args.filename, args.format)
        ccx2paraview.run()
    else:
        msg = 'ERROR! Wrong format \"{}\". '.format(a) \
            + 'Choose between: vtk, vtu.'
        print(msg)

    clean.cache()
