import hashlib
def verify_package(data):
    return hashlib.sha3_256(data).hexdigest()
