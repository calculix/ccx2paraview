# -*- coding: utf-8 -*-

"""
    © Ihor Mirzov, October 2019
    Distributed under GNU General Public License v3.0

    Writes ParaView Data (PVD) for series of VTU files.
    https://www.paraview.org/Wiki/ParaView/Data_formats#PVD_File_Format

"""


def writePVD(file_name, times, names):
    # times and names lists should be the same length

    with open(file_name, 'w') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">\n')
        f.write('\t<Collection>\n')
        for i in range(len(times)):
            f.write('\t\t<DataSet timestep="{}" file="{}"/>\n'\
                .format(times[i], names[i]))
        f.write('\t</Collection>\n')
        f.write('</VTKFile>')
