© Ihor Mirzov, 2019-2020  
Distributed under GNU General Public License v3.0

<br/><br/>



---

[Downloads](https://github.com/calculix/ccx2paraview/releases) |
[How to use](#how-to-use) |
[Screenshots](#screenshots) |
[Your help](#your-help) |
[For developers](#for-developers) |
[TODO](#todo)

---

<br/><br/>



# CalculiX to Paraview converter (frd to vtk/vtu)

Converts [CalculiX](http://www.dhondt.de/) ASCII .frd-file to view and postprocess analysis results in [Paraview](https://www.paraview.org/). Generates von Mises and principal components for stress and strain tensors.

Creates separate file for each output interval - it makes possible to animate time history. **Caution!** If you have 300 time steps in the FRD, there will be 300 Paraview files. If you need one file - write output only for one step in your CalculiX model.

Converter is tested on [CalculiX examples](https://github.com/calculix/examples). Here is how some [test log](https://github.com/calculix/ccx2paraview/blob/master/tests/test.log) looks like.

FRD reader is tested to reduce processing time as much as possible. Now it's quite optimized and fast, but Python itself is slower than C/C++. Here we can do nothing, so, for example, [Calmed converter](https://www.salome-platform.org/forum/forum_12/126338563) must be faster - another question is if it's able to read and convert any CalculiX results.

<br/><br/>



# How to use

Please, pay attention to .frd-file type - it should be ASCII, not binary! Use keywords *NODE FILE, *EL FILE and *CONTACT FILE in your INP model to get results in ASCII format.

Running this software from source is not recommended, because sources are under development and may contain bugs. So, first, [download released binaries](https://github.com/calculix/ccx2paraview/releases), unpack them and allow to be executed (give permissions).

Run binary with command:

    in Linux:       ./ccx2paraview yourjobname.frd vtu
                    ./ccx2paraview yourjobname.frd vtk
    in Windows:     ccx2paraview.exe yourjobname.frd vtu
                    ccx2paraview.exe yourjobname.frd vtk

Also you can pass both formats to convert .frd to .vtk and .vtu at once.

It is recommended to convert .frd to modern XML .vtu format - its contents are compressed. If you have more than one time step there will be additional XML file created - [the PVD file](https://www.paraview.org/Wiki/ParaView/Data_formats#PVD_File_Format). Open it in Paraview to read data from all time steps (all VTU files) at ones.

Starting from ccx2paraview v3.0.0 legacy .vtk format is also fully supported - previously there were problems with component names.

**Attention!** While developing this converter I'm using latest Python3, latest VTK and latest Paraview. If you have problems with opening conversion results in Paraview - update it.

<br/><br/>



# Screenshots

Converted von Mises stress field with Turbo colormap:  
![baffle](https://github.com/calculix/ccx2paraview/blob/master/img_baffle.png "baffle")

Converted translations field with Viridis colormap:  
![blades](https://github.com/calculix/ccx2paraview/blob/master/img_blades.png "blades")

<br/><br/>



# Your help

Please, you may:

- Simply use this software and ask questions.
- Share your models and screenshots.
- Report problems by [posting issues](https://github.com/calculix/ccx2paraview/issues).

<br/><br/>



# For developers

To run this converter from source you'll need [Python 3](https://www.python.org/downloads/) with *numpy* and *vtk*. Install all with command:

    pip3 install numpy vtk ccx2paraview

In your code use ccx2paraview package in this way:

    import ccx2paraview
    c = ccx2paraview.Converter(frd_file_name, 'vtu')
    c.run()

If you have Python version >= 3.8 create binary with [nuitka](https://nuitka.net/):

    pip3 install nuitka
    
    In Windows:
    set CC=C:\\MinGW64\\mingw64\\bin\\gcc.exe
    python3 -m nuitka --follow-imports --mingw64 __init__.py

    In Linux:
    python3 -m nuitka --follow-imports __init__.py

If you have Python version < 3.8 create binary with [pyinstaller](https://www.pyinstaller.org/):

    pip3 install pyinstaller
    pyinstaller __init__.py --onefile

Read [here](https://packaging.python.org/tutorials/packaging-projects/) about how to create packages for [pypi.org](https://pypi.org/):

    python3 -m pip install --user --upgrade setuptools wheel twine
    python3 setup.py sdist bdist_wheel
    twine upload dist/*

Read about VTK [file formats](https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf) and VTK [unstructured grid](https://lorensen.github.io/VTKExamples/site/VTKFileFormats/#unstructuredgrid). Remember that FRD file is node based, so element results are also stored at nodes after extrapolation from the integration points.

<br/><br/>



# TODO

Multiprocessing for tests.

Paraview programmable filter for tensor principal directions (eigenvectors).

Read binary .frd files.

Read DAT files: it would be a killer feature if Paraview could visualize results in gauss points.

Contribute to meshio. Use meshio XDMF writer: https://github.com/calculix/ccx2paraview/issues/6
