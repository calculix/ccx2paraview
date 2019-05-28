# Tests

Folders *tests-elements*, *tests-examples* and *tests-users* contain .inp-tasks + .frd-calculation + .vtk and .vtu convertion results. They are needed for the development process.

- *tests elements* contains tests of mesh conversion
- *tests-examples* are taken directly from [Calculix examples](http://www.dhondt.de/ccx_2.15.test.tar.bz2)
- *tests-users* contains files sent by users

You'll need */usr/local/bin/ccx* command to be available in your system. Run all tests with command:

    python3 tests.py

<br/><br/>



# FRDParser_original.py

[Original code](https://gitlab.lrz.de/snippets/238) of the FRD parser, written by Lukas Bante, LRZ, in Sep 2017.
