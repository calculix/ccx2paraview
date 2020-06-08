from __future__ import unicode_literals
from setuptools import setup, find_packages

setup(

    name='ccx2paraview',
    version='0.0.1',
    description='A tool for converting results from calculix to paraview',
    packages=find_packages(exclude=['contrib', 'docs', 'dev', 'ci', 'examples', 'tests']),
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    platforms=['x64'],
    keywords=['Python', 'Structural Analysis', 'Interoperability', 'Automation'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
)