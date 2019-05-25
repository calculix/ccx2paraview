# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019
# Inspired by C# converter written by Maciek Hawryłkiewicz in 2015


"""
    About the format read:
    https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf
"""


class VTKWriter:


    # Convert Calculix element type to VTK
    def convert_elem_type(self, frd_elem_type):
        """
            Keep in mind that CalculiX expands shell elements
            In vtk elements nodes are numbered starting from 0, not 1

            For frd see http://www.dhondt.de/cgx_2.15.pdf pages 117-123 (chapter 10)
            For vtk see https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf pages 9-10

            CalculiX type  1 -  8 node brick element = vtk type 12 - VTK_HEXAHEDRON
            CalculiX type  2 -  6 node penta element = vtk type 13 - VTK_WEDGE
            CalculiX type  3 -  4 node   tet element = vtk type 10 - VTK_TETRA
            CalculiX type  4 - 20 node brick element = vtk type 25 - VTK_QUADRATIC_HEXAHEDRON
            CalculiX type  5 - 15 node penta element ~ vtk type 13 - VTK_WEDGE
            CalculiX type  6 - 10 node   tet element = vtk type 24 - VTK_QUADRATIC_TETRA
            CalculiX type  7 -  3 node shell element = vtk type  5 - VTK_TRIANGLE
            CalculiX type  8 -  6 node shell element = vtk type 22 - VTK_QUADRATIC_TRIANGLE
            CalculiX type  9 -  4 node shell element = vtk type  9 - VTK_QUAD
            CalculiX type 10 -  8 node shell element = vtk type 23 - VTK_QUADRATIC_QUAD
            CalculiX type 11 -  2 node  beam element = vtk type  3 - VTK_LINE
            CalculiX type 12 -  3 node  beam element = vtk type 21 - VTK_QUADRATIC_EDGE
        """
        # frd_elem_type : vtk_elem_type
        dic = {
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
                12: 21,
            }
        if frd_elem_type in dic:
            return dic[frd_elem_type]
        else:
            return 0


    # Renumber and write element nodes
    def write_element_connectivity(self, renumbered_nodes, e, f):
        # frd: 20 node brick element
        if e.etype == 4:
            line = '20 '
            # Last eight nodes have to be repositioned
            r1 = tuple(range(12)) # 8,9,10,11
            r2 = tuple(range(12, 16)) # 12,13,14,15
            r3 = tuple(range(16, 20)) # 16,17,18,19
            node_num_list = r1 + r3 + r2
            for i in node_num_list:
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                line += '{:>8d}'.format(node)

        # frd: 15 node penta element
        elif e.etype==5 or e.etype==2:
            """ 
                CalculiX elements type 5 are not supported in VTK and
                has to be processed as CalculiX type 2 (6 node wedge,
                VTK type 13). Additional nodes are omitted.
            """
            line = '6 '
            for i in [0,2,1,3,5,4]: # repositioning nodes
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                line += '{:>8d}'.format(node)

        # All other elements
        else:
            n = len(e.nodes)
            line = '{0} '.format(n)
            for i in range(n):
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                line += '{:>8d}'.format(node)

        f.write('\t' + line + '\n')


    # Write SDV data
    def write_SDV_data(self, f, b):
        width = len(str(b.ncomps)) # max length of string designating SDV number
        for SDV in range(b.ncomps):
            # f.write('SCALARS {}_{}_SDV{:0{width}} double\n'.format(b.numstep, b.value, SDV, width=width))
            f.write('SCALARS SDV{:0{width}} double\n'.format(SDV, width=width))
            f.write('LOOKUP_TABLE default\n')
            for node in sorted(b.results.keys()):
                data = b.results[node]
                f.write('\t{:> .8E}\n'.format(data[SDV]))


    # Write scalar data
    def write_scalar_data(self, f, b):
        # f.write('SCALARS {}_{}_{} double\n'.format(b.numstep, b.value, b.name))
        f.write('SCALARS {} double\n'.format(b.name))
        f.write('LOOKUP_TABLE default\n')
        for node in sorted(b.results.keys()):
            data = b.results[node]
            f.write('\t{:> .8E}\n'.format(data[0]))


    # Write vector data
    def write_vector_data(self, f, b):
        # f.write('VECTORS {}_{}_{} double\n'.format(b.numstep, b.value, b.name))
        f.write('VECTORS {} double\n'.format(b.name))
        for node in sorted(b.results.keys()):
            for data in b.results[node]:
                f.write('\t{:> .8E}'.format(data))
            f.write('\n')


    # Write tensor data
    def write_tensor_data(self, f, b):
        # f.write('TENSORS {}_{}_{} double\n'.format(b.numstep, b.value, b.name))
        f.write('TENSORS {} double\n'.format(b.name))
        for node in sorted(b.results.keys()):
            data = b.results[node]
            Sxx = data[0]; Syy = data[1]; Szz = data[2]
            Sxy = data[3]; Syz = data[4]; Szx = data[5]
            f.write('\t{:> .8E}\t{:> .8E}\t{:> .8E}\n'.format(Sxx, Sxy, Szx))
            f.write('\t{:> .8E}\t{:> .8E}\t{:> .8E}\n'.format(Sxy, Syy, Syz))
            f.write('\t{:> .8E}\t{:> .8E}\t{:> .8E}\n'.format(Szx, Syz, Szz))
            f.write('\n')


    def __init__(self, p, skip_error_field, step): # p is FRDParser object

        # Output file name will be the same as input
        vtk_filename = p.file_name.replace('.frd', '.{}.vtk'.format(step))
        print(vtk_filename)
        with open(vtk_filename, 'w') as f:

            # Header
            f.write('# vtk DataFile Version 3.0\n\n')
            f.write('ASCII\n')
            f.write('DATASET UNSTRUCTURED_GRID\n\n')

            # POINTS section - coordinates of all nodes
            # nn = p.node_block.numnod # TODO Wrong amount of nodes - has 18 zero nodes more
            try:
                nn = max([len(b.results) for b in p.result_blocks]) # total number of nodes
            except:
                nn = p.node_block.numnod
            print('{} nodes total'.format(nn))
            f.write('POINTS ' + str(nn) + ' double\n')
            new_node_number = 0 # node numbers should start from 0
            renumbered_nodes = {} # old_number : new_number
            for n in p.node_block.nodes.keys():
                # Write nodes coordinates
                coordinates = ''.join('\t{:> .8E}'.format(coord) for coord in p.node_block.nodes[n])
                f.write(coordinates + '\n')

                # For vtk nodes should be renumbered starting from 0
                renumbered_nodes[n] = new_node_number
                new_node_number += 1

                # TODO Wrong amount of nodes - has 18 zero nodes more
                if new_node_number == nn: 
                    break
            f.write('\n')

            # CELLS section - composition of all elements
            ne = p.elem_block.numelem # number of elements
            print('{} cells total'.format(ne))
            totn = 0 # total number of nodes
            for e in p.elem_block.elements:
                if e.etype == 5: totn += 6
                else: totn += len(e.nodes)
            f.write('CELLS {0} {1}\n'.format(ne, ne + totn)) # number of cells and size of the cell list
            for e in p.elem_block.elements:
                self.write_element_connectivity(renumbered_nodes, e, f)
            f.write('\n')

            # CELL TYPES section - write element types:
            f.write('CELL_TYPES {0}\n'.format(ne))
            for e in p.elem_block.elements:
                vtk_elem_type = self.convert_elem_type(e.etype)
                f.write('\t{0}\n'.format(vtk_elem_type))
            f.write('\n')

            # POINT DATA - from here start all the results
            f.write('POINT_DATA {0}\n'.format(nn))
            for b in p.result_blocks: # iterate over FRDResultBlocks
                if skip_error_field and 'ERROR' in b.name:
                    continue
                if b.numstep == int(step): # write results for one time step only
                    print(('Step {}, time {}, {}, {} values'.format(b.numstep, b.value, b.name, b.ncomps)))

                    if len(b.results) and len(b.components):
                        if 'SDV' in b.name: # SDV results
                            self.write_SDV_data(f, b)
                        else:
                            if b.ncomps == 1: # scalar results
                                self.write_scalar_data(f, b)
                            elif b.ncomps == 3: # vector results
                                self.write_vector_data(f, b)
                            elif b.ncomps == 6:  # symmetric tensor results
                                self.write_tensor_data(f, b)
                            else:
                                print('Wrong amount of components: ' + str(b.ncomps))
                    else:
                        print('No data for this step')


"""
    TODO learn and use it for future code improvement:
    https://vtk.org/doc/nightly/html/classvtkUnstructuredGridWriter.html
    https://vtk.org/doc/nightly/html/c2_vtk_e_5.html#c2_vtk_e_vtkUnstructuredGrid
    https://vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/DataManipulation/Python/pointToCellData.py
"""