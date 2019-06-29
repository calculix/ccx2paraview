# -*- coding: utf-8 -*-

"""
    © Ihor Mirzov, April 2019
    Distributed under GNU General Public License, version 2.

    Inspired by odb2vtk converter written by Liujie-SYSU: https://github.com/Liujie-SYSU/odb2vtk

    About the format read:
    https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf
    https://lorensen.github.io/VTKExamples/site/VTKFileFormats/#unstructuredgrid

    Remember that the frd file is node based, so element results are also
    stored at the nodes after extrapolation from the integration points:
    http://www.dhondt.de/ccx_2.15.pdf
"""


from INPParser import Mesh


class VTUWriter:


    # Write element connectivity with renumbered nodes
    def write_element_connectivity(self, renumbered_nodes, e, f):
        element_string = ''

        # frd: 20 node brick element
        if e.etype == 4:
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
            for i in [0,2,1,3,5,4]: # repositioning nodes
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        # All other elements
        else:
            n = len(e.nodes)
            for i in range(n):
                node = renumbered_nodes[e.nodes[i]] # node after renumbering
                element_string += '{:d} '.format(node)

        f.write(element_string)


    # Amount of nodes in element: needed to calculate offset
    def amount_of_nodes_in_vtk_element(self, e):
        # frd: 20 node brick element
        if e.etype == 4:
            n = 20

        # frd: 15 node penta element
        elif e.etype==5 or e.etype==2:
            n = 6

        # All other elements
        else:
            n = len(e.nodes)

        # print(e.etype, n)
        return n


    # Write data
    def write_data(self, f, b, numnod):
        
        # Calculate amount of components and define their names
        component_names = ''
        i = 0 # counter
        for c in b.components.keys():
            if 'SDV' in c:
                component_names += 'ComponentName{}="{}" '.format(i, i)
            else:
                component_names += 'ComponentName{}="{}" '.format(i, c)
            i += 1

        # Write data
        f.write('\t\t\t\t<DataArray type="Float32" Name="{}" NumberOfComponents="{}" {}format="ascii">\n'.format(b.name, len(b.components), component_names))
        nodes = sorted(b.results.keys())
        for n in range(numnod): # iterate over nodes
            node = nodes[n] 
            data = b.results[node]
            f.write('\t\t\t\t')
            for d in data:
                if abs(d) < 1e-9: d = 0 # filter small values for smooth zero fields
                f.write('\t{:> .8E}'.format(d))
            f.write('\n')
        f.write('\t\t\t\t</DataArray>\n')


    # Main function
    def __init__(self, p, skip_error_field, file_name, step): # p is FRDParser object

        with open(file_name, 'w') as f:
            # Header
            f.write('<?xml version="1.0"?>\n')
            f.write('<VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian">\n')
            f.write('\t<UnstructuredGrid>\n')
            f.write('\t\t<Piece NumberOfPoints="{}" NumberOfCells="{}">\n'.format(p.node_block.numnod, p.elem_block.numelem))

            # POINTS section - coordinates of all nodes
            f.write('\t\t\t<Points>\n')
            f.write('\t\t\t\t<DataArray type="Float64" NumberOfComponents="3" format="ascii">\n')
            new_node_number = 0 # node numbers should start from 0
            renumbered_nodes = {} # old_number : new_number
            for n in p.node_block.nodes.keys():

                # Write nodes coordinates
                coordinates = ''.join('\t{:> .8E}'.format(coord) for coord in p.node_block.nodes[n])
                f.write('\t\t\t\t' + coordinates + '\n')

                # For vtk nodes should be renumbered starting from 0
                renumbered_nodes[n] = new_node_number
                new_node_number += 1

                if new_node_number == p.node_block.numnod: 
                    break

            f.write('\n\t\t\t\t</DataArray>\n')
            f.write('\t\t\t</Points>\n')


            f.write('\t\t\t<Cells>\n')

            # CELLS section - elements connectyvity
            f.write('\t\t\t\t<DataArray type="Int32" Name="connectivity" format="ascii">\n')
            f.write('\t\t\t\t\t')
            for e in p.elem_block.elements:
                self.write_element_connectivity(renumbered_nodes, e, f)
            f.write('\n\t\t\t\t</DataArray>\n')

            # Node offsets (indexes in the connectivity DataArray)
            f.write('\t\t\t\t<DataArray type="Int32" Name="offsets" format="ascii">\n')
            f.write('\t\t\t\t\t')
            offset = 0
            for frd_element in p.elem_block.elements:
                offset += self.amount_of_nodes_in_vtk_element(frd_element)
                f.write('{} '.format(offset))
            f.write('\n\t\t\t\t</DataArray>\n')

            # Element types
            f.write('\t\t\t\t<DataArray type="UInt8" Name="types" format="ascii">\n')
            f.write('\t\t\t\t\t')
            for e in p.elem_block.elements:
                vtk_elem_type = Mesh.convert_elem_type(e.etype)
                f.write('{0} '.format(vtk_elem_type))
            f.write('\n\t\t\t\t</DataArray>\n')

            f.write('\t\t\t</Cells>\n')


            # POINT DATA - from here start all the results
            f.write('\t\t\t<PointData>\n')
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
                    if len(b.results) != p.node_block.numnod:
                          log += '{}->{} values'.format(len(b.results), p.node_block.numnod)
                    else:
                        log += '{} values'.format(p.node_block.numnod)
                    print(log)
                    self.write_data(f, b, p.node_block.numnod)
                else:
                    print(b.name, '- no data for this step')
            f.write("\t\t\t</PointData>"+'\n')

            f.write('\t\t</Piece>\n')
            f.write('\t</UnstructuredGrid>\n')
            f.write('</VTKFile>')


"""
    TODO learn and use it for future code improvement:
    https://vtk.org/doc/nightly/html/c2_vtk_t_23.html#c2_vtk_t_vtkXMLUnstructuredGridWriter
    https://vtk.org/doc/nightly/html/c2_vtk_t_20.html#c2_vtk_t_vtkUnstructuredGrid
    https://vtk.org/gitweb?p=VTK.git;a=blob;f=IO/XML/Testing/Python/TestCellArray.py
    https://vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/DataManipulation/Python/marching.py
    https://vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/DataManipulation/Python/BuildUGrid.py
    https://vtk.org/gitweb?p=VTK.git;a=blob;f=IO/XML/Testing/Python/TestXMLUnstructuredGridIO.py
"""