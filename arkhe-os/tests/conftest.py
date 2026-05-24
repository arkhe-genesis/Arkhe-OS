import sys
import os

# Ensure the arkhe-os path is the absolute first path, prioritizing it over /app
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
