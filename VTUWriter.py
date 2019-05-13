# -*- coding: utf-8 -*-
# © Ihor Mirzov, UJV Rez, April 2019
# Inspired by odb2vtk converter written by Liujie-SYSU: https://github.com/Liujie-SYSU/odb2vtk


"""
    About the format read:
    https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf

    Remember that the frd file is node based, so element results are also
    stored at the nodes after extrapolation from the integration points:
    http://www.dhondt.de/ccx_2.15.pdf
"""


class VTUWriter:


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


    # Renumber nodes and write element connectivity
    def write_element_connectivity(self, renumbered_nodes, e, f):
        element_string = ''

        # frd: 20 node brick element
        if e.type == 4:
            # Last eight nodes have to be repositioned
            r1 = tuple(range(12))
            r2 = tuple(range(12, 16))
            r3 = tuple(range(16, 20))
            node_num_list = r1 + r2 + r3
            for i in node_num_list:
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        # frd: 15 node penta element
        elif e.type==5 or e.type==2:
            """ 
                CalculiX elements type 5 are not supported in VTK and
                has to be processed as CalculiX type 2 (6 node wedge,
                VTK type 13). Additional nodes are omitted.
            """
            for i in [0,2,1,3,5,4]: # repositioning nodes
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        # All other elements
        else:
            for i in range(len(e.nodes)):
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        f.write(element_string)


    # Amount of nodes in element: needed to calculate offset
    def amount_of_nodes_in_vtk_element(self, e):
        # frd: 20 node brick element
        if e.type == 4:
            n = 20

        # frd: 15 node penta element
        elif e.type==5 or e.type==2:
            n = 6

        # All other elements
        else:
            n = len(e.nodes)

        # print(e.type, n)
        return n


    # Write data
    def write_data(self, b, f):
        
        # Calculate amount of components and define their names
        # TODO FRDParser: b.ncomps != len(b.entities)
        component_names = ''
        for i in range(b.ncomps):
            ent = b.entities[i]
            if 'SDV' in ent.name:
                component_names += 'ComponentName{}="{}" '.format(i, i)
            else:
                component_names += 'ComponentName{}="{}" '.format(i, ent.name)

        # Write data
        f.write('\t\t\t\t<DataArray type="Float32" Name="{}" NumberOfComponents="{}" {}format="ascii">\n\t\t\t\t\t'.format(b.name, b.ncomps, component_names))
        for r in b.results:
            for d in r.data:
                f.write('{:.6f} '.format(d))
        f.write('\n\t\t\t\t</DataArray>\n')


    def __init__(self, p, skip_error_field, step): # p is FRDParser object

        # Output file name will be the same as input
        vtk_filename = p.file_name.replace('.frd', '.{}.vtu'.format(step))
        print(vtk_filename)
        with open(vtk_filename, 'w') as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian">\n')
            f.write('\t<UnstructuredGrid>\n')

            # nn = p.frd.node_block.numnod # TODO Wrong amount of nodes - has 18 zero nodes more
            nn = max([len(b.results) for b in p.frd.result_blocks])
            print('{} nodes total'.format(nn))
            ne = p.frd.elem_block.numelem # total number of elements
            print('{} cells total'.format(ne))

            f.write('\t\t<Piece NumberOfPoints="{}" NumberOfCells="{}">\n'.format(nn, ne))

            # Coordinates of all nodes
            f.write('\t\t\t<Points>\n')
            f.write('\t\t\t\t<DataArray type="Float64" NumberOfComponents="3" format="ascii">\n')
            f.write('\t\t\t\t\t')
            new_node_number = 0; renumbered_nodes = {} # old_number : new_number
            for i in range(nn):
                n = p.frd.node_block.nodes[i]
                # Write nodes coordinates
                coordinates = ''.join('{:.6f} '.format(coord) for coord in n.pos)
                f.write(coordinates)

                # For vtk nodes should be renumbered starting from 0
                renumbered_nodes[n.number] = new_node_number
                new_node_number += 1
            f.write('\n\t\t\t\t</DataArray>\n')
            f.write('\t\t\t</Points>\n')


            f.write('\t\t\t<Cells>\n')

            # Elements connectyvity
            f.write('\t\t\t\t<DataArray type="Int32" Name="connectivity" format="ascii">\n')
            f.write('\t\t\t\t\t')
            for e in p.frd.elem_block.elems:
                self.write_element_connectivity(renumbered_nodes, e, f)
            f.write('\n\t\t\t\t</DataArray>\n')

            # Node offsets (indexes in the connectivity DataArray)
            f.write('\t\t\t\t<DataArray type="Int32" Name="offsets" format="ascii">\n')
            f.write('\t\t\t\t\t')
            offset = 0
            for frd_element in p.frd.elem_block.elems:
                offset += self.amount_of_nodes_in_vtk_element(frd_element)
                f.write('{} '.format(offset))
            f.write('\n\t\t\t\t</DataArray>\n')

            # Element types
            f.write('\t\t\t\t<DataArray type="UInt8" Name="types" format="ascii">\n')
            f.write('\t\t\t\t\t')
            for e in p.frd.elem_block.elems:
                vtk_elem_type = self.convert_elem_type(e.type)
                f.write('{0} '.format(vtk_elem_type))
            f.write('\n\t\t\t\t</DataArray>\n')

            f.write('\t\t\t</Cells>\n')


            # POINT DATA - from here start all the results
            f.write('\t\t\t<PointData>\n')
            for b in p.frd.result_blocks: # iterate over FRDResultBlocks
                if skip_error_field and 'ERROR' in b.name:
                    continue
                if b.numstep == int(step): # write results for one time step only
                    print(('Step {}, time {}, {}, {} components, {} values'.format(b.numstep, b.value, b.name, b.ncomps, len(b.results))))
                    if len(b.results) and len(b.entities):
                        self.write_data(b, f)
                    else:
                        print('No data for this step')
            f.write("\t\t\t</PointData>"+'\n')

            f.write('\t\t</Piece>\n')
            f.write('\t</UnstructuredGrid>\n')
            f.write('</VTKFile>')
