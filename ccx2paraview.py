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
import sys
import logging
import argparse
import shutil
import math
import re

# External imports
import numpy as np
import vtk




"""Writer class and functions."""


def convert_elem_type(frd_elem_type):
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


def get_element_connectivity(renumbered_nodes, e):
    """Element connectivity with renumbered nodes."""
    connectivity = []

    # frd: 20 node brick element
    if e.type == 4:
        # Last eight nodes have to be repositioned
        r1 = tuple(range(12)) # 8,9,10,11
        r2 = tuple(range(12, 16)) # 12,13,14,15
        r3 = tuple(range(16, 20)) # 16,17,18,19
        node_num_list = r1 + r3 + r2
        for i in node_num_list:
            node = renumbered_nodes[e.nodes[i]] # node after renumbering
            connectivity.append(node)

    # frd: 15 node penta element
    elif e.type==5 or e.type==2:
        """CalculiX elements type 5 are not supported in VTK and
        has to be processed as CalculiX type 2 (6 node wedge,
        VTK type 13). Additional nodes are omitted.
        """
        for i in [0,2,1,3,5,4]: # repositioning nodes
            node = renumbered_nodes[e.nodes[i]] # node after renumbering
            connectivity.append(node)

    # All other elements
    else:
        n = len(e.nodes)
        for i in range(n):
            node = renumbered_nodes[e.nodes[i]] # node after renumbering
            connectivity.append(node)

    return connectivity


def amount_of_nodes_in_vtk_element(e):
    """Amount of nodes in element: needed to calculate offset
    Node offset is an index in the connectivity DataArray
    """
    # frd: 20 node brick element
    if e.type == 4:
        n = 20

    # frd: 15 node penta element
    elif e.type==5 or e.type==2:
        n = 6

    # All other elements
    else:
        n = len(e.nodes)

    return n


def generate_ugrid(frd):
    """Generate VTK mesh."""
    ugrid = vtk.vtkUnstructuredGrid() # create empty grid in VTK

    # POINTS section
    # Nodes should be renumbered starting from 0
    points = vtk.vtkPoints()
    renumbered_nodes = {} # old_number : new_number
    new_node_number = 0
    for n in sorted(frd.node_block.nodes.keys()):
        renumbered_nodes[n] = new_node_number
        coordinates = frd.node_block.nodes[n].coords
        points.InsertPoint(new_node_number, coordinates)
        new_node_number += 1
        if new_node_number == frd.node_block.numnod:
            break
    ugrid.SetPoints(points) # insert all points to the grid

    # CELLS section - elements connectyvity
    # Sometimes element nodes should be repositioned
    ugrid.Allocate(frd.elem_block.numelem)
    for e in sorted(frd.elem_block.elements, key=lambda x: x.num):
        vtk_elem_type = convert_elem_type(e.type)
        offset = amount_of_nodes_in_vtk_element(e)
        connectivity = get_element_connectivity(renumbered_nodes, e)
        ugrid.InsertNextCell(vtk_elem_type, offset, connectivity)

    return ugrid


def convert_frd_data_to_vtk(b, numnod):
    """Convert parsed FRD data to vtkDoubleArray."""
    data_array = vtk.vtkDoubleArray()
    data_array.SetName(b.name)
    data_array.SetNumberOfComponents(len(b.components))
    data_array.SetNumberOfTuples(numnod)

    # Set component names
    for i,c in enumerate(b.components):
        if 'SDV' in c:
            data_array.SetComponentName(i, i)
        else:
            data_array.SetComponentName(i, c)

    # Some warnings repeat too much time - mark them
    emitted_warning_types = {'Inf':0, 'NaN':0}

    # Assign data
    nodes = sorted(b.results.keys())[:numnod]
    for i,n in enumerate(nodes):
        node_values = b.results[n]
        for j,r in enumerate(node_values):
            if math.isinf(r):
                node_values[j] = 0.0
                emitted_warning_types['Inf'] += 1
            if math.isnan(r):
                node_values[j] = 0.0
                emitted_warning_types['NaN'] += 1
        data_array.InsertTuple(i, node_values)

    for k,v in emitted_warning_types.items():
        if v > 0:
            logging.warning('{} {} values are converted to 0.0'.format(v, k))

    return data_array


class Writer:
    """Writes .vtk and .vtu files based on data from FRD object.
    Uses native VTK Python package.
    """

    def __init__(self, frd, file_name, time):
        """Main function: frd is a FRD object."""
        self.file_name = file_name
        self.ugrid = generate_ugrid(frd)
        pd = self.ugrid.GetPointData()

        # POINT DATA - from here start all the results
        for b in frd.result_blocks: # iterate over NodalResultsBlock (increments)
            if b.value == time: # write results for one time increment only
                if len(b.results) and len(b.components):
                    print_some_log(b)

                    da = convert_frd_data_to_vtk(b, frd.node_block.numnod)
                    pd.AddArray(da)
                    pd.Modified()
                else:
                    logging.warning(b.name + ' - no data for this increment')

    def write_vtk(self):
        writer = vtk.vtkUnstructuredGridWriter()
        writer.SetInputData(self.ugrid)
        writer.SetFileName(self.file_name)
        writer.Write()

    def write_vtu(self):
        writer = vtk.vtkXMLUnstructuredGridWriter()
        writer.SetInputDataObject(self.ugrid)
        # writer.SetDataModeToAscii() # text file
        writer.SetDataModeToBinary() # compressed file
        writer.SetFileName(self.file_name)
        writer.Write()




"""Classes for reading CalculiX .frd files."""


class Node:
    """A single node object."""

    def __init__(self, num, coords):
        # logging.debug('Node {}: {}'.format(num, coords))
        self.num = num
        self.coords = coords


class Element:
    """A single finite element object."""

    def __init__(self, num, etype, nodes):
        # txt = 'Element {}, type {}: {}'.format(num, etype, nodes)
        # logging.debug(txt)
        self.num = num
        self.type = etype
        self.nodes = nodes


class NodalPointCoordinateBlock:
    """Nodal Point Coordinate Block: cgx_2.20.pdf Manual, § 11.3."""

    def __init__(self, in_file):
        """Read nodal coordinates."""
        self.nodes = {} # dictionary with nodes {num:Node}
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
            self.nodes[node_number] = Node(node_number, node_coords)

        self.numnod = len(self.nodes) # number of nodes in this block
        logging.info('{} nodes'.format(self.numnod)) # total number of nodes


class ElementDefinitionBlock:
    """Element Definition Block: cgx_2.20.pdf Manual, § 11.4."""

    def __init__(self, in_file):
        """Read elements."""
        self.in_file = in_file
        self.elements = [] # list of Element objects

        while True:
            line = in_file.readline().strip()

            # End of block
            if not line or line == '-3':
                break

            self.read_element(line)

        self.numelem = len(self.elements) # number of elements in this block
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
        element_num = int(line.split()[1])
        element_type = int(line.split()[2])
        element_nodes = []
        for j in range(self.num_lines(element_type)):
            line = self.in_file.readline().strip()
            nodes = [int(n) for n in line.split()[1:]]
            element_nodes.extend(nodes)

        elem = Element(element_num, element_type, element_nodes)
        self.elements.append(elem)

    def num_lines(self, etype):
        """Amount of lines in element connectivity definition.
        First value is meaningless, since elements are 1-based.
        """
        return (0, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1)[etype]


class NodalResultsBlock:
    """Nodal Results Block: cgx_2.20.pdf Manual, § 11.6."""

    def __init__(self, line=''):
        """Read calculated values."""
        self.components = [] # component names
        self.results = {} # dictionary with nodal result {node:data}
        self.name = None
        self.value = 0
        self.ncomps = 0
        self.numstep = 0
        self.line = line

    def run(self, in_file, node_block):
        self.in_file = in_file
        self.node_block = node_block

        self.read_step_info()
        self.read_vars_info()
        self.read_components_info()
        results_counter = self.read_nodal_results()
        print_some_log(self, results_counter)

    def read_step_info(self):
        """Read step information
        CL  101 0.36028E+01         320                     3    1           1
        CL  101 1.000000000         803                     0    1           1
        CL  101 1.000000000          32                     0    1           1
        CL  102 117547.9305          90                     2    2MODAL      1
        """
        line = self.line[12:]
        regex = '^(.{12})\s+\d+\s+\d+\s+(\d+)'
        match = match_line(regex, line)
        self.value = float(match.group(1)) # could be frequency, time or any numerical value
        self.numstep = int(match.group(2)) # step number
        # txt = 'Step info: value {}, numstep {}' \
        #     .format(self.value, self.numstep)
        # logging.debug(txt)

    def read_vars_info(self):
        """Read variables information
        -4  V3DF        4    1
        -4  DISP        4    1
        -4  STRESS      6    1
        -4  DOR1  Rx    4    1
        """
        line = self.in_file.readline().strip()
        regex = '^-4\s+(\w+)' + '\D+(\d+)'*2
        match = match_line(regex, line)
        self.ncomps = int(match.group(2)) # amount of components

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
        # txt = 'Vars info: name {}, ncomps {}' \
        #     .format(self.name, self.ncomps)
        # logging.debug(txt)
        if self.name in inpname:
            self.name = inpname[self.name]

    def read_components_info(self):
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
        for i in range(self.ncomps):
            line = self.in_file.readline()[5:]
            regex = '^\w+'
            match = match_line(regex, line)

            # Exclude variable name from the component name: SXX->XX, EYZ->YZ
            component_name = match.group(0)
            if component_name.startswith(self.name):
                component_name = component_name[len(self.name):]
            # logging.debug('Component name ' + component_name)

            if 'ALL' in component_name:
                self.ncomps -= 1
            else:
                self.components.append(component_name)

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
        for node_num in self.node_block.nodes.keys():
            self.results[node_num] = [0]*self.ncomps

        # Some warnings repeat too much time - mark them
        before = ''
        after = None
        emitted_warning_types = {'NaNInf':0, 'WrongFormat':0}

        results_counter = 0 # independent results counter
        while True:
            line = self.in_file.readline().strip()

            # End of block
            if not line or line == '-3':
                break

            row_comps = min(6, self.ncomps) # amount of values written in row
            regex = '^-1\s+(\d+)' + '(.{12})' * row_comps
            match = match_line(regex, line)
            node = int(match.group(1))
            data = []
            for c in range(row_comps):
                m = match.group(c + 2)
                try:
                    # NaN/Inf values will be parsed
                    num = float(m)
                    if ('NaN' in m or 'Inf' in m):
                        emitted_warning_types['NaNInf'] += 1
                except:
                    # Too big number is written without 'E'
                    num = float(re.sub(r'(.+).([+-])(\d{3})', r'\1e\2\3', m))
                    emitted_warning_types['WrongFormat'] += 1
                    before = m
                    after = num
                data.append(num)

            results_counter += 1
            self.results[node] = data

            # Result could be multiline
            for j in range((self.ncomps-1)//6):
                row_comps = min(6, self.ncomps-6*(j+1)) # amount of values written in row
                line = self.in_file.readline().strip()
                regex = '^-2\s+' + '(.{12})' * row_comps
                match = match_line(regex, line)
                data = [float(match.group(c+1)) for c in range(row_comps)]
                self.results[node].extend(data)

            # logging.debug('Node {}: {}'.format(node, self.results[node]))

        if emitted_warning_types['NaNInf']:
            logging.warning('NaN and Inf are not supported in Paraview ({} warnings).'\
                .format(emitted_warning_types['NaNInf']))
        if emitted_warning_types['WrongFormat']:
            logging.warning('Wrong format, {} -> {} ({} warnings).'\
                .format(before.strip(), after, emitted_warning_types['WrongFormat']))
        return results_counter


class FRD:
    """Main class."""

    def __init__(self, file_name=None):
        """Read contents of the .frd file."""
        self.file_name = None   # path to the .frd-file to be read
        self.node_block = None  # node block
        self.elem_block = None  # elements block
        self.result_blocks = [] # all result blocks in order of appearance
        if file_name:
            self.file_name = file_name
            with open(file_name, 'r') as in_file:
                while True:
                    line = in_file.readline()
                    if not line:
                        break

                    key = line[:5].strip()

                    # Header
                    if key == '1' or key == '1P':
                        # in_file.readline()
                        pass

                    # Nodes
                    elif key == '2':
                        block = NodalPointCoordinateBlock(in_file)
                        self.node_block = block

                    # Elements
                    elif key == '3':
                        block = ElementDefinitionBlock(in_file)
                        self.elem_block = block

                    # Results
                    elif key == '100':
                        b = NodalResultsBlock(line)
                        b.run(in_file, self.node_block)
                        self.result_blocks.append(b)
                        if b.name == 'S':
                            b1 = self.calculate_mises_stress(b)
                            b2 = self.calculate_principal(b)
                            self.result_blocks.extend([b1,b2])
                        if b.name == 'E':
                            b1 = self.calculate_mises_strain(b)
                            b2 = self.calculate_principal(b)
                            self.result_blocks.extend([b1,b2])

                    # End
                    elif key == '9999':
                        break

            self.times = [b.value for b in self.result_blocks]
            self.times = sorted(set(self.times))
            l = len(self.times)
            if l:
                msg = '{} time increment{}'.format(l, 's'*min(1, l-1))
                logging.info(msg)
            else:
                logging.warning('No time increments!')

    def calculate_mises_stress(self, b):
        """Append von Mises stress."""
        b1 = NodalResultsBlock()
        b1.name = 'S_Mises'
        b1.components = (b1.name, )
        b1.ncomps = len(b1.components)
        b1.value = b.value
        b1.numstep = b.numstep

        # Iterate over nodes
        for node_num in b.node_block.nodes.keys():
            data = b.results[node_num] # list with results for current node
            Sxx = data[0]; Syy = data[1]; Szz = data[2]
            Sxy = data[3]; Syz = data[4]; Sxz = data[5]

            # Calculate Mises stress for current node
            mises = 1 / math.sqrt(2) \
                * math.sqrt((Sxx - Syy)**2 \
                + (Syy - Szz)**2 \
                + (Szz - Sxx)**2 \
                + 6 * Syz**2 \
                + 6 * Sxz**2 \
                + 6 * Sxy**2)
            b1.results[node_num] = [mises]

        return b1

    def calculate_mises_strain(self, b):
        """Append von Mises equivalent strain."""
        b1 = NodalResultsBlock()
        b1.name = 'E_Mises'
        b1.components = (b1.name,)
        b1.ncomps = len(b1.components)
        b1.value = b.value
        b1.numstep = b.numstep

        # Iterate over nodes
        for node_num in b.node_block.nodes.keys():
            data = b.results[node_num] # list with results for current node
            Sxx = data[0]; Syy = data[1]; Szz = data[2]
            Sxy = data[3]; Syz = data[4]; Sxz = data[5]

            # Calculate Mises stress for current node
            mises = 1 / math.sqrt(2) \
                * math.sqrt((Sxx - Syy)**2 \
                + (Syy - Szz)**2 \
                + (Szz - Sxx)**2 \
                + 6 * Syz**2 \
                + 6 * Sxz**2 \
                + 6 * Sxy**2)
            b1.results[node_num] = [mises]

        return b1

    def calculate_principal(self, b):
        """Append tensor's eigenvalues."""
        b1 = NodalResultsBlock()
        b1.name = b.name + '_Principal'
        b1.components = ('Min', 'Mid', 'Max')
        b1.ncomps = len(b1.components)
        b1.value = b.value
        b1.numstep = b.numstep

        # Iterate over nodes
        for node_num in b.node_block.nodes.keys():
            data = b.results[node_num] # list with results for current node
            Txx = data[0]; Tyy = data[1]; Tzz = data[2]
            Txy = data[3]; Tyz = data[4]; Txz = data[5]
            tensor = np.array([[Txx, Txy, Txz], [Txy, Tyy, Tyz], [Txz, Tyz, Tzz]])

            # Calculate principal values for current node
            b1.results[node_num] = []
            for ps in sorted(np.linalg.eigvals(tensor).tolist()):
                b1.results[node_num].append(ps)

        return b1


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




"""Utility functions."""


def screen():
    """Clean screen."""
    os.system('cls' if os.name=='nt' else 'clear')


def cache(folder=None):
    """Recursively delete cached files in all subfolders."""
    if not folder:
        folder = os.getcwd()
    pycache = os.path.join(folder, '__pycache__')
    if os.path.isdir(pycache):
        shutil.rmtree(pycache) # works in Linux as in Windows

    # Recursively clear cache in child folders
    try:
        for f in os.scandir(folder):
            if f.is_dir():
                cache(f.path)
    except PermissionError:
        print('ERROR: Insufficient permissions for ' + folder)


def files(startFolder=None):
    """Cleaup trash files in startFolder and all subfolders."""
    extensions = (  '.12d', '.cvg', '.dat', '.vwf', '.out', '.nam', '.inp1', '.inp2',
                    '.sta', '.equ', '.eig', '.stm', '.mtx', '.net', '.inp0', '.rin',
                    '.fcv', 'dummy' )
    if not startFolder:
        startFolder = os.getcwd()
    for f in os.scandir(startFolder):
        if f.is_dir(): # if folder
            files(f.path)
        elif f.is_file() and f.name.endswith(extensions):
            try:
                os.remove(f.path)
                sys.__stdout__.write('Delelted: ' + f.path + '\n')
            except:
                sys.__stdout__.write(f.path + ': ' + sys.exc_info()[1][1] + '\n')


def results():
    """Cleaup old result files."""
    extensions = ('.frd', '.vtk', '.vtu')
    for f in os.scandir('.'):
        if f.name.endswith(extensions):
            try:
                os.remove(f.path)
                sys.__stdout__.write('Delelted: ' + f.path + '\n')
            except:
                sys.__stdout__.write(f.path + ': ' + sys.exc_info()[1][1] + '\n')


def print_some_log(b, results_counter=None):
    """b is a results block."""
    if results_counter is None:
        results_counter = len(b.results)
    if b.value < 1:
        time_str = 'time {:.2e}, '.format(b.value)
    else:
        time_str = 'time {:.1f}, '.format(b.value)
    txt = 'Step {}, '.format(b.numstep) + time_str \
        + '{}, '.format(b.name) \
        + '{} components, '.format(len(b.components)) \
        + '{} values'.format(results_counter)
    logging.info(txt)




"""Main class."""


class Converter:
    """Converts CalculiX .frd-file to .vtk (ASCII) or .vtu (XML) format:
    python3 ccx2paraview.py ../examples/other/Ihor_Mirzov_baffle_2D.frd vtk
    python3 ccx2paraview.py ../examples/other/Ihor_Mirzov_baffle_2D.frd vtu
    """

    def __init__(self, file_name, fmt_list):
        self.file_name = file_name
        self.fmt_list = fmt_list
        self.times_names = {}  # {increment time: file name, ...}

    def run(self):
        # Read FRD-file
        base_name = os.path.basename(self.file_name)
        logging.info('Reading ' + base_name)
        frd = FRD(self.file_name)

        # If file does not contain mesh data
        if not frd.node_block or not frd.elem_block:
            logging.warning('File is empty!')
            return

        l = len(frd.times)
        for fmt in self.fmt_list:
            if l:
                """If model has many time steps - many output files
                will be created. Each output file's name should contain
                increment number padded with zero.
                """
                print()
                counter = 1
                for t in frd.times:
                    if l > 1:
                        ext = '.{:0{width}}.{}'.format(
                            counter, fmt, width=len(str(l))
                        )
                        file_name = self.file_name.replace('.frd', ext)
                    else:
                        ext = '.{}'.format(fmt)
                        file_name = self.file_name.replace('.frd', ext)
                    self.times_names[t] = file_name
                    counter += 1

                """For each time increment generate separate .vt* file
                Output file name will be the same as input.
                """
                for t, file_name in self.times_names.items():
                    base_name = os.path.basename(file_name)
                    logging.info('Writing ' + base_name)
                    self.run_writer(frd, file_name, t, fmt)

                # Write ParaView Data (PVD) for series of VTU files
                if l > 1 and fmt == 'vtu':
                    self.write_pvd()

            else:
                """FRD has no step data - only mesh."""
                file_name = self.file_name[:-3] + fmt
                self.run_writer(frd, file_name, None, fmt)

    def write_pvd(self):
        """Writes ParaView Data (PVD) file for series of VTU files."""
        with open(self.file_name[:-4] + '.pvd', 'w') as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">\n')
            f.write('\t<Collection>\n')

            for t, n in self.times_names.items():
                f.write('\t\t<DataSet file="{}" timestep="{}"/>\n'\
                    .format(os.path.basename(n), t))

            f.write('\t</Collection>\n')
            f.write('</VTKFile>')

    def run_writer(self, frd, file_name, time_inc, fmt):
        w = Writer(frd, file_name, time_inc)
        if fmt == 'vtk':
            w.write_vtk()
        if fmt == 'vtu':
            w.write_vtu()


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('filename', type=str, help='FRD file name with extension')
    ap.add_argument('format', type=str, nargs='+', help='output format: vtk, vtu')
    args = ap.parse_args()

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
        msg = 'ERROR! Wrong format "{}". '.format(a) + 'Choose between: vtk, vtu.'
        print(msg)

    cache()


if __name__ == '__main__':
    screen()
    main()
