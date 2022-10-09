#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0

CalculiX to Paraview converter (frd to vtk/vtu).
Makes possible to view and postprocess CalculiX
analysis results in Paraview. Generates Mises and
Principal components for stress and strain tensors.
"""

# Standard imports
import os
import logging
import argparse
import threading
import math
import re

# External imports
import numpy as np
import vtk

renumbered_nodes = {} # old_number : new_number


def clean_screen():
    """Clean screen."""
    os.system('cls' if os.name=='nt' else 'clear')


def get_inc_step(line):
    """Read step information
    CL  101 0.36028E+01         320                     3    1           1
    CL  101 1.000000000         803                     0    1           1
    CL  101 1.000000000          32                     0    1           1
    CL  102 117547.9305          90                     2    2MODAL      1
    """
    line = line[12:]
    regex = '^(.{12})\s+\d+\s+\d+\s+(\d+)'
    match = match_line(regex, line)
    inc = float(match.group(1)) # could be frequency, time or any numerical value
    step = int(match.group(2)) # step number
    # txt = 'Step info: value {}, step {}'.format(inc, step)
    # logging.debug(txt)
    return inc, step


def match_line(regex, line):
    """Search regex in line and report problems.
    NOTE Using regular expressions is faster than splitting strings.
    """
    match = re.search(regex, line)
    if match:
        return match
    else:
        logging.error('Can\'t parse line:\n{}\nwith regex:\n{}'\
            .format(line, regex))
        raise Exception




"""Classes and functions for reading CalculiX .frd files."""


class NodalPointCoordinateBlock:
    """Nodal Point Coordinate Block: cgx_2.20.pdf Manual, § 11.3.
    Generate vtkPoints. Points should be renumbered starting from 0.
    """

    def __init__(self, in_file):
        """Read nodal coordinates."""
        global renumbered_nodes
        renumbered_nodes.clear()
        self.points = vtk.vtkPoints()

        new_node_number = 0
        while True:
            line = in_file.readline().strip()

            # End of block
            if not line or line == '-3':
                break

            regex = '^-1(.{10})' + '(.{12})'*3
            match = match_line(regex, line)
            node_number = int(match.group(1))
            node_coords = [ float(match.group(2)),
                            float(match.group(3)),
                            float(match.group(4)), ]

            renumbered_nodes[node_number] = new_node_number
            self.points.InsertPoint(new_node_number, node_coords)
            new_node_number += 1

        self.numnod = self.points.GetNumberOfPoints() # number of nodes in this block
        logging.info('{} nodes'.format(self.numnod)) # total number of nodes

    def get_node_numbers(self):
        global renumbered_nodes
        return sorted(renumbered_nodes.keys())


"""NOTE Not used
class NodalPointCoordinateBlock2:
    # Nodal Point Coordinate Block: cgx_2.20.pdf Manual, § 11.3.
    # self.nodes is a Pandas DataFrame.

    def __init__(self, in_file):
        import pandas
        lines = ''
        while True:
            line = in_file.readline()
            if not line or line.strip() == '-3': break
            lines += line

        from io import StringIO
        self.nodes = pandas.read_fwf(StringIO(lines), usecols=[1,2,3,4], index_col=0,
            names=['skip', 'node', 'X', 'Y', 'Z'], widths=[5, 8, 12, 12, 12])

        self.numnod = self.nodes.shape[0] # number of nodes in this block
        logging.info('{} nodes'.format(self.numnod)) # total number of nodes

    def get_node_numbers(self):
        # Dataframe index column.
        # return [int(n) for n in list(self.nodes.index.values)]
        return list(self.nodes.index.values)
"""


class ElementDefinitionBlock:
    """Element Definition Block: cgx_2.20.pdf Manual, § 11.4.
    Generates vtkCellArray.
    """

    def __init__(self, in_file):
        self.in_file = in_file
        self.cells = vtk.vtkCellArray()
        self.types = []

        while True:
            line = in_file.readline().strip()

            # End of block
            if not line or line == '-3':
                break

            self.read_element(line)

        self.numelem = self.cells.GetNumberOfCells() # number of elements in this block
        logging.info('{} cells'.format(self.numelem)) # total number of elements

    def read_element(self, line):
        """Read element composition
        -1         1    1    0AIR
        -2         1         2         3         4         5         6         7         8
        -1         1   10    0    1
        -2         1         2         3         4         5         6         7         8
        -1         2   11    0    2
        -2         9        10
        -1         3   12    0    2
        -2        10        12        11
        """
        global renumbered_nodes
        element_num = int(line.split()[1])
        element_type = int(line.split()[2])
        element_nodes = []
        for j in range(self.num_lines(element_type)):
            line = self.in_file.readline().strip()
            nodes = [renumbered_nodes[int(n)] for n in line.split()[1:]]
            element_nodes.extend(nodes)

        vtk_elem_type = self.convert_elem_type(element_type)
        self.types.append(vtk_elem_type)
        connectivity = self.get_element_connectivity(element_type, element_nodes)
        self.cells.InsertNextCell(len(connectivity), connectivity)

    def num_lines(self, etype):
        """Amount of lines in element connectivity definition.
        First value is meaningless, since elements are 1-based.
        """
        return (0, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1)[etype]

    def convert_elem_type(self, frd_elem_type):
        """Convert Calculix element type to VTK.
        Keep in mind that CalculiX expands shell elements.
        In VTK nodes are numbered starting from 0, not from 1.

        For FRD see http://www.dhondt.de/cgx_2.15.pdf pages 117-123 (chapter 10)
        For VTK see https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf pages 9-10
        _________________________________________________________________
        |                               |                                 |
        | №№      CalculiX type         |  №№         VTK type            |
        |_______________________________|_________________________________|
        |    |          |               |      |                          |
        |  1 | C3D8     |  8 node brick | = 12 | VTK_HEXAHEDRON           |
        |    | F3D8     |               |      |                          |
        |    | C3D8R    |               |      |                          |
        |    | C3D8I    |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  2 | C3D6     |  6 node wedge | = 13 | VTK_WEDGE                |
        |    | F3D6     |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  3 | C3D4     |  4 node tet   | = 10 | VTK_TETRA                |
        |    | F3D4     |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  4 | C3D20    | 20 node brick | = 25 | VTK_QUADRATIC_HEXAHEDRON |
        |    | C3D20R   |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  5 | C3D15    | 15 node wedge | ~ 13 | VTK_WEDGE                |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  6 | C3D10    | 10 node tet   | = 24 | VTK_QUADRATIC_TETRA      |
        |    | C3D10T   |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  7 | S3       |  3 node shell | =  5 | VTK_TRIANGLE             |
        |    | M3D3     |               |      |                          |
        |    | CPS3     |               |      |                          |
        |    | CPE3     |               |      |                          |
        |    | CAX3     |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  8 | S6       |  6 node shell | = 22 | VTK_QUADRATIC_TRIANGLE   |
        |    | M3D6     |               |      |                          |
        |    | CPS6     |               |      |                          |
        |    | CPE6     |               |      |                          |
        |    | CAX6     |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        |  9 | S4       |  4 node shell | =  9 | VTK_QUAD                 |
        |    | S4R      |               |      |                          |
        |    | M3D4     |               |      |                          |
        |    | M3D4R    |               |      |                          |
        |    | CPS4     |               |      |                          |
        |    | CPS4R    |               |      |                          |
        |    | CPE4     |               |      |                          |
        |    | CPE4R    |               |      |                          |
        |    | CAX4     |               |      |                          |
        |    | CAX4R    |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        | 10 | S8       |  8 node shell | = 23 | VTK_QUADRATIC_QUAD       |
        |    | S8R      |               |      |                          |
        |    | M3D8     |               |      |                          |
        |    | M3D8R    |               |      |                          |
        |    | CPS8     |               |      |                          |
        |    | CPS8R    |               |      |                          |
        |    | CPE8     |               |      |                          |
        |    | CPE8R    |               |      |                          |
        |    | CAX8     |               |      |                          |
        |    | CAX8R    |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        | 11 | B21      |  2 node beam  | =  3 | VTK_LINE                 |
        |    | B31      |               |      |                          |
        |    | B31R     |               |      |                          |
        |    | T2D2     |               |      |                          |
        |    | T3D2     |               |      |                          |
        |    | GAPUNI   |               |      |                          |
        |    | DASHPOTA |               |      |                          |
        |    | SPRING2  |               |      |                          |
        |    | SPRINGA  |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        | 12 | B32      |  3 node beam  | = 21 | VTK_QUADRATIC_EDGE       |
        |    | B32R     |               |      |                          |
        |    | T3D3     |               |      |                          |
        |    | D        |               |      |                          |
        |____|__________|_______________|______|__________________________|
        |    |          |               |      |                          |
        | ?? | SPRING1  |  1 node       | =  1 | VTK_VERTEX               |
        |    | DCOUP3D  |               |      |                          |
        |    | MASS     |               |      |                          |
        |____|__________|_______________|______|__________________________|
        """
        # frd_elem_type : vtk_elem_type
        frd2vtk_num = {
            1: 12,
            2: 13,
            3: 10,
            4: 25,
            5: 13,
            6: 24,
            7:  5,
            8: 22,
            9:  9,
            10: 23,
            11:  3,
            12: 21}
        frd2vtk_txt = {
            'C3D8':12,
            'F3D8':12,
            'C3D8R':12,
            'C3D8I':12,
            'C3D6':13,
            'F3D6':13,
            'C3D4':10,
            'F3D4':10,
            'C3D20':25,
            'C3D20R':25,
            'C3D15':13,
            'C3D10':24,
            'C3D10T':24,
            'S3':5,
            'M3D3':5,
            'CPS3':5,
            'CPE3':5,
            'CAX3':5,
            'S6':22,
            'M3D6':22,
            'CPS6':22,
            'CPE6':22,
            'CAX6':22,
            'S4':9,
            'S4R':9,
            'M3D4':9,
            'M3D4R':9,
            'CPS4':9,
            'CPS4R':9,
            'CPE4':9,
            'CPE4R':9,
            'CAX4':9,
            'CAX4R':9,
            'S8':23,
            'S8R':23,
            'M3D8':23,
            'M3D8R':23,
            'CPS8':23,
            'CPS8R':23,
            'CPE8':23,
            'CPE8R':23,
            'CAX8':23,
            'CAX8R':23,
            'B21':3,
            'B31':3,
            'B31R':3,
            'T2D2':3,
            'T3D2':3,
            'GAPUNI':3,
            'DASHPOTA':3,
            'SPRING2':3,
            'SPRINGA':3,
            'B32':21,
            'B32R':21,
            'T3D3':21,
            'D':21,
            'SPRING1':1,
            'DCOUP3D':1,
            'MASS':1}
        if frd_elem_type in frd2vtk_num:
            return frd2vtk_num[frd_elem_type]
        else:
            if frd_elem_type in frd2vtk_txt:
                return frd2vtk_txt[frd_elem_type]
            else:
                return 0

    def get_element_connectivity(self, e_type, e_nodes):
        """Element connectivity with renumbered nodes.
        Here passed element nodes are repositioned according to VTK rules.
        """
        connectivity = []

        # frd: 20 node brick element
        if e_type == 4:
            # Last eight nodes have to be repositioned
            r1 = tuple(range(12)) # 8,9,10,11
            r2 = tuple(range(12, 16)) # 12,13,14,15
            r3 = tuple(range(16, 20)) # 16,17,18,19
            node_num_list = r1 + r3 + r2
            for i in node_num_list:
                connectivity.append(e_nodes[i]) # nodes after renumbering

        # frd: 15 node penta element
        elif e_type==5 or e_type==2:
            """CalculiX elements type 5 are not supported in VTK and
            has to be processed as CalculiX type 2 (6 node wedge,
            VTK type 13). Additional nodes are omitted.
            """
            for i in [0,2,1,3,5,4]: # repositioning nodes
                connectivity.append(e_nodes[i]) # nodes after renumbering

        # All other elements
        else:
            n = len(e_nodes)
            for i in range(n):
                connectivity.append(e_nodes[i]) # nodes after renumbering

        return connectivity


"""NOTE Not used
class ElementDefinitionBlock2:
    # Element Definition Block: cgx_2.20.pdf Manual, § 11.4.
    # self.elements is a Pandas DataFrame.

    def __init__(self, in_file):
        # Read element composition
        # -1      2355    1    0    1
        # -2     20814     26109     21063     25605     20816     26111     21065     25607
        # -1      2356    1    0    1
        # -2     20781     25602     21066     26106     20783     25604     21068     26108
        # -1         1    1    0AIR
        # -2         1         2         3         4         5         6         7         8
        # -1         1   10    0    1
        # -2         1         2         3         4         5         6         7         8
        # -1         2   11    0    2
        # -2         9        10
        # -1         3   12    0    2
        # -2        10        12        11
        import pandas
        lines = ''
        while True:
            line = in_file.readline().lstrip()
            if not line or line.rstrip() == '-3': break
            if line.startswith('-1'):
                line = line[:19]
            lines += line[3:]

        # for line in lines.split('\n')[:5]:
        #     logging.debug(line)

        from io import StringIO
        self.elements = pandas.read_fwf(StringIO(lines), index_col=0, header=None)
        # logging.debug(self.elements.head())

        self.numelem = self.elements.shape[0] # number of elements in this block
        logging.info('{} cells'.format(self.numelem)) # total number of elements
    """


class NodalResultsBlock:
    """Nodal Results Block: cgx_2.20.pdf Manual, § 11.6.
    Oned instance keeps data for one field variable in one step.
    """

    def __init__(self, node_block):
        """Read calculated values."""
        self.components = [] # component names
        self.name = None
        self.inc = 0
        self.ncomps = 0
        self.step = 0
        self.node_block = node_block
        self.messages = []
        self.data_array = vtk.vtkDoubleArray()

        # Some warnings repeat too much time - mark them
        self.emitted_warning_types = {'Inf':0, 'NaN':0, 'WrongFormat':0}

    def run(self, in_file, line):
        self.in_file = in_file
        self.data_array.SetNumberOfTuples(self.node_block.numnod)
        self.inc, self.step = get_inc_step(line)
        self.read_components_info()
        self.read_nodal_results()

    def read_components_info(self):
        """Read components information
        -4  V3DF        4    1
        -4  DISP        4    1
        -4  STRESS      6    1
        -4  DOR1  Rx    4    1
        """
        line = self.in_file.readline().strip()
        regex = '^-4\s+(\w+)' + '\D+(\d+)'*2
        match = match_line(regex, line)

        # Rename result block to the name from .inp-file
        inpname = {
            'DISP':'U',
            'NDTEMP':'NT',
            'STRESS':'S',
            'TOSTRAIN':'E',
            'FORC':'RF',
            'PE':'PEEQ',
            }
        self.name = match.group(1) # dataset name
        if self.name in inpname:
            self.name = inpname[self.name]
        self.data_array.SetName(self.name)

        """Iterate over components
        -5  D1          1    2    1    0
        -5  D2          1    2    2    0
        -5  D3          1    2    3    0
        -5  ALL         1    2    0    0    1ALL

        -5  DFDN        1    1    1    0
        -5  DFDNFIL     1    1    2    0

        -5  V1          1    2    1    0
        -5  V2          1    2    2    0
        -5  V3          1    2    3    0
        -5  ALL         1    2    0    0    1ALL

        -5  SXX         1    4    1    1
        -5  SYY         1    4    2    2
        -5  SZZ         1    4    3    3
        -5  SXY         1    4    1    2
        -5  SYZ         1    4    2    3
        -5  SZX         1    4    3    1
        """
        while True:
            line = self.in_file.readline()
            if line[:3] != ' -5':
                self.in_file.seek(self.in_file.tell() - len(line)) # go up one line
                break
            line = line[5:]
            regex = '^\w+'
            match = match_line(regex, line)

            # Exclude variable name from the component name: SXX->XX, EYZ->YZ
            component_name = match.group(0)
            if component_name.startswith(self.name):
                component_name = component_name[len(self.name):]

            if 'ALL' not in component_name:
                self.ncomps += 1
                self.components.append(component_name)

        self.set_component_names()

    def set_component_names(self):
        """Set component names."""
        self.data_array.SetNumberOfComponents(self.ncomps)
        for i,c in enumerate(self.components):
            if 'SDV' in c:
                self.data_array.SetComponentName(i, i)
            else:
                self.data_array.SetComponentName(i, c)

    def set_point_values(self, point_num, values):
        """point_num is a renumbered node number.
        VTK point numbering starts from 0."""
        self.set_component_names()
        self.data_array.InsertTuple(point_num, values)

    def read_nodal_results(self):
        """Iterate over nodal results
        -1         1-7.97316E+10-3.75220E-01
        -1         2-8.19094E+10-3.85469E-01

        -1         1-6.93889E-18-9.95185E-01-4.66908E-34
        -1         2-1.94151E-01-9.76063E-01 6.46011E-30

        -1         1 1.47281E+04 1.39140E+04 2.80480E+04 5.35318E+04 6.36642E+03 1.82617E+03
        -2           5.31719E+01 6.69780E+01 2.76244E+01 2.47686E+01 1.99930E+02 2.14517E+02
        """
        # Fill data with zeroes - sometimes FRD result block has only non zero values
        global renumbered_nodes
        for point_num in renumbered_nodes.values():
            self.set_point_values(point_num, [0]*self.ncomps)

        i = 0 # independent results counter
        while True:
            line = self.in_file.readline().strip()

            # End of block
            if not line or line == '-3':
                break

            row_comps = min(6, self.ncomps) # amount of values written in row
            regex = '^-1\s+(\d+)' + '(.{12})' * row_comps
            match = match_line(regex, line)
            node_num = int(match.group(1))
            values = []
            for c in range(row_comps):
                m = match.group(c + 2)
                try:
                    # NaN/Inf values will be parsed
                    num = float(m)
                    if math.isinf(num):
                        num = 0.0
                        self.emitted_warning_types['Inf'] += 1
                    if math.isnan(num):
                        num = 0.0
                        self.emitted_warning_types['NaN'] += 1
                except:
                    # Too big number is written without 'E'
                    num = float(re.sub(r'(.+).([+-])(\d{3})', r'\1e\2\3', m))
                    self.emitted_warning_types['WrongFormat'] += 1
                values.append(num)

            # Result could be multiline
            for j in range((self.ncomps-1)//6):
                row_comps = min(6, self.ncomps-6*(j+1)) # amount of values written in row
                line = self.in_file.readline().strip()
                regex = '^-2\s+' + '(.{12})' * row_comps
                match = match_line(regex, line)
                values.extend([float(match.group(c+1)) for c in range(row_comps)])

            i += 1
            if node_num in renumbered_nodes:
                point_num = renumbered_nodes[node_num]
            else:
                point_num = self.data_array.GetNumberOfTuples()
            self.set_point_values(point_num, values)

    def get_some_log(self):
        v = self.data_array.GetNumberOfTuples()
        if self.inc < 1:
            time_str = 'time {:.2e}, '.format(self.inc)
        else:
            time_str = 'time {:.1f}, '.format(self.inc)
        txt = 'Step {}, '.format(self.step) + time_str \
            + '{}, '.format(self.name) \
            + '{} components, '.format(len(self.components)) \
            + '{} values'.format(v)
        if v:
            self.messages.append((logging.INFO, txt))
        else:
            self.messages.append((logging.WARNING, txt))

        if v > self.node_block.numnod:
            txt = 'Truncating {} data. More values than nodes.'.format(self.name)
            self.messages.append((logging.WARNING, txt))

        for k,v in self.emitted_warning_types.items():
            if v > 0:
                txt = '{} {} values are converted to 0.0'.format(v, k)
                self.messages.append((logging.WARNING, txt))

    def has_results(self):
        v = self.data_array.GetNumberOfTuples()
        if v and len(self.components):
            return True
        return False




"""Main class and functions."""


class Converter:
    """Main class.
    Converts CalculiX .frd file to .vtk (ASCII) or .vtu (XML) format:

    python3 ccx2paraview.py ../examples/other/Ihor_Mirzov_baffle_2D.frd vtk
    python3 ccx2paraview.py ../examples/other/Ihor_Mirzov_baffle_2D.frd vtu

    To implement large file parsing we need a step-by-step reader and writer.
    """

    def __init__(self, frd_file_name, fmt_list,
                parseonly=False, nomises=False, noeigen=False):
        self.frd_file_name = frd_file_name
        self.fmt_list = ['.' + fmt.lower() for fmt in fmt_list] # ['.vtk', '.vtu']
        self.parseonly = parseonly
        self.nomises = nomises
        self.noeigen = noeigen
        self.in_file = None     # path to the .frd-file to be read
        self.node_block = None  # node block
        self.elem_block = None  # elements block
        self.steps_increments = [] # [(step, inc), ]
        self.ugrid = vtk.vtkUnstructuredGrid() # create empty grid in VTK

    def run(self):
        """Read contents of the .frd file."""
        threads = [] # list of Threads
        logging.info('Reading ' + os.path.basename(self.frd_file_name))
        self.in_file = open(self.frd_file_name, 'r')

        # Check if file contains mesh data
        self.parse_mesh()
        if not self.has_mesh():
            return

        """For each time increment generate separate .vt* file.
        Output file name will be the same as input but with serial number.

        Threads are used to save .vt* files:
        ccx2paraview_0 - no threading at all         7m 37.5s    25m 33.7s
        ccx2paraview_1 - save files with threading   7m 44.0s    25m 32.8s
        ccx2paraview_2 - slight refactoring of 0     7m 18.0s    26m 10.2s
        ccx2paraview_3 - slight refactoring of 1     7m 25.4s    25m 1.1s
        """
        self.count_increments()
        pd = self.ugrid.GetPointData()
        for step, inc, num in self.step_inc_num(): # NOTE Could be (0, 0, '')
            for b in self.parse_step_result_blocks(step, inc): # NOTE Could be empty list []
                for (level, txt) in b.messages:
                    logging.log(level, txt)

                if b.has_results():
                    pd.Reset()
                    pd.AddArray(b.data_array)
                    pd.Modified()

            if not self.parseonly:
                for t in threads:
                    t.join() # do not start a new thread while and old one is running 
                threads.clear()
                for fmt in self.fmt_list: # ['.vtk', '.vtu']
                    file_name = self.frd_file_name[:-4] + num + fmt
                    logging.info('Writing ' + os.path.basename(file_name))
                    t = threading.Thread(target=self.write_converted_file,
                        args=(file_name, ))
                    t.start()
                    threads.append(t)

        # Write ParaView Data (PVD) for series of VTU files
        if len(self.steps_increments) > 1 and '.vtu' in self.fmt_list:
            self.write_pvd()

        self.in_file.close()
        for t in threads:
            t.join() # do not start a new thread while and old one is running 

    def parse_mesh(self):
        """Fill in unstructered grid with points and cells."""
        while True:
            line = self.in_file.readline()
            if not line:
                break
            key = line[:5].strip()

            # Nodes
            if key == '2':
                self.node_block = NodalPointCoordinateBlock(self.in_file)

            # Elements
            elif key == '3':
                self.elem_block = ElementDefinitionBlock(self.in_file)

            # Results
            if key == '100':
                self.in_file.seek(self.in_file.tell() - len(line)) # go up one line
                break

            # End
            elif key == '9999':
                break

        if self.node_block.numnod: # insert all points to the grid
            self.ugrid.SetPoints(self.node_block.points)
        if self.elem_block.numelem: # insert all cells to the grid
            self.ugrid.Allocate(self.elem_block.numelem)
            self.ugrid.SetCells(self.elem_block.types, self.elem_block.cells)

    def count_increments(self):
        """Count amount of time increments and amount of calculated variables.
        It is assumed, that there is constant set of variables calculated at 
        each time increment.
        """
        init_pos = self.in_file.tell()
        while True:
            line = self.in_file.readline()
            if not line:
                break
            key = line[:5].strip()
            # Results
            if key == '100':
                inc, step = get_inc_step(line)
                if (step, inc) not in self.steps_increments:
                    self.steps_increments.append((step, inc))
            # End
            elif key == '9999':
                break
        self.in_file.seek(init_pos)

        i = len(self.steps_increments)
        if i:
            msg = '{} time increment{}'.format(i, 's'*min(1, i-1))
            logging.info(msg)
        else:
            logging.warning('No time increments!')

    def parse_step_result_blocks(self, step, inc):
        """Header: key == '1' or key == '1P'."""
        step_result_blocks = []
        if step:
            while True:
                line = self.in_file.readline()
                if not line:
                    break
                key = line[:5].strip()

                # Read results for certain time increment
                if key == '100':
                    # logging.debug('line: ' + line)
                    got_inc, got_step = get_inc_step(line)
                    if inc != got_inc or step != got_step:
                        self.in_file.seek(self.in_file.tell() - len(line)) # go up one line
                        break

                    b = NodalResultsBlock(self.node_block)
                    b.run(self.in_file, line)
                    step_result_blocks.append(b)

                    b.get_some_log()

                    if b.name in ['S', 'E']:
                        if not self.nomises:
                            step_result_blocks.append(self.calculate_mises(b))
                        if not self.noeigen:
                            step_result_blocks.append(self.calculate_principal(b))

                # End
                elif key == '9999':
                    break

        return step_result_blocks

    def calculate_mises(self, b):
        """Append equivalent (von Mises) stress/strain."""
        b1 = NodalResultsBlock(b.node_block)
        b1.name = b.name + '_Mises'
        b1.components = (b1.name, )
        b1.ncomps = len(b1.components)
        b1.inc = b.inc
        b1.step = b.step

        # Iterate over points
        global renumbered_nodes
        for point_num in renumbered_nodes.values():
            data = b.data_array.GetTuple(point_num)
            Txx = data[0]; Tyy = data[1]; Tzz = data[2]
            Txy = data[3]; Tyz = data[4]; Txz = data[5]

            if b.name == 'S':
                # Calculate Mises stress for current node
                mises = 1 / math.sqrt(2) \
                    * math.sqrt((Txx - Tyy)**2 \
                    + (Tyy - Tzz)**2 \
                    + (Tzz - Txx)**2 \
                    + 6 * Tyz**2 \
                    + 6 * Txz**2 \
                    + 6 * Txy**2)

            if b.name == 'E':
                # Calculate Mises strain for current node
                tensor = np.array([[Txx, Txy, Txz], [Txy, Tyy, Tyz], [Txz, Tyz, Tzz]])

                # Calculate principal values for current node
                [e1, e2, e3] = np.linalg.eigvals(tensor).tolist()

                # Calculate Mises strain for current node
                mises = 2 / 3 / math.sqrt(2) \
                    * math.sqrt((e1 - e2)**2 \
                                + (e2 - e3)**2 \
                                + (e3 - e1)**2)

            b1.set_point_values(point_num, [mises])

        b1.get_some_log()
        return b1

    def calculate_principal(self, b):
        """Append tensor's eigenvalues."""
        b1 = NodalResultsBlock(b.node_block)
        b1.name = b.name + '_Principal'
        b1.components = ('Min', 'Mid', 'Max')
        b1.ncomps = len(b1.components)
        b1.inc = b.inc
        b1.step = b.step

        # Iterate over nodes
        global renumbered_nodes
        for point_num in renumbered_nodes.values():
            data = b.data_array.GetTuple(point_num)
            Txx = data[0]; Tyy = data[1]; Tzz = data[2]
            Txy = data[3]; Tyz = data[4]; Txz = data[5]
            tensor = np.array([[Txx, Txy, Txz], [Txy, Tyy, Tyz], [Txz, Tyz, Tzz]])

            # Calculate principal values for current node
            eigenvalues = np.linalg.eigvals(tensor).tolist()
            b1.set_point_values(point_num, sorted(eigenvalues))

        b1.get_some_log()
        return b1

    def has_mesh(self):
        blocks = [self.node_block, self.elem_block]
        if all([b is not None for b in blocks]):
            return True
        logging.warning('File is empty!')
        return False

    def step_inc_num(self):
        """If model has many time increments - many output files
        will be created. Each output file's name should contain
        increment number padded with zero. In this method file_name
        has no extension.
        """
        i = len(self.steps_increments)
        if not i:
            return [(0, 0, '')]
        d = [] # [(step, inc, num), ]
        for counter, (step, inc) in enumerate(self.steps_increments):
            if i > 1:
                num = '.{:0{width}}'.format(counter+1, width=len(str(i)))
            else:
                num = ''
            d.append((step, inc, num)) # without extension
        return d

    def write_converted_file(self, file_name):
        """Writes .vtk and .vtu files based on data from FRD object.
        Uses VTK Python package.
        Writes results for one time increment only.

        NOTE Ugrid always has a mesh - it isn't effective
        writer = vtk.vtkEnSightWriter()
        writer.SetInputData(self.ugrid)
        writer.SetTransientGeometry()
        """
        if file_name.endswith('.vtk'):
            writer = vtk.vtkUnstructuredGridWriter()
            writer.SetInputData(self.ugrid)
        elif file_name.endswith('.vtu'):
            writer = vtk.vtkXMLUnstructuredGridWriter()
            writer.SetInputDataObject(self.ugrid)
            writer.SetDataModeToBinary() # compressed file
        writer.SetFileName(file_name)
        writer.Write()

    def write_pvd(self):
        """Writes ParaView Data (PVD) file for series of VTU files."""
        with open(self.frd_file_name[:-4] + '.pvd', 'w') as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">\n')
            f.write('\t<Collection>\n')

            for step, inc, num in self.step_inc_num():
                file_name = os.path.basename(self.frd_file_name[:-4]) + num
                f.write('\t\t<DataSet file="{}.vtu" timestep="{}"/>\n'\
                    .format(os.path.basename(file_name), inc))

            f.write('\t</Collection>\n')
            f.write('</VTKFile>')


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('filename', type=str, help='FRD file name with extension')
    ap.add_argument('format', type=str, nargs='+', help='output format: vtk, vtu')
    ap.add_argument('-parseonly', type=bool, default=False, help='do not write output, only parse')
    ap.add_argument('-nomises', type=bool, default=False, help='do not append Mises stress/strain')
    ap.add_argument('-noeigen', type=bool, default=False, help='do not append principal stress/strain')
    args = ap.parse_args()

    # Check arguments
    assert os.path.isfile(args.filename), 'FRD file does not exist.'
    for a in args.format:
        msg = 'Wrong format "{}". '.format(a) + 'Choose between: vtk, vtu.'
        assert a in ('vtk', 'vtu'), msg

    # Create converter and run it
    ccx2paraview = Converter(args.filename, args.format, args.parseonly,
                            args.nomises, args.noeigen)
    ccx2paraview.run()


if __name__ == '__main__':
    clean_screen()
    main()
