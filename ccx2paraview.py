#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    © Ihor Mirzov, August 2019
    Distributed under GNU General Public License v3.0

    Converts CalculiX .frd resutls file to ASCII .vtk or XML .vtu format.

    Run with command:
        python3 ccx2paraview.py ./tests/official-examples/beamf.frd vtk
        python3 ccx2paraview.py ./tests/official-examples/beamf.frd vtu
"""

# TODO https://github.com/pearu/pyvtk/blob/master/examples/example1.py

import argparse, os, logging
import FRDParser, VTKWriter, VTUWriter, PVDWriter, clean


if __name__ == '__main__':
    # Configure logging
    # test_file = './tests.log'
    logging.basicConfig(level=logging.INFO,
                        # filename=test_file, filemode='a',
                        format='%(levelname)s: %(message)s')

    # Command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str,
                        help='FRD file name with extension')
    parser.add_argument('format', type=str,
                        help='output format: vtu or vtk')
    args = parser.parse_args()

    # Parse FRD-file
    p = FRDParser.Parse(args.filename)

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
        relpath = os.path.relpath(args.filename, start=__file__)
        logging.info('Writing {}.{}'.format(relpath[:-4], args.format))
        for s in steps:
            # Output file name will be the same as input
            if len(steps) > 1: # include step number in file_name
                file_name = p.file_name.replace('.frd', '.{}.{}'.format(s, args.format))
                names.append(os.path.basename(file_name))
            else: # exclude step number from file_name
                file_name = p.file_name.replace('.frd', '.{}'.format(args.format))

            # Call converters
            if args.format == 'vtk':
                VTKWriter.writeVTK(p, file_name, s)
            if args.format == 'vtu':
                VTUWriter.writeVTU(p, file_name, s)

        # Write ParaView Data (PVD) for series of VTU files.
        if len(times) > 1 and args.format == 'vtu':
            PVDWriter.writePVD(p.file_name.replace('.frd', '.pvd'), times, names)


    else:
        logging.warning('File is empty!')

    # Delete cached files
    clean.cache()
