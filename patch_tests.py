with open('test_substrates.py', 'r') as f:
    content = f.read()

tests_to_add = """
def test_870_blockchain_z_glm():
    import importlib.util
    import os
    import json
    file_path = os.path.abspath('substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py')
    spec = importlib.util.spec_from_file_location("substrato_870_blockchain_z_glm", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato_870_blockchain_z_glm()
    path = canonizer.canonize()

    assert os.path.exists(path)

def test_865_cohesion_engine():
    import importlib.util
    import os
    import json
    file_path = os.path.abspath('substrates/t/865_cohesion_engine/substrato_865_cohesion_engine.py')
    spec = importlib.util.spec_from_file_location("substrato_865_cohesion_engine", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato_865_cohesion_engine()
    path = canonizer.canonize()

    assert os.path.exists(path)

def test_864_eip8272_recent_roots_bridge():
    import importlib.util
    import os
    import json
    file_path = os.path.abspath('substrates/t/864_eip8272_recent_roots_bridge/substrato_864_eip8272_recent_roots_bridge.py')
    spec = importlib.util.spec_from_file_location("substrato_864_eip8272_recent_roots_bridge", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato_864_eip8272_recent_roots_bridge()
    path = canonizer.canonize()

    assert os.path.exists(path)

"""

with open('test_substrates.py', 'w') as f:
    f.write(content + "\n" + tests_to_add)
