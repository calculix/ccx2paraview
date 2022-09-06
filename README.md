© Ihor Mirzov, 2019-2021  
Distributed under GNU General Public License v3.0

[![PyPi](https://badgen.net/badge/icon/pypi?icon=pypi&label)](https://pypi.org/project/ccx2paraview)
[![PyPi downloads](https://img.shields.io/pypi/dm/ccx2paraview.svg)](https://pypistats.org/packages/ccx2paraview)  
[![GitHub](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/calculix/ccx2paraview)
[![Github All Releases](https://img.shields.io/github/downloads/calculix/ccx2paraview/total.svg)](https://github.com/calculix/ccx2paraview/releases)

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

FRD reader is tested to reduce processing time as much as possible. Now it's quite optimized and fast, but Python itself is slower than C/C++. Here we can do nothing, so, for example, [Calmed converter](https://calculix.discourse.group/t/exporting-mode-shapes/182/7) must be faster - another question is if it's able to read and convert any CalculiX results.

<br/><br/>



# How to use

To run this converter you'll need [Python 3](https://www.python.org/downloads/) with *numpy* and *vtk*:

    pip3 install numpy vtk

Please, pay attention that .frd-file type should be ASCII, not binary! Use keywords *NODE FILE, *EL FILE and *CONTACT FILE in your INP model to get results in ASCII format.

[Download released sources](https://github.com/calculix/ccx2paraview/releases), unpack them and allow to be executed (give permissions).

Run converter with command (both in Linux and in Windows):

    python3 ccx2paraview.py yourjobname.frd vtk
    python3 ccx2paraview.py yourjobname.frd vtu

Also you can pass both formats to convert .frd to .vtk and .vtu at once.

It is recommended to convert .frd to modern XML .vtu format - its contents are compressed. If you have more than one time step there will be additional XML file created - [the PVD file](https://www.paraview.org/Wiki/ParaView/Data_formats#PVD_File_Format). Open it in Paraview to read data from all time steps (all VTU files) at ones.

Starting from ccx2paraview v3.0.0 legacy .vtk format is also fully supported - previously there were problems with component names.

A snippet for Paraview **programmable filter** to convert 6 components data array to full tensor:

```Python
import numpy as np 
res = np.array([])
pd = inputs[0].PointData['S']
for xx,yy,zz,xy,yz,xz in pd:
    t = np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
    res = np.append(res, t)
tensor = dsa.VTKArray(res)
tensor.shape = (len(pd), 3, 3)
output.PointData.append(tensor, 'S_tensor')
```

A snippet for Paraview programmable filter to calculate eigenvalues and eigenvectors:

```Python
import numpy as np
eigenvalues = np.array([])
eigenvectors = np.array([])
pd = inputs[0].PointData['S']
for xx,yy,zz,xy,yz,xz in pd:
    t = np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
    w, v = np.linalg.eig(t)
    w_ = np.absolute(w).tolist()
    i = w_.index(max(w_))
    eigenvalues = np.append(eigenvalues, w[i]) # max abs eigenvalue
    eigenvectors = np.append(eigenvectors, v[i]) # max principal vector
eigenvectors = dsa.VTKArray(eigenvectors)
eigenvalues = dsa.VTKArray(eigenvalues)
eigenvectors.shape = (len(pd), 3)
eigenvalues.shape = (len(pd), 1)
output.PointData.append(eigenvectors, 'S_max_principal_vectors')
output.PointData.append(eigenvalues, 'S_max_eigenvalues')
```

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

- Star this project.
- Simply use this software and ask questions.
- Share your models and screenshots.
- Report problems by [posting issues](https://github.com/calculix/ccx2paraview/issues).

<br/><br/>



# For developers

[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ccx2paraview.svg)](https://www.python.org/downloads/)
[![Visual Studio Code](https://img.shields.io/badge/--007ACC?logo=visual%20studio%20code&logoColor=ffffff)](https://code.visualstudio.com/)

[![CalculiX-to-Paraview Converter](https://img.youtube.com/vi/KofE0x0csZE/maxresdefault.jpg)](https://www.youtube.com/watch?v=KofE0x0csZE)

Install package with dependacies:

    pip3 install numpy vtk ccx2paraview

In your code use ccx2paraview package in this way:

```Python
    import logging
    import ccx2paraview
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    c = ccx2paraview.Converter(frd_file_name, ['vtu'])
    c.run()
```

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

Also there is a good way to create a binary with Cython (works fine for a signle module):

    sudo apt install cython3
    cython3 -3 --embed -o ccx2paraview.c ccx2paraview.py
    PYTHONLIBVER=python$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')$(python3-config --abiflags)
    gcc -Os $(python3-config --includes) ccx2paraview.c -o ccx2paraview $(python3-config --ldflags) -l$PYTHONLIBVER

Read [how to create packages](https://packaging.python.org/tutorials/packaging-projects/) for [pypi.org](https://pypi.org/):

    python3 -m pip install --user --upgrade setuptools wheel twine
    python3 setup.py sdist bdist_wheel
    twine upload dist/*

Read about VTK [file formats](https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf) and VTK [unstructured grid](https://kitware.github.io/vtk-examples/site/VTKFileFormats/#unstructuredgrid). Remember that FRD file is node based, so element results are also stored at nodes after extrapolation from the integration points.

<br/><br/>



# TODO

Read DAT files: it would be a killer feature if Paraview could visualize results in Gauss points. Use [CCXStressReader](https://github.com/Mote3D/CCXStressReader).

Multiprocessing for tests.

Read binary .frd files.

Process huge files increment by increment.

Contribute to meshio. FRD writer. Use meshio XDMF writer: https://github.com/calculix/ccx2paraview/issues/6

Include an integer scalar containing each element’s GROUP or MATERIAL.

Add element’s material tangent stiffness tensor. Easiest for the paraview user would be to provide it in the (deflected) global cartesian frame. This dataset is useful for checking input data for anisotropic materials, as well as for the stuff with inverse design of fields of this tensor. But it’s a lot more work to produce, especially with nonlinear materials. It’s almost as useful to see the highest principal value of the stiffness, as a scalar or a vector. (but for the vector you need to do the transformation)
