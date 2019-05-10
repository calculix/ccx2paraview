"""This module contains a python class for parsing and analyzing .frd files.

FRDParser loads and operates on an underlying FRDFile object.
It can be used to access or modify specific datasets or values which are not
necessarily immediately obtainable from the FRDFile.

This module also contains a python class representation for .frd files.

FRDFile is the main class and contains the following subclasses:
    FRDHeader, containing Model/Parameter/User Information
    FRDNodeBlock, containing Node Information
    FRDElemBlock, containing Element Information
    FRDResultBlock, containing Result Information

Note that only Unix Line endings are currently supported!

"""

import datetime
import struct
from math import sqrt

class FRDHeader(object):
    """This class stores Model/Parameter/User Information.

    Attributes:
        key         Header key (Always 1)
        code        Header Type (C:Model, U:User, P:Parameter)
        string      Information stored in Header

    """

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self, in_file=None, code=None):
        """Initialize a new FRDHeader Object.

        Optional parameters:
            in_file     File from which the FRDHeader is to be read from
            code        Header Type

        """
        self.key = 1
        self.code = code
        self.string = None
        if in_file is not None:
            self._read(in_file)

    def _read(self, in_file):
        """Read values for this FRDHeader Object from File in_file."""
        self.string = in_file.readline().decode().strip()

    def _write(self, out_file):

        out_file.write(' '.encode())  # pad byte
        out_file.write('{:4d}'.format(self.key).encode())
        out_file.write(self.code.encode())
        if self.string != '':
            out_file.write(self.string.ljust(66).encode())
        out_file.write('\n'.encode())


class FRDNode(object):
    """This class represents a node as defined in the .frd File.

    Attributes:
        number      Node Number
        pos         Node Coordinates (x/y/z)
        key         Node Key (ASCII only, always -1)

    """

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self):
        """Initialize a new, empty Node Object."""
        self.number = None
        self.pos = None
        self.key = -1


class FRDNodeBlock(object):
    """This class represents a node block in the .frd File.

    Attributes:
        key         Node Block Key (Always 2)
        code        Node Block Code (Always C)
        numnod      Number of nodes in this block
        format      Format indicator:
                        0   ASCII short
                        1   ASCII long
                        2   Binary float (4 bytes)
                        3   Binary double (8 bytes)
        nodes       List containing FRDNode objects defined in this block

    """

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self, in_file=None):
        """Initialize a new FRDNodeBlock Object.

        Optional parameter:
            in_file     File from which the FRDNodeBlock is to be read from

        """
        self.key = 2
        self.code = 'C'
        self.numnod = None
        self.format = None
        self.nodes = []
        if in_file is not None:
            self._read(in_file)

    def _read(self, in_file):
        """Read values for this FRDNodeBlock Object from File in_file."""
        in_file.read(18)  # pad bytes
        self.numnod = int(in_file.read(12))
        in_file.read(37)  # pad bytes
        self.format = int(in_file.read(1))
        in_file.read(1)  # eol
        self.nodes = []

        for _ in range(self.numnod):
            node = FRDNode()
            self.nodes.append(node)
            if self.format < 2:
                in_file.read(1)
                node.key = int(in_file.read(2))
                node.number = int(in_file.read(5*(self.format+1)))
                node.pos = [float(in_file.read(12)) for j in range(3)]
                in_file.read(1)  # eol
            else:
                node.number = struct.unpack('i', in_file.read(4))[0]
                if self.format == 2:
                    node.pos = struct.unpack('fff', in_file.read(12))
                else:
                    node.pos = struct.unpack('ddd', in_file.read(24))

        if self.format < 2:
            in_file.readline()  # last record for ascii only

    def _write(self, out_file):
        """Write values for this FRDNodeBlock Object to File out_file."""
        out_file.write(' '.encode())  # pad byte
        out_file.write('{:4d}'.format(self.key).encode())
        out_file.write(self.code.encode())
        out_file.write((' '*18).encode())  # pad bytes
        out_file.write('{:12d}'.format(self.numnod).encode())
        out_file.write((' '*37).encode())  # pad bytes
        out_file.write('{:1d}'.format(self.format).encode())
        out_file.write('\n'.encode())

        for node in self.nodes:
            if self.format < 2:
                out_file.write(' '.encode())
                out_file.write('-1'.encode())
                if self.format == 0:
                    out_file.write('{:5d}'.format(node.number).encode())
                else:
                    out_file.write('{:10d}'.format(node.number).encode())
                for i in range(3):
                    out_file.write('{:12.5E}'.format(node.pos[i]).encode())
                out_file.write('\n'.encode())
            else:
                out_file.write(struct.pack('i', node.number))
                if self.format == 2:
                    out_file.write(struct.pack('fff', *node.pos))
                else:
                    out_file.write(struct.pack('ddd', *node.pos))

        if self.format < 2:
            out_file.write(' -3\n'.encode())  # last record for ascii only


class FRDElem(object):
    """This class represents an element as defined in the .frd File.

    Attributes:
        number      Element Number
        type        Element Type (cf. cgx manual):
                        1   8-Node Brick Element he8
                        2   6-Node Penta Element pe6
                        3   4-Node Tet Element
                        4   20-Node Brick Element he20
                        5   15-Node Penta Element
                        6   10-Node Tet Element
                        7   3-Node Shell Element tr3, tr3u
                        8   6-Node Shell Element tr6
                        9   4-Node Shell Element qu4
                        10  8-Node Shell Element qu8
                        11  2-Node Beam Element be2
                        12  3-Node Beam Element be3
        group       Element Group Number
        material    Element Material Number
        nodes       List of node numbers belonging to this element
        key         Element Key (ASCII only, always -1)

    """

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    # first value is meaningless, since elements are 1-based
    nodesPerType = [0, 8, 6, 4, 20, 15, 10, 3, 6, 4, 8, 2, 3]

    def __init__(self):
        """Initialize a new, empty Element Object."""
        self.number = None
        self.nodes = []
        self.type = None
        self.group = None
        self.material = None
        self.key = -1


class FRDElemBlock(object):
    """This class represents an element block in the .frd File.

    Attributes:
        key         Element Block Key (Always 3)
        code        Element Block Code (Always C)
        numelem     Number of elements in this block
        format      Format indicator:
                        0   ASCII short
                        1   ASCII long
                        2   Binary
        elems       List containing FRDElem objects defined in this block

    """

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self, in_file=None):
        """Initialize a new FRDElemBlock Object.

        Optional parameter:
            in_file     File from which the FRDElemBlock is to be read from

        """
        self.key = 3
        self.code = 'C'
        self.numelem = None
        self.format = None
        self.elems = []
        if in_file is not None:
            self._read(in_file)

    def _read(self, in_file):
        """Read values for this FRDElemBlock Object from File in_file."""
        in_file.read(18)  # pad bytes
        self.numelem = int(in_file.read(12))
        in_file.read(37)  # pad bytes
        self.format = int(in_file.read(1))
        in_file.read(1)  # eol
        self.elems = []

        for _ in range(self.numelem):
            elem = FRDElem()
            self.elems.append(elem)
            if self.format < 2:
                in_file.read(1)
                elem.key = int(in_file.read(2))
                elem.number = int(in_file.read(5*(self.format+1)))
                elem.type = int(in_file.read(5))
                elem.group = int(in_file.read(5))
                elem.material = int(in_file.read(5))
                in_file.read(1)  # eol
                elem.nodes = []
                num_nodes = FRDElem.nodesPerType[elem.type]
                num_lines = int(num_nodes/(5*(3-self.format)+1))+1
                for j in range(num_lines):
                    in_file.read(3)  # pad byte and key = -2
                    k_start = j*5*(3-self.format)
                    k_end = min(num_nodes - k_start, (j+1)*5*(3-self.format))
                    for _ in range(0, k_end):
                        elem.nodes.append(
                            int(in_file.read(5*(self.format+1))))
                    in_file.read(1)  # eol
            else:
                elem.number = struct.unpack('i', in_file.read(4))[0]
                elem.type = struct.unpack('i', in_file.read(4))[0]
                num_nodes = FRDElem.nodesPerType[elem.type]
                elem.group = struct.unpack('i', in_file.read(4))[0]
                elem.material = struct.unpack('i', in_file.read(4))[0]
                elem.nodes = struct.unpack(
                    'i'*num_nodes, in_file.read(num_nodes*4))

        if self.format < 2:
            in_file.readline()  # last record for ascii only

    def _write(self, out_file):
        """Write values for this FRDElemBlock Object to File out_file."""
        out_file.write(' '.encode())  # pad byte
        out_file.write('{:4d}'.format(self.key).encode())
        out_file.write(self.code.encode())
        out_file.write((' '*18).encode())  # pad bytes
        out_file.write('{:12d}'.format(self.numelem).encode())
        out_file.write((' '*37).encode())  # pad bytes
        out_file.write('{:1d}'.format(self.format).encode())
        out_file.write('\n'.encode())

        for elem in self.elems:
            if self.format < 2:
                out_file.write(' -1'.encode())
                if self.format == 0:
                    out_file.write('{:5d}'.format(elem.number).encode())
                else:
                    out_file.write('{:10d}'.format(elem.number).encode())
                out_file.write('{:5d}'.format(elem.type).encode())
                out_file.write('{:5d}'.format(elem.group).encode())
                out_file.write('{:5d}'.format(elem.material).encode())
                out_file.write('\n'.encode())
                num_nodes = FRDElem.nodesPerType[elem.type]
                num_lines = int(num_nodes/(5*(3-self.format)+1))+1
                for j in range(num_lines):
                    out_file.write(' -2'.encode())  # pad byte and key = -2
                    k_start = j*5*(3-self.format)
                    k_end = min(num_nodes, (j+1)*5*(3-self.format))
                    if self.format == 0:
                        for k in range(k_start, k_end):
                            out_file.write(
                                '{:5d}'.format(elem.nodes[k]).encode())
                    else:
                        for k in range(k_start, k_end):
                            out_file.write(
                                '{:10d}'.format(elem.nodes[k]).encode())
                    out_file.write('\n'.encode())  # eol
            else:
                out_file.write(struct.pack('i', elem.number))
                out_file.write(struct.pack('i', elem.type))
                out_file.write(struct.pack('i', elem.group))
                out_file.write(struct.pack('i', elem.material))
                out_file.write(struct.pack('i'*num_nodes, *elem.nodes))

        if self.format < 2:
            out_file.write(' -3\n')  # last record for ascii only


class FRDEntity(object):
    """This class represents a result component entity in the .frd File.

    Attributes:
        key         Entity Key (Always -5)
        name        Entity name to be used in the cgx menu fo this comp.
        menu        Always 1
        ictype      Type of Entity:
                        1   scalar
                        2   vector with 3 components
                        4   matrix
                        12  vector with 3 amplitudes and 3 phase-angles
                        14  tensor with 6 amplitudes and 6 phase-angles
        icind1      sub-component index or row number
        icind2      column number for ictype==4
        iexist      0   data are provided (only imlemented type)
        icname      ALL - calculate the total displacement if ictype==2

    """

    # Number of instance attributes due to .frd format, i.e. non-negotiable
    # pylint: disable=too-many-instance-attributes

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self):
        """Initialize a new, empty FRDEntity Object."""
        self.key = None
        self.name = None
        self.menu = None
        self.ictype = None
        self.icind1 = None
        self.icind2 = None
        self.iexist = None
        self.icname = None


class FRDNodeResult(object):
    """This class represents a single nodal result.

    Attributes:
        node    Node Number
        data    List of values (also for scalar values)

    """

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self):
        """Initialize a new, empty FRDNodeResult Object."""
        self.node = None
        self.data = None


class FRDResultBlock(object):
    """This class represents a nodal result block in the .frd File.

    Attributes:
        key         Result Block Key (Always 100)
        code        Result Block Code (Always C)
        setname     Name (not used)
        value       Could be frequency, time or any numerical value
        numnod      Number of nodes in this nodal result block
        text        Any text
        ictype      Analysis type:
                        0   static
                        1   time step
                        2   frequency
                        3   load step
                        4   user named
        numstep     Step number
        analys      Type of analysis (description)
        format      Format Indicator:
                        0   ASCII short
                        1   ASCII long
                        2   Binary
        name        Dataset name to be used in cgx menu
        ncomps      number of entities
        irtype      1   Nodal data, material independent (only type imple.)
        entities    List of contained FRDEntity objects
        results     List of contained FRDNodeResult objects

    """

    # Number of instance attributes due to .frd format, i.e. non-negotiable
    # pylint: disable=too-many-instance-attributes

    # We might want to extend this class with methods later on.
    # Also, really don't want this stuff stored in a dict or list.
    # (Yeah I want a struct like in C, deal with it.)
    # So for now, shut up pylint
    # pylint: disable=too-few-public-methods

    def __init__(self, in_file=None):
        """Initialize a new FRDResultBlock Object.

        Optional parameter:
            in_file     File from which the FRDResultBlock is to be read

        """
        self.key = 100
        self.code = 'C'
        self.setname = None
        self.value = None
        self.numnod = None
        self.text = None
        self.ictype = None
        self.numstep = None
        self.analys = None
        self.format = None
        self.name = None
        self.ncomps = None
        self.irtype = None
        self.entities = []
        self.results = []
        if in_file is not None:
            self._read(in_file)

    def _read(self, in_file):
        """Read values for this FRDResultBlock Object from File in_file."""
        #
        # I know this function is long, but the FRD block is long as well...
        # Splitting this into multiple functions would not help in my opinion.
        # Therefore -> shut up pylint
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        #
        self.setname = in_file.read(6).decode().strip()
        self.value = float(in_file.read(12))
        self.numnod = int(in_file.read(12))
        self.text = in_file.read(20).decode().strip()
        self.ictype = int(in_file.read(2))
        self.numstep = int(in_file.read(5))
        self.analys = in_file.read(10).decode().strip()
        self.format = int(in_file.read(2))
        in_file.read(1)  # eol

        in_file.read(1)  # pad byte
        in_file.read(2)  # key = -4
        in_file.read(2)  # pad bytes
        self.name = in_file.read(8).decode().strip()
        self.ncomps = int(in_file.read(5))
        self.irtype = int(in_file.read(5))
        if self.irtype != 1:
            raise NotImplementedError()
        in_file.read(1)  # eol

        for i in range(self.ncomps):
            entity = FRDEntity()
            self.entities.append(entity)

            in_file.read(1)  # pad byte
            entity.key = int(in_file.read(2))
            in_file.read(2)  # pad bytes
            entity.name = in_file.read(8).decode().strip()
            entity.menu = int(in_file.read(5))
            entity.ictype = int(in_file.read(5))
            entity.icind1 = int(in_file.read(5))
            if entity.ictype == 4:
                entity.icind2 = int(in_file.read(5))
            elif entity.ictype == 2 and i == 3:
                entity.icind2 = int(in_file.read(5))
                entity.iexist = int(in_file.read(5))
                entity.icname = in_file.read(3).decode().strip()
                self.ncomps -= 1
            else:
                entity.iexist = int(in_file.read(5))
            in_file.read(1)  # eol

        for i in range(self.numnod):
            result = FRDNodeResult()
            self.results.append(result)
            if self.format < 2:
                num_lines = int(self.ncomps/(6 + 1)) + 1
                result.data = []
                for j in range(num_lines):
                    in_file.read(3)  # pad byte and key = -1 || -2
                    if result.node is None:
                        result.node = int(in_file.read(5*(self.format+1)))
                    else:
                        in_file.read(5*(self.format+1))
                    k_start = j*6
                    k_end = min(self.ncomps - k_start, (j+1)*6)
                    for _ in range(0, k_end):
                        result.data.append(float(in_file.read(12)))
                    in_file.read(1)  # eol
            else:
                result.node = struct.unpack('i', in_file.read(4))[0]
                result.data = struct.unpack(
                    'f'*self.ncomps, in_file.read(self.ncomps*4))

        if self.format < 2:
            in_file.readline()  # last record for ascii only

    def _write(self, out_file):
        """Write values for this FRDResultBlock Object to File out_file."""
        #
        # I know this function is long, but the FRD block is long as well...
        # Splitting this into multiple functions would not help in my opinion.
        # Therefore -> shut up pylint
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        #
        out_file.write(' '.encode())  # pad byte
        out_file.write('{:4d}'.format(self.key).encode())
        out_file.write(self.code.encode())
        out_file.write(self.setname.ljust(6).encode())
        out_file.write('{:12.5E}'.format(self.value).encode())
        out_file.write('{:12d}'.format(self.numnod).encode())
        out_file.write(self.text.ljust(20).encode())
        out_file.write('{:2d}'.format(self.ictype).encode())
        out_file.write('{:5d}'.format(self.numstep).encode())
        out_file.write(self.analys.ljust(10).encode())
        out_file.write('{:2d}'.format(self.format).encode())
        out_file.write('\n'.encode())

        out_file.write(' '.encode())  # pad byte
        out_file.write('-4'.encode())  # key = -4
        out_file.write((' '*2).encode())  # pad bytes
        out_file.write(self.name.ljust(8).encode())
        if self.entities[0].ictype == 2 and self.ncomps == 3:
            out_file.write('{:5d}'.format(self.ncomps + 1).encode())
        else:
            out_file.write('{:5d}'.format(self.ncomps).encode())
        out_file.write('{:5d}'.format(self.irtype).encode())
        out_file.write('\n'.encode())  # eol

        for entity in self.entities:
            out_file.write(' '.encode())  # pad byte
            out_file.write('-5'.encode())
            out_file.write((' '*2).encode())  # pad bytes
            out_file.write(entity.name.ljust(8).encode())
            out_file.write('{:5d}'.format(entity.menu).encode())
            out_file.write('{:5d}'.format(entity.ictype).encode())
            out_file.write('{:5d}'.format(entity.icind1).encode())
            if entity.ictype == 4:
                out_file.write('{:5d}'.format(entity.icind2).encode())
            elif entity.ictype == 2 and entity is self.entities[-1]:
                out_file.write('{:5d}'.format(entity.icind2).encode())
                out_file.write('{:5d}'.format(entity.iexist).encode())
                out_file.write(entity.icname.encode())
            else:
                out_file.write('{:5d}'.format(entity.iexist).encode())
            out_file.write('\n'.encode())  # eol

        for result in self.results:
            if self.format < 2:
                num_lines = int(self.ncomps/(6 + 1)) + 1
                for j in range(num_lines):
                    if j == 0:
                        out_file.write(' -1'.encode())  # pad byte and key = -1
                        if self.format == 0:
                            out_file.write(
                                '{:5d}'.format(result.node).encode())
                        else:
                            out_file.write(
                                '{:10d}'.format(result.node).encode())
                    else:
                        out_file.write(' -2'.encode())  # pad byte and key = -2
                        out_file.write(' '*(5*(self.format+1)).encode())
                    k_start = j*6
                    k_end = min(self.ncomps - k_start, (j+1)*6)
                    for k in range(k_start, k_end):
                        out_file.write(
                            '{:12.5E}'.format(result.data[k]).encode())
                    out_file.write('\n'.encode())  # eol
            else:
                out_file.write(struct.pack('i', result.node))
                out_file.write(struct.pack('f'*self.ncomps, *result.data))

        if self.format < 2:
            out_file.write(' -3\n'.encode())  # last record for ascii only


class FRDFile(object):
    """This class encapsulates all information in a .frd File.

    Attributes:
        blocks      All FRD blocks in order of appearance
        headers     All FRD headers in order of appearance
        nodes       FRD node block in file
        elems       FRD element block in file
        results     All FRD result blocks in order of appearance

    """

    def __init__(self, file_name=None):
        """Initialize a new FRDFile Object.

        Optional parameter:
            file_name    Path to the .frd file to be read

        """
        self.blocks = []
        self.headers = []
        self.node_block = None
        self.elem_block = None
        self.result_blocks = []
        self.file_name = file_name

        if file_name is not None:
            self.load(file_name)

    def load(self, file_name):
        """Read content of .frd file at file_name into this FRDFile object.

        Parameters:
            file_name   Path to .frd file to be loaded

        """
        self.file_name = file_name

        with open(file_name, 'rb') as in_file:
            eof = (in_file.read(1) == b'')

            while not eof:
                key = int(in_file.read(4))
                code = in_file.read(1).decode()
                block = None
                if key == 1:
                    block = FRDHeader(in_file, code)
                    self.headers.append(block)
                elif key == 2:
                    block = FRDNodeBlock(in_file)
                    self.node_block = block
                elif key == 3:
                    block = FRDElemBlock(in_file)
                    self.elem_block = block
                elif key == 100:
                    block = FRDResultBlock(in_file)
                    self.result_blocks.append(block)
                elif key == 9999:
                    eof = True
                if block is not None:
                    self.blocks.append(block)
                eof = (eof or (in_file.read(1) == b''))

    def save(self, file_name=None):
        """Save/Overwrite the .frd file at (previously) specified location."""
        if file_name is not None:
            self.file_name = file_name

        if self.file_name is not None:
            with open(file_name, 'wb') as out_file:
                for block in self.blocks:
                    # Rather not have the write methods public,
                    # since only this save function should be used,
                    # so make pylint shutup on this call.
                    # pylint: disable=protected-access
                    block._write(out_file)
                out_file.write('9999'.encode())

class FRDParser(object):
    """This class loads and performs operations on a FRDFile object.

    Attributes:
        file_name   Filename of current FRD object
        frd         Current FRD object

    """

    def __init__(self, file_name=None):
        """Initialize a new FRDParser Object.

        Optional parameter:
            file_name   Path to .frd File to be read upon creation

        """
        self.file_name = file_name
        self.frd = None
        self._steps = []
        if file_name is not None:
            self.load(file_name)

    def load(self, file_name):
        """Load a .frd file into the parser.

        Parameters:
            file_name   Path to the .frd File to be read

        """
        self.file_name = file_name
        self.frd = FRDFile(file_name)
        self._build_node_kon()
        self._build_step_idx()

    def save(self, file_name=None, as_copy=False):
        """Saves/Overwrites the .frd file in the parser.

        Optional parameters:
            file_name   Path at which to save .frd file
            as_copy     Bool - Save As copy, only applicable with file_name

        """
        if self.frd is not None:
            if file_name is not None:
                self.frd.save(file_name)
                if as_copy:
                    self.frd.file_name = self.file_name
            else:
                self.frd.save(self.file_name)

    def _confirm_step_selection(self, steps):
        steps = steps[:]
        for i, step in enumerate(steps):
            if step < 0:
                try:
                    steps[i] = self._steps[step]
                except IndexError:
                    raise IndexError(
                        'Step {:d} does not exist.'.format(step))
            else:
                try:
                    self._steps.index(step)
                except ValueError:
                    raise IndexError(
                        'Step {:d} does not exist.'.format(step))
        return steps

    def get_results_block(self, names=None, steps=None):
        """Get a (filtered) list of FRDResultBlock objects in the .frd File.

        Optional parameters:
            names   Component names to be included (None -> all names)
                    For example:
                        STRESS      stress
                        DISP        displacement
                        NDTEMP      temperature
            steps   Step numbers to be included (None -> all steps)

        """
        if steps is not None:
            steps = self._confirm_step_selection(steps)

        r_blocks = self.frd.result_blocks[:]
        i_start = len(r_blocks) - 1
        i_end = -1

        for idx in range(i_start, i_end, -1):
            r_block = r_blocks[idx]
            if names is not None and r_block.name not in names:
                r_blocks.remove(r_block)
            elif steps is not None and r_block.numstep not in steps:
                r_blocks.remove(r_block)

        return r_blocks

    @staticmethod
    def _parse_ccx_date(date, time):

        # For english locale, strptime would be able to handle the month
        # names that appear in the .frd files (which are always in english!),
        # however it would fail for other (e.g. german) locales.
        # Rather than mess with the locale settings, let's just replace the
        # calculix month names with the corresponding month decimals
        ccx_months = {
            'january': '01',
            'february': '02',
            'march': '03',
            'april': '04',
            'may': '05',
            'june': '06',
            'july': '07',
            'august': '08',
            'september': '09',
            'october': '10',
            'november': '11',
            'december': '12',
            }
        for month in ccx_months:
            date = date.replace(month, ccx_months[month])

        dformat = "%d.%m.%Y %H:%M:%S"

        return datetime.datetime.strptime(date + ' ' + time, dformat)

    def get_time_and_date(self):
        """Return time and date of the .frd File as dateTime object."""
        date_str = ''
        time_str = ''
        for header in self.frd.headers:
            if header.code != 'U':
                continue
            elif header.string.startswith('DATE'):
                date_str = header.string.replace('DATE', '').strip()
            elif header.string.startswith('TIME'):
                time_str = header.string.replace('TIME', '').strip()
        return FRDParser._parse_ccx_date(date_str, time_str)

    def get_results_node(self, number, names=None, steps=None):
        """Get a list of result values in the .frd File for specified nodes.

        If no name or step is specified, all results are returned in a list
        ordered by steps and names in order of appearance in the .frd file.

        Note that the returned list entries are always iterables,
        even if the result has only one component (e.g. the return
        value for NDTEMP in a single step could be [750.0] )

         Parameters:
             number     Node number
         Optional parameters:
             names      List of comp. names to be included (None -> all names)
                        For example:
                            STRESS      stress
                            DISP        displacement
                            NDTEMP      temperature
             steps      List of step numbers to be included (None -> all steps)

        """
        results = []

        if steps is not None:
            steps = self._confirm_step_selection(steps)

        for r_block in self.frd.result_blocks:
            if names is not None and r_block.name not in names:
                continue
            elif steps is not None and r_block.numstep not in steps:
                continue
            else:
                res = FRDParser._find_node(r_block.results, number)
                if res is not None:
                    results.append(res.data)

        if not results:
            err_msg = 'No results for node '
            err_msg += '{}, names {}, steps {}'.format(number, names, steps)
            raise RuntimeError(err_msg)
        else:
            return results

    def get_results_pos(self, pos, names=None, steps=None):
        """Get a list of result values in the .frd File for specified coords.

        If the given coords do not match a single node, the result is
        interpolated within the closest element.

        If no name or step is specified, all results are returned in a list
        ordered by steps and names in order of appearance in the .frd file.

        Note that the returned list entries are always iterables,
        even if the result has only one component (e.g. the return
        value for NDTEMP in a single step could be [750.0] )

        Parameters:
            pos     Position (as xyz-tuple)
        Optional parameters:
            names   List of component names to be included (None -> all names)
                    For example:
                        STRESS      stress
                        DISP        displacement
                        NDTEMP      temperature
            steps   List of step numbers to be included (None -> all steps)

        """
        results = []

        if steps is not None:
            steps = self._confirm_step_selection(steps)

        for r_block in self.frd.result_blocks:
            if names is not None and r_block.name not in names:
                continue
            elif steps is not None and r_block.numstep not in steps:
                continue
            else:
                results.append(self._interpolate_xyz(r_block, pos))

        if not results:
            err_msg = 'No results for pos '
            err_msg += '{}, names {}, steps {}'.format(pos, names, steps)
            raise RuntimeError(err_msg)
        else:
            return results

    @staticmethod
    def _assert_err_msg(res, r_block):
        msg = ''
        msg += 'Node: ' + str(res.node)
        msg += ' Name: ' + r_block.name
        msg += ' Step: ' + str(r_block.numstep)
        msg += ' Data: ' + str(res.data)
        return msg

    def assert_node_results(self, func, nodes=None, names=None, steps=None):
        """Peform a given test on a subset of all result values.

        If the test fails on a node, an AssertionError, showing node,
        name and step information is raised.

        Parameters:
            func    Function which operates on a single nodal Result

                    Since each result is a list of components (even
                    for scalar results), the (only!) input argument has
                    to be a iterable.

                    func should return True if the test is passed
                    and False if the test is failed.
        Optional parameters:
            node    List of node numbers to be tested (None -> all nodes)
            names   List of component names to be tested (None -> all names)
            steps   List of step numbers to be tested (None -> all steps)

        """
        if steps is not None:
            steps = self._confirm_step_selection(steps)

        for r_block in self.frd.result_blocks:
            if names is not None and r_block.name not in names:
                continue
            elif steps is not None and r_block.numstep not in steps:
                continue
            else:
                if nodes is not None:
                    for node in nodes:
                        res = FRDParser._find_node(r_block.results, node)
                        if res is not None and not func(res.data):
                            err = AssertionError(
                                FRDParser._assert_err_msg(res, r_block))
                            err.node = res.node
                            err.step = r_block.numstep
                            err.node_data = res.data
                            err.res_name = r_block.name
                            raise err
                else:
                    for res in r_block.results:
                        if res is not None and not func(res.data):
                            err = AssertionError(
                                FRDParser._assert_err_msg(res, r_block))
                            err.node = res.node
                            err.step = r_block.numstep
                            err.node_data = res.data
                            err.res_name = r_block.name
                            raise err

    def convert_format(self, new_format):
        """Convert the loaded .frd file to a different storage format.

        Parameters:
            new_format
                0   ASCII short (5 digit element/node-names)
                1   ASCII long (10 digit element/node-names)
                2   BINARY float (4-byte for all binary-encoded numeric values)
                3   BINARY double (8-byte for each node coordinate,
                                   4-byte for all other binary numeric values)

        """
        if new_format not in [0, 1, 2, 3]:
            raise ValueError("Unknown format specified")

        inp_format = new_format
        if inp_format == 3:
            new_format = 2

        for block in self.frd.blocks:
            if hasattr(block, 'format'):
                block.format = new_format

        self.frd.node_block.format = inp_format

    @staticmethod
    def _reduce_result_block(nodes, r_block):

        j_start = len(r_block) - 1
        j_end = -1
        for j in range(j_start, j_end, -1):
            res = r_block[j]
            if res.node not in nodes:
                r_block.remove(res)

    def reduce_file_nodes(self, nodes, names=None, steps=None):
        """Reduce the .frd file to only the specified node numbers.

        Unspecified nodes and their results , as well as all elements
        and irrelevant parameter headers will be removed.

        Parameters:
            nodes   List of node numbers to be kept in the file
        Optional parameter:
            names   List of component names to be kept (None -> all names)
            steps   List of step numbers to be kept (None -> all steps)

        """
        if steps is not None:
            steps = self._confirm_step_selection(steps)

        idx_start = len(self.frd.node_block.numnod) - 1
        idx_end = -1

        for idx in range(idx_start, idx_end, -1):
            node = self.frd.node_block.nodes[idx]
            if node.number not in nodes:
                self.frd.node_block.nodes.remove(node)
                self.frd.node_block.numnod -= 1

        self.frd.blocks.remove(self.frd.elem_block)
        self.frd.elem_block = None

        idx_start = len(self.frd.result_blocks) - 1
        idx_end = -1

        for idx in range(idx_start, idx_end, -1):
            r_block = self.frd.result_blocks[idx]
            if names is not None and r_block.name not in names:
                self._remove_result_param_header(r_block)
                self.frd.blocks.remove(r_block)
                self.frd.result_blocks.remove(r_block)
            elif steps is not None and r_block.numstep not in steps:
                self._remove_result_param_header(r_block)
                self.frd.blocks.remove(r_block)
                self.frd.result_blocks.remove(r_block)
            else:
                FRDParser._reduce_result_block(nodes, r_block)

    def _remove_result_param_header(self, r_block):

        idx = None
        try:
            idx = self.frd.blocks.index(r_block)
        except ValueError:
            pass

        if idx and self.frd.blocks[idx-1].code == 'P':
            self.frd.headers.remove(self.frd.blocks[idx-1])
            self.frd.blocks.remove(self.frd.blocks[idx-1])

    def reduce_file_xyz(self, positions, names=None, steps=None):
        """Reduce the .frd file to only the specified coordinates.

        Nodes and nodal results not at the coordinates, as well as all elements
        and irrelevant parameter headers will be removed.
        If the coordinates are not nodes already, new nodes will be added, with
        the result data interpolated from existing nodes.

        Parameters:
            positions   List of (xyz-tuples) to be kept in the file
        Optional parameter:
            names       List of component names to be kept (None -> all names)
            steps       List of step numbers to be kept (None -> all steps)

        """
        if steps is not None:
            steps = self._confirm_step_selection(steps)

        new_result_blocks = []
        for r_block in self.frd.result_blocks:

            if steps is not None and r_block.numstep not in steps:
                self._remove_result_param_header(r_block)
                self.frd.blocks.remove(r_block)
                continue
            elif names is not None and r_block.name not in names:
                self._remove_result_param_header(r_block)
                self.frd.blocks.remove(r_block)
                continue

            r_block.numnod = len(positions)
            new_results = []
            for pos in positions:
                res = FRDNodeResult()
                new_results.append(res)
                res.node = len(new_results)
                res.data = self.get_results_pos(
                    pos, names=[r_block.name], steps=[r_block.numstep])[0]
            r_block.results = new_results
            new_result_blocks.append(r_block)

        self.frd.result_blocks = new_result_blocks

        self.frd.node_block.numnod = len(positions)
        self.frd.node_block.nodes = []
        for pos in positions:
            frd_node = FRDNode()
            self.frd.node_block.nodes.append(frd_node)
            frd_node.number = len(self.frd.node_block.nodes)
            frd_node.pos = pos

        self.frd.blocks.remove(self.frd.elem_block)
        self.frd.elem_block = None

    def get_comp_names(self, names):
        """Get component/entity names for the supplied result names."""
        names = names[:]
        comp_names = {}
        for r_block in self.frd.result_blocks:
            if r_block.name in names and r_block.name not in comp_names:
                comp_names[r_block.name] = []
                for ent in r_block.entities:
                    if ent.ictype == 2 and ent.icind1 == 0:
                        continue
                    comp_names[r_block.name].append(ent.name)
                names.remove(r_block.name)
                if not names:
                    break
        return comp_names

    def add_user_header(self, text):
        """Insert a user header with the supplied text into the .frd file."""
        new_header = FRDHeader()
        new_header.key = 1
        new_header.code = 'U'
        new_header.string = text
        last_user_idx = -1
        last_user_header = self.frd.headers[last_user_idx]
        while last_user_header.code != 'U':
            last_user_idx -= 1
            last_user_header = self.frd.headers[last_user_idx]
        idx = self.frd.blocks.index(last_user_header)
        self.frd.blocks.insert(idx+1, new_header)
        idx = self.frd.headers.index(last_user_header)
        self.frd.headers.insert(idx+1, new_header)

    def get_user_header(self, prefix):
        """Get the first user header that matches the given prefix."""
        for header in self.frd.headers:
            if header.string.startswith(prefix):
                return header.string.replace(prefix, '').strip()

    @staticmethod
    def _find_node(block, n_num):

        if not block:
            return None

        idr = None
        if hasattr(block[0], 'node'):
            idr = 'node'
        elif hasattr(block[0], 'number'):
            idr = 'number'

        # First check whether nodes are defined in order, starting from 1
        idx = n_num - 1
        if idx < len(block) and getattr(block[idx], idr) == n_num:
            return block[idx]

        # Then check whether nodes are defined in order, starting with offset
        offset = getattr(block[0], idr)
        idx = n_num - offset
        if idx >= 0 and idx < len(block) and getattr(block[idx], idr) == n_num:
            return block[idx]

        # Ok, let's check all nodes
        for node in block:
            if getattr(node, idr) == n_num:
                return node

        # If we got this far, we didn't find this node number
        return None

    def _interpolate_xyz(self, r_block, pos):

        result = []

        node = self._find_closest_node(pos)
        n_data = FRDParser._find_node(r_block.results, node.number).data

        if FRDParser._same_xform(node.pos, pos):
            result = n_data[:]
            # print "Not interpolating", node.number, result, node.pos
        else:
            # print "Interpolating", pos
            result = [0.0 for i in range(len(n_data))]
            elem = self._find_closest_element(pos, node=node)
            if elem is not None:
                dists = {}
                for n_idx in elem.nodes:
                    e_node = FRDParser._find_node(
                        self.frd.node_block.nodes, n_idx)
                    dists[e_node] = FRDParser._vector_distance(e_node.pos, pos)
                inv_dist_sum = sum([1.0 / x for x in dists.values()])
                for e_node in dists:
                    weight = 1.0 / (dists[e_node] * inv_dist_sum)
                    en_data = FRDParser._find_node(
                        r_block.results, e_node.number).data
                    for i in range(r_block.ncomps):
                        result[i] += weight * en_data[i]
            else:
                result = n_data[:]
        return result

    def _find_closest_node(self, pos):

        closest_dist = FRDParser._vector_distance(
            pos, self.frd.node_block.nodes[0].pos)
        closest_node = self.frd.node_block.nodes[0]
        for node in self.frd.node_block.nodes:
            dist = FRDParser._vector_distance(pos, node.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_node = node
        return closest_node

    @staticmethod
    def _vector_distance(origin, target):

        return sqrt(sum([(a-b)**2 for a, b in zip(origin, target)]))

    def _find_closest_element(self, pos, node=None):

        if node is None:
            node = self._find_closest_node(pos)

        closest_dist = float('inf')
        closest_elem = None

        for elem in node.elems:
            dist = 0
            for n_idx in elem.nodes:
                e_node = FRDParser._find_node(self.frd.node_block.nodes, n_idx)
                if e_node is not None:
                    dist += FRDParser._vector_distance(e_node.pos, pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_elem = elem

        return closest_elem

    def _build_node_kon(self):

        for node in self.frd.node_block.nodes:
            node.elems = []

        if self.frd.elem_block:
            for elem in self.frd.elem_block.elems:
                for n_num in elem.nodes:
                    node = FRDParser._find_node(
                        self.frd.node_block.nodes, n_num)
                    if node is not None:
                        node.elems.append(elem)

    def _build_step_idx(self):

        self._steps = []

        for r_block in self.frd.result_blocks:
            if r_block.numstep not in self._steps:
                self._steps.append(r_block.numstep)

    @staticmethod
    def _same_xform(vec1, vec2):

        return vec1[0] == vec2[0] and vec1[1] == vec2[1] and vec1[2] == vec2[2]