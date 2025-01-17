import sys
import unittest
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

loader = unittest.TestLoader()
suite = loader.discover("tests")

runner = unittest.TextTestRunner()
runner.run(suite)
