# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019
# Inspired by C# converter written by Maciek Hawryłkiewicz in 2015


"""
    About the format read:
    https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf

    Remember that the frd file is node based, so element results are also
    stored at the nodes after extrapolation from the integration points:
    http://www.dhondt.de/ccx_2.15.pdf
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


    # Write element connectivity with renumbered nodes
    def write_element_connectivity(self, renumbered_nodes, e, f):
        # frd: 20 node brick element
        if e.etype == 4:
            element_string = '20 '
            # Last eight nodes have to be repositioned
            r1 = tuple(range(12)) # 8,9,10,11
            r2 = tuple(range(12, 16)) # 12,13,14,15
            r3 = tuple(range(16, 20)) # 16,17,18,19
            node_num_list = r1 + r3 + r2
            for i in node_num_list:
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        # frd: 15 node penta element
        elif e.etype==5 or e.etype==2:
            """ 
                CalculiX elements type 5 are not supported in VTK and
                has to be processed as CalculiX type 2 (6 node wedge,
                VTK type 13). Additional nodes are omitted.
            """
            element_string = '6 '
            for i in [0,2,1,3,5,4]: # repositioning nodes
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        # All other elements
        else:
            n = len(e.nodes)
            element_string = '{} '.format(n)
            for i in range(n):
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        f.write('\t' + element_string + '\n')


    # Write data
    def write_data(self, f, b, nn):
        f.write('FIELD {} 1\n'.format(b.name))
        f.write('\t{} {} {} double\n'.format(b.name, len(b.components), nn))
        nodes = sorted(b.results.keys())
        for n in range(nn): # iterate over nodes
            node = nodes[n] 
            data = b.results[node]
            f.write('\t')
            for d in data:
                f.write('\t{:> .8E}'.format(d))
            f.write('\n')


    # Main function
    def __init__(self, p, skip_error_field, file_name, step, nn, ne): # p is FRDParser object

        with open(file_name, 'w') as f:
            # Header
            f.write('# vtk DataFile Version 3.0\n\n')
            f.write('ASCII\n')
            f.write('DATASET UNSTRUCTURED_GRID\n\n')

            # POINTS section - coordinates of all nodes
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

                if new_node_number == nn: 
                    break

            f.write('\n')

            # CELLS section - elements connectyvity
            totn = 0 # total number of nodes
            for e in p.elem_block.elements:
                if e.etype == 5: totn += 6
                else: totn += len(e.nodes)
            f.write('CELLS {} {}\n'.format(ne, ne + totn)) # number of cells and size of the cell list
            for e in p.elem_block.elements:
                self.write_element_connectivity(renumbered_nodes, e, f)
            f.write('\n')

            # CELL TYPES section - write element types:
            f.write('CELL_TYPES {}\n'.format(ne))
            for e in p.elem_block.elements:
                vtk_elem_type = self.convert_elem_type(e.etype)
                f.write('\t{}\n'.format(vtk_elem_type))
            f.write('\n')

            # POINT DATA - from here start all the results
            f.write('POINT_DATA {}\n'.format(nn))
            for b in p.result_blocks: # iterate over FRDResultBlocks
                if skip_error_field and 'ERROR' in b.name:
                    continue
                if b.numstep != int(step): # write results for one time step only
                    continue
                if len(b.results) and len(b.components):
                    log = 'Step {}, '.format(b.numstep) +\
                          'time {}, '.format(b.value) +\
                          '{}, '.format(b.name) +\
                          '{} components, '.format(len(b.components))
                    if len(b.results) != nn:
                          log += '{}->{} values'.format(len(b.results), nn)
                    else:
                        log += '{} values'.format(nn)
                    print(log)
                    self.write_data(f, b, nn)
                else:
                    print(b.name, '- no data for this step')


"""
    TODO learn and use it for future code improvement:
    https://vtk.org/doc/nightly/html/classvtkUnstructuredGridWriter.html
    https://vtk.org/doc/nightly/html/c2_vtk_e_5.html#c2_vtk_e_vtkUnstructuredGrid
    https://vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/DataManipulation/Python/pointToCellData.py
"""