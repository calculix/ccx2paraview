# -*- coding: utf-8 -*-
# © Lukas Bante, LRZ,     Sep 2017 - original code https://gitlab.lrz.de/snippets/238
# © Ihor Mirzov, UJV Rez, May 2019 - refactoring and bugfix

"""
    This module contains a python classes for parsing Calculix .frd-files.

    FRDParser is the main class and contains the following subclasses:
        NodalPointCoordinateBlock, containing node information
        ElementDefinitionBlock, containing element information
        NodalResultsBlock, containing result information

    Note that only Unix Line endings are currently supported!
"""


import struct
from math import sqrt, ceil


# Nodal Point Coordinate Block
# cgx_2.15 documentation, § 11.3
class NodalPointCoordinateBlock(object):
    key = 2         # node block Key (Always 2)
    code = 'C'      # node block Code (Always C)
    numnod = None   # number of nodes in this block
    fmt = None      # format indicator:
                        # 0   ASCII short
                        # 1   ASCII long
                        # 2   Binary float (4 bytes)
                        # 3   Binary double (8 bytes)
    nodes = {}      # dictionary with node coordinates {node:coords}

    # Read values for this NodalPointCoordinateBlock Object from File in_file
    def __init__(self, in_file=None):
        if in_file:
            in_file.read(18) # pad bytes
            self.numnod = int(in_file.read(12))
            in_file.read(37) # pad bytes
            self.fmt = int(in_file.read(1))
            in_file.read(1) # eol
            for _ in range(self.numnod):
                if self.fmt < 2:
                    in_file.read(1)
                    in_file.read(2) # node key (ASCII only, always -1)
                    node_number = int(in_file.read(5*(self.fmt+1))) # node number
                    node_coords = [float(in_file.read(12)) for j in range(3)] # node coordinates (x,y,z)
                    in_file.read(1) # eol
                else:
                    node_number = struct.unpack('i', in_file.read(4))[0]
                    if self.fmt == 2:
                        node_coords = struct.unpack('fff', in_file.read(12))
                    else:
                        node_coords = struct.unpack('ddd', in_file.read(24))
                self.nodes[node_number] = node_coords
            if self.fmt < 2:
                in_file.readline() # last record for ascii only


# Element
class Element(object):
    number = None       # Element Number
    nodes = []          # List of node numbers belonging to this element
    etype = None        # Element Type (cf. cgx manual):
                        # 1   8-Node Brick Element he8
                        # 2   6-Node Penta Element pe6
                        # 3   4-Node Tet Element
                        # 4   20-Node Brick Element he20
                        # 5   15-Node Penta Element
                        # 6   10-Node Tet Element
                        # 7   3-Node Shell Element tr3, tr3u
                        # 8   6-Node Shell Element tr6
                        # 9   4-Node Shell Element qu4
                        # 10  8-Node Shell Element qu8
                        # 11  2-Node Beam Element be2
                        # 12  3-Node Beam Element be3
    group = None        # Element Group Number
    material = None     # Element Material Number


# Element Definition Block
# cgx_2.15 documentation, § 11.4
class ElementDefinitionBlock(object):
    # First value is meaningless, since elements are 1-based
    nodes_per_elem_type = [0, 8, 6, 4, 20, 15, 10, 3, 6, 4, 8, 2, 3]
    key = 3             # element block Key (Always 3)
    code = 'C'          # element block Code (Always C)
    numelem = None      # number of elements in this block
    elements = []       # list of Element objects
    fmt = None          # format indicator:
                        # 0 ASCII short
                        # 1 ASCII long
                        # 2 Binary

    # Read values for this ElementDefinitionBlock Object from File in_file
    def __init__(self, in_file=None):
        if in_file:
            in_file.read(18) # pad bytes
            self.numelem = int(in_file.read(12))
            in_file.read(37) # pad bytes
            self.fmt = int(in_file.read(1))
            in_file.read(1) # eol

            for _ in range(self.numelem):
                elem = Element()
                if self.fmt < 2:
                    in_file.read(1)
                    in_file.read(2) # elem key
                    elem.number = int(in_file.read(5*(self.fmt+1)))
                    elem.etype = int(in_file.read(5))
                    elem.group = int(in_file.read(5))
                    elem.material = int(in_file.read(5))
                    in_file.read(1) # eol
                    elem.nodes = []
                    num_nodes = self.nodes_per_elem_type[elem.etype]
                    num_lines = int(num_nodes/(5*(3-self.fmt)+1))+1
                    for j in range(num_lines):
                        in_file.read(3) # pad byte and key = -2
                        k_start = j*5*(3-self.fmt)
                        k_end = min(num_nodes - k_start, (j+1)*5*(3-self.fmt))
                        for _ in range(0, k_end):
                            elem.nodes.append(
                                int(in_file.read(5*(self.fmt+1))))
                        in_file.read(1) # eol
                else:
                    elem.number = struct.unpack('i', in_file.read(4))[0]
                    elem.etype = struct.unpack('i', in_file.read(4))[0]
                    num_nodes = self.nodes_per_elem_type[elem.etype]
                    elem.group = struct.unpack('i', in_file.read(4))[0]
                    elem.material = struct.unpack('i', in_file.read(4))[0]
                    elem.nodes = struct.unpack(
                        'i'*num_nodes, in_file.read(num_nodes*4))
                self.elements.append(elem)

            if self.fmt < 2:
                in_file.readline() # last record for ascii only


# Result component
# D1, D2, D3, T, SXX, SYY, SZZ etc.
class Component(object):
    ictype = None   # component type:
                    # 1   scalar
                    # 2   vector with 3 components
                    # 4   matrix
                    # 12  vector with 3 amplitudes and 3 phase-angles
                    # 14  tensor with 6 amplitudes and 6 phase-angles
    key = -5        # component key (always -5)
    name = None     # component name to be used in the cgx menu
    menu = 1        # always 1
    icind1 = None   # sub-component index or row number
    icind2 = None   # column number for ictype==4
    iexist = None   # 0   data are provided (only imlemented type)
    icname = None   # ALL - calculate the total displacement if ictype==2


# Nodal Results Block
# DISP, NDTEMP, STRESS, SDV etc.
# cgx_2.15 documentation, § 11.6
class NodalResultsBlock(object):
    key = 100   # result block key (Always 100)
    code = 'C'  # result block code (Always C)

    # Read values for this NodalResultsBlock object from file in_file
    def __init__(self, in_file=None):
        self.value = None       # could be frequency, time or any numerical value
        self.numnod = None      # number of nodes in this nodal result block # TODO Wrong amount of nodes - has 18 zero nodes more
        self.text = None        # any text
        self.ictype = None      # analysis type:
                                # 0 static
                                # 1 time step
                                # 2 frequency
                                # 3 load step
                                # 4 user named
        self.numstep = None     # step number
        self.analys = None      # analysis description
        self.fmt = None         # format Indicator:
                                # 0 ASCII short
                                # 1 ASCII long
                                # 2 Binary
        self.name = None        # dataset name
        self.irtype = None      # 1   nodal data, material independent (only type imple.)
        self.ncomps = None      # amount of components
        self.components = {}    # dictionary with Component objects {name:object}
        self.results = {}       # dictionary with nodal result {node:data}

        if in_file:
            in_file.read(6).decode().strip() # name (not used)
            self.value = float(in_file.read(12))
            self.numnod = int(in_file.read(12))
            self.text = in_file.read(20).decode().strip()
            self.ictype = int(in_file.read(2))
            self.numstep = int(in_file.read(5))
            self.analys = in_file.read(10).decode().strip()
            self.fmt = int(in_file.read(2))
            in_file.read(1) # eol
            in_file.read(1) # pad byte
            in_file.read(2) # key = -4
            in_file.read(2) # pad bytes
            self.name = in_file.read(8).decode().strip()
            self.ncomps = int(in_file.read(5))
            self.irtype = int(in_file.read(5))
            if self.irtype != 1:
                raise NotImplementedError()
            in_file.read(1) # eol

            # Iterate over components
            for i in range(self.ncomps):
                c = Component()
                in_file.read(1) # pad byte
                c.key = int(in_file.read(2))
                in_file.read(2) # pad bytes
                c.name = in_file.read(8).decode().strip()
                self.components[c.name] = c
                c.menu = int(in_file.read(5))
                c.ictype = int(in_file.read(5)) # component type
                c.icind1 = int(in_file.read(5))
                if c.ictype == 4:
                    c.icind2 = int(in_file.read(5))
                elif c.ictype == 2 and i == 3: # remove 'ALL' component for DISP
                    c.icind2 = int(in_file.read(5))
                    c.iexist = int(in_file.read(5))
                    c.icname = in_file.read(3).decode().strip()
                    self.ncomps -= 1
                    del self.components[c.name]
                else:
                    c.iexist = int(in_file.read(5))
                in_file.read(1) # eol

            # Iterate over nodes
            for i in range(self.numnod):
                data = []
                node = None
                if self.fmt < 2:
                    num_lines = ceil(self.ncomps/6)
                    for j in range(num_lines):
                        in_file.read(3) # pad byte and key = -1 || -2
                        if node is None:
                            node = int(in_file.read(5*(self.fmt+1)))
                        else:
                            in_file.read(5*(self.fmt+1))
                        if j < num_lines - 1:
                            k_end = 6
                        else:
                            k_end = self.ncomps - j*6
                        for _ in range(k_end):
                            data.append(float(in_file.read(12)))
                        in_file.read(1) # eol
                else:
                    node = struct.unpack('i', in_file.read(4))[0]
                    data = struct.unpack(
                        'f'*self.ncomps, in_file.read(self.ncomps*4))
                self.results[node] = data

            if self.fmt < 2:
                in_file.readline() # last record for ascii only

        if 'STRESS' in self.name:
            self.AppendMisesStress()
            self.AppendPrincipalStresses()

    # Append Mises stress to nodes results
    def AppendMisesStress(self):
        c = Component()
        c.ictype = 1; c.name = 'Mises'
        self.components[c.name] = c
        self.ncomps += 1

        # Iterate over nodes
        for node in self.results.keys():
            data = self.results[node] # list with results for current node
            Sxx = data[0]; Syy = data[1]; Szz = data[2]
            Sxy = data[3]; Syz = data[4]; Szx = data[5]

            # Calculate Mises stress for current node
            mises = 1/sqrt(2) *\
                sqrt(   (Sxx - Syy)**2 +\
                        (Syy - Szz)**2 +\
                        (Szz - Sxx)**2 +\
                        6 * Syz**2 +\
                        6 * Szx**2 +\
                        6 * Sxy**2)
            self.results[node].append(mises)

    # Append principal stresses to nodes results
    def AppendPrincipalStresses(self):
        # Check if numpy is installed
        try:
            import numpy

            for i in range(3):
                c = Component()
                c.ictype = 1; c.name = 'Principal'+str(i+1)
                self.components[c.name] = c
                self.ncomps += 1

            # Iterate over nodes
            for node in self.results.keys():
                data = self.results[node] # list with results for current node
                Sxx = data[0]; Syy = data[1]; Szz = data[2]
                Sxy = data[3]; Syz = data[4]; Szx = data[5]
                stessTensor = numpy.array([[Sxx, Sxy, Szx], [Sxy, Syy, Syz], [Szx, Syz, Szz]])

                # Calculate principal stresses for current node
                w, v = numpy.linalg.eig(stessTensor)
                for ps in w.tolist():
                    self.results[node].append(ps)

        except ImportError:
            print('Numpy is not installed.')
            print('Principal stresses will not be calculated.')


# Main class
class FRDParser(object):

    # Read contents of the .frd file
    def __init__(self, file_name=None):
        self.file_name = None       # path to the .frd-file to be read
        self.node_block = None      # node block
        self.elem_block = None      # elements block
        self.result_blocks = []     # all result blocks in order of appearance
        if file_name:
            self.file_name = file_name
            print('Reading .frd-file...')
            with open(file_name, 'rb') as in_file:
                eof = (in_file.read(1) == b'')
                while not eof:
                    key = int(in_file.read(4))
                    code = in_file.read(1).decode()
                    block = None

                    # Header
                    if key == 1:
                        in_file.readline().decode().strip()

                    # Nodes
                    elif key == 2:
                        block = NodalPointCoordinateBlock(in_file)
                        self.node_block = block

                    # Elements
                    elif key == 3:
                        block = ElementDefinitionBlock(in_file)
                        self.elem_block = block

                    # Results
                    elif key == 100:
                        block = NodalResultsBlock(in_file)
                        self.result_blocks.append(block)

                    # End
                    elif key == 9999:
                        eof = True
                    eof = (eof or (in_file.read(1) == b''))
