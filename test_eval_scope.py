import os
import sys
sys.path.insert(0, "substrates/9015_arkhe_stdlib")
os.environ["ARKHE_STDLIB_ENABLED"] = "1"
import arkhe_stdlib.compat as compat
compat.activate()

my_var = 42

def func():
    print(eval("my_var"))

func()
