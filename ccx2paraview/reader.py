#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
© Lukas Bante, 2017 - original code https://gitlab.lrz.de/snippets/238
© Ihor Mirzov, 2019-2020 - bugfix, refactoring and improvement
Distributed under GNU General Public License v3.0

This module contains classes for reading CalculiX .frd files """

import re
import math
import logging

import numpy as np


class Node:
    """A single node object."""

    def __init__(self, num, coords):
        self.num = num
        self.coords = coords


class Element:
    """A single finite element object."""

    def __init__(self, num, etype, nodes):
        self.num = num
        self.type = etype
        self.nodes = nodes


class NodalPointCoordinateBlock:
    """Nodal Point Coordinate Block: cgx_2.17 Manual, § 11.3."""

    def __init__(self, in_file):
        """Read nodal coordinates."""
        line = read_byte_line(in_file)
        self.nodes = {} # dictionary with nodes {num:Node}
        while True:
            line = read_byte_line(in_file)

            # End of block
            if line == '-3':
                break

            regex = '^-1(.{10})' + '(.{12})'*3
            match = read_line(regex, line)
            node_number = int(match.group(1))
            node_coords = [ float(match.group(2)),
                            float(match.group(3)),
                            float(match.group(4)), ]
            self.nodes[node_number] = Node(node_number, node_coords)
            # logging.debug('Node {}: {}'.format(node_number, node_coords))

        self.numnod = len(self.nodes) # number of nodes in this block
        logging.info('{} nodes'.format(self.numnod)) # total number of nodes


class ElementDefinitionBlock:
    """Element Definition Block: cgx_2.17 Manual, § 11.4."""

    def __init__(self, in_file):
        """Read elements."""
        self.in_file = in_file
        line = read_byte_line(in_file)
        self.elements = [] # list of Element objects

        while True:
            line = read_byte_line(in_file)

            # End of block
            if line == '-3':
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
        # num_nodes = self.amount_of_nodes_in_frd_element(element_type)
        for j in range(self.num_lines(element_type)):
            line = read_byte_line(self.in_file)
            nodes = [int(n) for n in line.split()[1:]]
            element_nodes.extend(nodes)

        # logging.debug('Element {}: {}'.format(element_num, element_nodes))
        elem = Element(element_num, element_type, element_nodes)
        self.elements.append(elem)

    def amount_of_nodes_in_frd_element(self, etype):
        """Amount of nodes in frd element.
        First value is meaningless, since elements are 1-based.
        """
        return (0, 8, 6, 4, 20, 15, 10, 3, 6, 4, 8, 2, 3)[etype]

    def num_lines(self, etype):
        """Amount of lines in element connectivity definition.
        First value is meaningless, since elements are 1-based.
        """
        return (0, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1)[etype]


class NodalResultsBlock:
    """Nodal Results Block: cgx_2.17 Manual, § 11.6."""

    def __init__(self):
        """Read calculated values."""
        self.components = [] # component names
        self.results = {} # dictionary with nodal result {node:data}
        self.name = None
        self.value = 0
        self.ncomps = 0
        self.numstep = 0

    def run(self, in_file, node_block):
        self.in_file = in_file
        self.node_block = node_block

        self.read_step_info()
        self.read_vars_info()
        self.read_components_info()
        results_counter = self.read_nodal_results()
        # self.append_stresses() # append Mises and principal stresses
        # self.append_strains() # append principal strains

        if self.value < 1:
            time_str = 'time {:.2e}, '.format(self.value)
        else:
            time_str = 'time {:.1f}, '.format(self.value)
        txt = 'Step {}, '.format(self.numstep) + time_str \
            + '{}, '.format(self.name) \
            + '{} components, '.format(len(self.components)) \
            + '{} values'.format(results_counter)
        logging.info(txt)

    def read_step_info(self):
        """Read step information
        CL  101 0.36028E+01         320                     3    1           1
        CL  101 1.000000000         803                     0    1           1
        CL  101 1.000000000          32                     0    1           1
        CL  102 117547.9305          90                     2    2MODAL      1
        """
        line = read_byte_line(self.in_file)[7:]
        regex = '^(.{12})\s+\d+\s+\d+\s+(\d+)'
        match = read_line(regex, line)
        self.value = float(match.group(1)) # could be frequency, time or any numerical value
        self.numstep = int(match.group(2)) # step number

    def read_vars_info(self):
        """Read variables information
        -4  V3DF        4    1
        -4  DISP        4    1
        -4  STRESS      6    1
        -4  DOR1  Rx    4    1
        """
        line = read_byte_line(self.in_file)[4:]
        regex = '^(\w+)' + '\D+(\d+)'*2
        match = read_line(regex, line)
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
            line = read_byte_line(self.in_file)[4:]
            regex = '^\w+'
            match = read_line(regex, line)

            # Exclude variable name from the component name: SXX->XX, EYZ->YZ
            component_name = match.group(0)
            if component_name.startswith(self.name):
                component_name = component_name[len(self.name):]

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
            line = read_byte_line(self.in_file)

            # End of block
            if line == '-3':
                break

            row_comps = min(6, self.ncomps) # amount of values written in row
            regex = '^-1\s+(\d+)' + '(.{12})' * row_comps
            match = read_line(regex, line)
            node = int(match.group(1))
            data = []
            for c in range(row_comps):
                m = match.group(c + 2)
                try:
                    # NaN/Inf values will be parsed
                    num = float(m)
                    if ('NaN' in m or 'Inf' in m):
                        emitted_warning_types['NaNInf'] += 1
                except Exception as e:
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
                line = read_byte_line(self.in_file)
                regex = '^-2\s+' + '(.{12})' * row_comps
                match = read_line(regex, line)
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

    def reshape9(self):
        """All 9 tensor components."""
        self.ncomps = 9
        xx = self.components[0]
        yy = self.components[1]
        zz = self.components[2]
        xy = self.components[3]
        yz = self.components[4]
        xz = self.components[5]
        self.components = [
            xx, xy, xz,
            xy, yy, yz,
            xz, yz, zz]
        for node_num in self.node_block.nodes.keys():
            data = self.results[node_num]
            xx = data[0]; yy = data[1]; zz = data[2]
            xy = data[3]; yz = data[4]; xz = data[5]
            self.results[node_num] = [
                xx, xy, xz,
                xy, yy, yz,
                xz, yz, zz]

    """
    Append Mises and principal stresses
    NOTE DEPRECATED
    def append_stresses(self):
        if self.name == 'S':
            try:
                component_names = (
                    'Mises',
                    'Min Principal',
                    'Mid Principal',
                    'Max Principal')
                for i in range(len(component_names)):
                    self.components.append(component_names[i])
                    self.ncomps += 1

                # Iterate over nodes
                for node_num in self.node_block.nodes.keys():
                    data = self.results[node_num] # list with results for current node
                    Sxx = data[0]; Syy = data[1]; Szz = data[2]
                    Sxy = data[3]; Syz = data[4]; Sxz = data[5]
                    tensor = np.array([[Sxx, Sxy, Sxz], [Sxy, Syy, Syz], [Sxz, Syz, Szz]])

                    # Calculate Mises stress for current node
                    mises = 1 / math.sqrt(2) *\
                        math.sqrt(  (Sxx - Syy)**2 +\
                                    (Syy - Szz)**2 +\
                                    (Szz - Sxx)**2 +\
                                    6 * Syz**2 +\
                                    6 * Sxz**2 +\
                                    6 * Sxy**2)
                    self.results[node_num].append(mises)

                    # Calculate principal stresses for current node
                    for ps in np.linalg.eigvalsh(tensor).tolist():
                        self.results[node_num].append(ps)

            except:
                logging.error('Additional stresses will not be appended.')
    """

    """
    Append principal strains
    NOTE DEPRECATED
    def append_strains(self):
        if self.name == 'E':
            try:
                component_names = (
                    'Mises',
                    'Min Principal',
                    'Mid Principal',
                    'Max Principal',
                    )
                for i in range(len(component_names)):
                    self.components.append(component_names[i])
                    self.ncomps += 1

                # Iterate over nodes
                for node_num in self.node_block.nodes.keys():
                    data = self.results[node_num] # list with results for current node
                    Exx = data[0]; Eyy = data[1]; Ezz = data[2]
                    Exy = data[3]; Eyz = data[4]; Exz = data[5]
                    tensor = np.array([[Exx, Exy, Exz], [Exy, Eyy, Eyz], [Exz, Eyz, Ezz]])

                    # Calculate Mises strain for current node
                    mises = math.sqrt(2)/3 *\
                        math.sqrt(   (Exx - Eyy)**2 +\
                                (Eyy - Ezz)**2 +\
                                (Ezz - Exx)**2 +\
                                6 * Eyz**2 +\
                                6 * Exz**2 +\
                                6 * Exy**2)
                    self.results[node_num].append(mises)

                    # Calculate principal strains for current node
                    for ps in np.linalg.eigvalsh(tensor).tolist():
                        self.results[node_num].append(ps)

            except:
                logging.error('Additional strains will not be appended.')
    """


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
            with open(file_name, 'rb') as in_file:
                key = in_file.read(5).decode().strip()
                while key:
                    # Header
                    if key == '1' or key == '1P':
                        read_byte_line(in_file)

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
                        b = NodalResultsBlock()
                        b.run(in_file, self.node_block)
                        self.result_blocks.append(b)
                        if b.name == 'S':
                            b1 = self.calculate_mises_stress(b)
                            b2 = self.calculate_principal(b)
                            self.result_blocks.extend([b1,b2])
                            # b.reshape9()
                        if b.name == 'E':
                            b1 = self.calculate_mises_strain(b)
                            b2 = self.calculate_principal(b)
                            self.result_blocks.extend([b1,b2])
                            # b.reshape9()

                    # End
                    elif key == '9999':
                        break

                    key = in_file.read(5).decode().strip()

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
            tensor = np.array([[Sxx, Sxy, Sxz], [Sxy, Syy, Syz], [Sxz, Syz, Szz]])

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
            tensor = np.array([[Sxx, Sxy, Sxz], [Sxy, Syy, Syz], [Sxz, Syz, Szz]])

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


def read_byte_line(f):
    """Read byte line and decode: return None after EOF."""

    # Check EOF
    byte = f.read(1)
    if not byte:
        return None

    # Convert first byte
    try:
        line = byte.decode()
    except UnicodeDecodeError:
        line = ' ' # replace endecoded symbols with space

    # Continue reading until EOF or new line
    while byte != b'\n':
        byte = f.read(1)
        if not byte:
            return line.strip() # EOF
        try:
            line += byte.decode()
        except UnicodeDecodeError:
            line += ' ' # replace endecoded symbols with space

    return line.strip()


def read_line(regex, line):
    """Search regex in line and report problems."""
    match = re.search(regex, line)
    if match:
        return match
    else:
        logging.error('Can\'t parse line:\n{}\nwith regex:\n{}'\
            .format(line, regex))
        raise Exception
