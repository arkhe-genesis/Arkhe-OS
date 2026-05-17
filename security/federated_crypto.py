import json

def encrypt_model_update(update_obj, pubkey):
    # Dummy encryption
    return {"encrypted": True, "data": update_obj}

def decrypt_model_update(encrypted_obj, privkey):
    # Dummy decryption
    return encrypted_obj["data"]
