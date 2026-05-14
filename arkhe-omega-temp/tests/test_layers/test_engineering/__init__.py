import unittest
import sys
import os

# Add the src directory to sys.path so we can import from arkhe.layers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

if __name__ == '__main__':
    unittest.main()
