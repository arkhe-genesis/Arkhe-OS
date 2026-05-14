import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'substrates', '9012_arkhe_ipython')))

from arkhe_ipython.magics import ArkheMagics
class MockShell:
    pass
magics = ArkheMagics(MockShell())
magics.arkhe("scan import os; os.system('ls')")
