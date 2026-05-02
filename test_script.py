import sys
import os
sys.path.append(os.path.abspath('arkhe-v3277'))
sys.path.append(os.path.abspath('arkhe-v3277/pipeline'))
sys.path.append(os.path.abspath('arkhe-v3277/core'))

try:
    from pipeline.homeostasis_zee200_bridge import HomeostasisZEE200Bridge
    print("Bridge imported.")
except Exception as e:
    print(f"Error: {e}")
