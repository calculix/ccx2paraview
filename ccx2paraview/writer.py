#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2020
Distributed under GNU General Public License v3.0

Writes .vtk and .vtu files based on data from FRD object.
Uses native VTK python package. """

import os
import math
import logging

import vtk

import frd2vtk


def get_element_connectivity(renumbered_nodes, e):
    """Write element connectivity with renumbered nodes."""
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
        """
            CalculiX elements type 5 are not supported in VTK and
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


def generate_ugrid(p):
    """Generate VTK mesh."""

    ugrid = vtk.vtkUnstructuredGrid() # create empty grid in VTK

    # POINTS section
    # Nodes should be renumbered starting from 0
    points = vtk.vtkPoints()
    renumbered_nodes = {} # old_number : new_number
    new_node_number = 0
    for n in sorted(p.node_block.nodes.keys()):
        renumbered_nodes[n] = new_node_number
        coordinates = p.node_block.nodes[n].coords
        points.InsertPoint(new_node_number, coordinates)
        new_node_number += 1
        if new_node_number == p.node_block.numnod:
            break
    ugrid.SetPoints(points) # insert all points to the grid

    # CELLS section - elements connectyvity
    # Sometimes element nodes should be repositioned
    ugrid.Allocate(p.elem_block.numelem)
    for e in sorted(p.elem_block.elements, key=lambda x: x.num):
        vtk_elem_type = frd2vtk.convert_elem_type(e.type)
        offset = amount_of_nodes_in_vtk_element(e)
        connectivity = get_element_connectivity(renumbered_nodes, e)
        ugrid.InsertNextCell(vtk_elem_type, offset, connectivity)

    return ugrid


def assign_data(ugrid, b, numnod):
    """Assign data to VTK mesh."""

    data_array = vtk.vtkDoubleArray()
    data_array.SetName(b.name)
    data_array.SetNumberOfComponents(len(b.components))
    data_array.SetNumberOfTuples(numnod)

    # Calculate amount of components and define their names
    i = 0 # counter
    for c in b.components:
        if 'SDV' in c:
            data_array.SetComponentName(i, i)
        else:
            data_array.SetComponentName(i, c)
        i += 1

    # Some warnings repeat too much time - mark them
    emitted_warning_types = {'Inf':0, 'NaN':0}

    # Assign data
    nodes = sorted(b.results.keys())[:numnod]
    index = 0
    for n in nodes:
        data = b.results[n]
        for i in range(len(data)):
            if math.isinf(data[i]):
                data[i] = 0.0
                emitted_warning_types['Inf'] += 1
            if math.isnan(data[i]):
                data[i] = 0.0
                emitted_warning_types['NaN'] += 1
        data_array.InsertTuple(index, data)
        index += 1
    ugrid.GetPointData().AddArray(data_array)

    for k, v in emitted_warning_types.items():
        if v > 0:
            logging.warning('{} {} values are converted to 0.0'.format(v, k))


class Writer:

    def __init__(self, p, file_name, time):
        """Main function: p is a FRD object."""
        
        self.file_name = file_name
        self.ugrid = generate_ugrid(p)

        # POINT DATA - from here start all the results
        for b in p.result_blocks: # iterate over NodalResultsBlock
            if b.value != time: # write results for one time increment only
                continue
            if len(b.results) and len(b.components):
                if b.value < 1:
                    time_str = 'time {:.2e}, '.format(b.value)
                else:
                    time_str = 'time {:.1f}, '.format(b.value)
                logging.info('Step {}, '.format(b.numstep) +\
                            time_str +\
                            '{}, '.format(b.name) +\
                            '{} components, '.format(len(b.components)) +\
                            '{} values'.format(len(b.results)))
                assign_data(self.ugrid, b, p.node_block.numnod)
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


def write_pvd(file_name, times_names):
    """Writes ParaView Data (PVD) file for series of VTU files."""

    with open(file_name, 'w') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">\n')
        f.write('\t<Collection>\n')

        for t, n in times_names.items():
            f.write('\t\t<DataSet file="{}" timestep="{}"/>\n'\
                .format(os.path.basename(n), t))

        f.write('\t</Collection>\n')
        f.write('</VTKFile>')
