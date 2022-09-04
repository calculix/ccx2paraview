#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
© Lukas Bante, 2017 - original code https://gitlab.lrz.de/snippets/238
© Ihor Mirzov, 2019-2022 - bugfix, refactoring and improvement
Distributed under GNU General Public License v3.0

This module contains classes for reading CalculiX .frd files """

import re
import math
import logging

import numpy as np

from utils import print_some_log


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
    """Element Definition Block: cgx_2.17 Manual, § 11.4."""

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

        # txt = 'Element {}, type {}: {}' \
        #     .format(element_num, element_type, element_nodes)
        # logging.debug(txt)
        elem = Element(element_num, element_type, element_nodes)
        self.elements.append(elem)

    def num_lines(self, etype):
        """Amount of lines in element connectivity definition.
        First value is meaningless, since elements are 1-based.
        """
        return (0, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1)[etype]


class NodalResultsBlock:
    """Nodal Results Block: cgx_2.17 Manual, § 11.6."""

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
        # logging.debug('value {}, numstep {}'.format(self.value, self.numstep))

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
        # logging.debug('Name {}, ncomps {}'.format(self.name, self.ncomps))
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


class Reader:
    """To implement large file parsing we need a step-by-step
    reader and writer. For now the whole file is being parsed,
    then written, which need more memory."""

    def __init__(self) -> None:
        pass

    def get_file_info(self):
        """Parse amount of steps, nodes, elements."""
        pass

    def parse_next_step(self):
        pass

    def parse_step(self, n):
        pass


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
    """Search regex in line and report problems."""
    match = re.search(regex, line)
    if match:
        return match
    else:
        logging.error('Can\'t parse line:\n{}\nwith regex:\n{}'\
            .format(line, regex))
        raise Exception
