# src/arkhe/layers/engineering/error_standardization.py
class CanonicalErrorCode:
    CODES = {
        "E001": "Unknown",
        "E002": "Type Mismatch",
        "E003": "Auth Failed",
        "E004": "State Corrupted",
    }

    @classmethod
    def make(cls, code, message):
        return {'code': code, 'description': cls.CODES.get(code, "Unknown"), 'message': message}

# All new exceptions use this scheme
class ArkheError(Exception):
    def __init__(self, code, message):
        super().__init__(f"[{code}] {message}")
        self.error_obj = CanonicalErrorCode.make(code, message)
