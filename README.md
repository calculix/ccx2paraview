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

Converts [CalculiX](http://www.dhondt.de/) .frd-file to view and postprocess analysis results in [Paraview](https://www.paraview.org/). Generates Mises and Principal components for stress and strain tensors.

Creates separate file for each output interval - it makes possible to animate time history. **Caution!** If you have 300 time steps in the FRD, there will be 300 Paraview files. If you need one file - write output only for one step in your CalculiX model.

Converter is tested on [CalculiX examples](https://github.com/calculix/examples). Here is how some [test log](https://github.com/calculix/ccx2paraview/blob/master/tests/test.log) looks like.

FRD parser is tested to reduce processing time as much as possible. Now it's quite optimized and fast, but Python itself is slower than C/C++. Here we can do nothing, so, for example, [Calmed converter](https://www.salome-platform.org/forum/forum_12/126338563) must be faster - another question is if it's able to parse and convert any CalculiX results.

<br/><br/>



# How to use

Running this software from source is not recommended, because sources are under development and may contain bugs. So, first, [download released binaries](https://github.com/calculix/ccx2paraview/releases), unpack them and allow to be executed (give permissions).

Run the binary with command:

    in Linux:       ./ccx2paraview yourjobname.frd vtu
                    ./ccx2paraview yourjobname.frd vtk
    in Windows:     ccx2paraview.exe yourjobname.frd vtu
                    ccx2paraview.exe yourjobname.frd vtk

It is recommended to convert .frd to modern XML .vtu format - its contents are compressed. If you have more than one time step there will be additional XML file created - the PVD file. Open it in Paraview to read data from all time steps (all VTU files) at ones.

Starting from ccx2paraview v3.0.0 legacy .vtk format is also fully supported - previously there were problems with component names. Also you can pass both formats to convert .frd to .vtk and .vtu at once.

**Attention!** While developing this converter I'm using latest Python3, latest VTK and latest Paraview. If you have problems with opening conversion results in Paraview - update it.

<br/><br/>



# Screenshots

![baffle](https://github.com/calculix/ccx2paraview/blob/master/img_baffle.png "baffle")

![piston](https://github.com/calculix/ccx2paraview/blob/master/img_piston.png "piston")

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

Create binary with [pyinstaller](https://www.pyinstaller.org/):

    pip3 install pyinstaller
    pyinstaller ./ccx2paraview/__init__.py --onefile

Read [here](https://packaging.python.org/tutorials/packaging-projects/) about how to create packages for [pypi.org](https://pypi.org/):

    python3 -m pip install --user --upgrade setuptools wheel
    python3 setup.py sdist bdist_wheel
    twine upload dist/*

Read about VTK [file formats](https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf) and VTK [unstructured grid](https://lorensen.github.io/VTKExamples/site/VTKFileFormats/#unstructuredgrid). Remember that FRD file is node based, so element results are also stored at the nodes after extrapolation from the integration points.

<br/><br/>



# TODO

Move PVD writer into writer.py.

XDMF writer: https://github.com/calculix/ccx2paraview/issues/6

Parse DAT files: it would be a killer feature if Paraview could visualize gauss point results.
https://public.kitware.com/pipermail/paraview/2013-January/027121.html

Multiprocessing for tests.
