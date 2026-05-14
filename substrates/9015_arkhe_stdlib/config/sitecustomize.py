import sys
import os

# Adiciona o diretório substrates/9015_arkhe_stdlib ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import arkhe_stdlib.compat
    arkhe_stdlib.compat.activate()
except ImportError:
    pass
