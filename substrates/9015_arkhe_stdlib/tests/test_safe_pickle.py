import pytest
import pickle
import io
from arkhe_stdlib import ArkheSecurityError
from arkhe_stdlib import safe_pickle

class MaliciousPayload:
    def __reduce__(self):
        import os
        return (os.system, ('echo hacked',))

def test_safe_pickle_loads_blocked():
    payload = pickle.dumps(MaliciousPayload())
    with pytest.raises(ArkheSecurityError) as exc:
        safe_pickle.loads(payload)
    assert "UNSAFE_REDUCE_DETECTED" in str(exc.value)

def test_safe_pickle_load_blocked():
    payload = pickle.dumps(MaliciousPayload())
    file_obj = io.BytesIO(payload)
    with pytest.raises(ArkheSecurityError) as exc:
        safe_pickle.load(file_obj)
    assert "UNSAFE_REDUCE_DETECTED" in str(exc.value)

def test_safe_pickle_allowed():
    # Deve permitir dados seguros
    data = {'key': 'value'}
    payload = pickle.dumps(data)
    loaded = safe_pickle.loads(payload)
    assert loaded == data
