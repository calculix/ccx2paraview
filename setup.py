#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

long_description = """CalculiX to Paraview converter (frd to vtk/vtu). 
Converts CalculiX FRD file to view and postprocess analysis results 
in Paraview. Generates Mises and Principal components for stress 
and strain tensors."""

setuptools.setup(
    name="ccx2paraview",
    version="2.3.1",
    author="Ihor Mirzov",
    author_email="imirzov@gmail.com",
    description="CalculiX to Paraview converter (frd to vtk/vtu)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/calculix/ccx2paraview",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)