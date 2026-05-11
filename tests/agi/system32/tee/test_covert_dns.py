import ctypes
import os
import pytest

# Compile the C code into a shared library for testing
@pytest.fixture(scope="session")
def dns_enclave_lib(tmp_path_factory):
    lib_path = str(tmp_path_factory.mktemp("lib") / "libcovert_dns.so")
    src_path = os.path.join(os.path.dirname(__file__), "../../../../agi/system32/tee/covert_dns_enclave.c")
    os.system(f"gcc -shared -fPIC -o {lib_path} {src_path}")

    lib = ctypes.CDLL(lib_path)

    # Define structs
    class ResolverStruct(ctypes.Structure):
        _fields_ = [
            ("ip_address", ctypes.c_char * 64),
            ("latency_ms", ctypes.c_float),
            ("packet_loss", ctypes.c_float),
            ("coherence_score", ctypes.c_float),
            ("is_active", ctypes.c_int)
        ]

    class SessionStruct(ctypes.Structure):
        _fields_ = [
            ("session_id", ctypes.c_uint32),
            ("resolvers", ResolverStruct * 16),
            ("num_resolvers", ctypes.c_int),
            ("global_coherence", ctypes.c_float),
            ("duplication_count", ctypes.c_int)
        ]

    lib.SessionStruct = SessionStruct
    lib.ResolverStruct = ResolverStruct

    lib.init_covert_dns_session.argtypes = [ctypes.POINTER(SessionStruct), ctypes.c_uint32]
    lib.init_covert_dns_session.restype = ctypes.c_int

    lib.add_resolver.argtypes = [ctypes.POINTER(SessionStruct), ctypes.c_char_p]
    lib.add_resolver.restype = ctypes.c_int

    lib.update_resolver_metrics.argtypes = [ctypes.POINTER(SessionStruct), ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float]
    lib.update_resolver_metrics.restype = ctypes.c_int

    lib.select_best_resolver.argtypes = [ctypes.POINTER(SessionStruct)]
    lib.select_best_resolver.restype = ctypes.POINTER(ResolverStruct)

    lib.encode_dns_payload.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.encode_dns_payload.restype = ctypes.c_int

    lib.decode_dns_payload.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.decode_dns_payload.restype = ctypes.c_int

    return lib

def test_coherence_routing(dns_enclave_lib):
    session = dns_enclave_lib.SessionStruct()
    assert dns_enclave_lib.init_covert_dns_session(ctypes.byref(session), 1001) == 0

    assert dns_enclave_lib.add_resolver(ctypes.byref(session), b"1.1.1.1") == 0
    assert dns_enclave_lib.add_resolver(ctypes.byref(session), b"8.8.8.8") == 0

    # Update metrics: 1.1.1.1 has low latency, 8.8.8.8 has high coherence
    dns_enclave_lib.update_resolver_metrics(ctypes.byref(session), b"1.1.1.1", 10.0, 0.0, 0.4)
    dns_enclave_lib.update_resolver_metrics(ctypes.byref(session), b"8.8.8.8", 50.0, 0.0, 0.9)

    best_resolver = dns_enclave_lib.select_best_resolver(ctypes.byref(session))
    assert best_resolver.contents.ip_address == b"8.8.8.8"
    assert round(best_resolver.contents.coherence_score, 1) == 0.9

def test_resolver_auto_disable(dns_enclave_lib):
    session = dns_enclave_lib.SessionStruct()
    dns_enclave_lib.init_covert_dns_session(ctypes.byref(session), 1002)

    dns_enclave_lib.add_resolver(ctypes.byref(session), b"9.9.9.9")
    dns_enclave_lib.update_resolver_metrics(ctypes.byref(session), b"9.9.9.9", 20.0, 0.0, 0.05)

    best_resolver = dns_enclave_lib.select_best_resolver(ctypes.byref(session))
    # Should be None/Null since it's deactivated
    assert not best_resolver

def test_payload_encode_decode(dns_enclave_lib):
    data = b"Hello Cathedral"
    data_len = len(data)

    data_arr = (ctypes.c_uint8 * data_len)(*data)
    out_buffer = (ctypes.c_uint8 * 256)()
    out_len = ctypes.c_size_t()

    # Encode
    res = dns_enclave_lib.encode_dns_payload(data_arr, data_len, out_buffer, 256, ctypes.byref(out_len))
    assert res == 0

    encoded_bytes = bytes(out_buffer[:out_len.value])
    # Length should be data_len + 7 (DNS_OVERHEAD)
    assert len(encoded_bytes) == data_len + 7

    # Decode
    encoded_arr = (ctypes.c_uint8 * out_len.value)(*encoded_bytes)
    decoded_buffer = (ctypes.c_uint8 * 256)()
    decoded_len = ctypes.c_size_t()

    res = dns_enclave_lib.decode_dns_payload(encoded_arr, out_len.value, decoded_buffer, 256, ctypes.byref(decoded_len))
    assert res == 0

    decoded_bytes = bytes(decoded_buffer[:decoded_len.value])
    assert decoded_bytes == data