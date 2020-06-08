import unittest
from ccx2paraview import Converter


class MyTestCase(unittest.TestCase):
    def test_contact2e(self):
        ccx2paraview = Converter('..\\examples\\ccx_2.16.structest\\contact2e.frd', 'vtu')
        ccx2paraview.run()


if __name__ == '__main__':
    unittest.main()