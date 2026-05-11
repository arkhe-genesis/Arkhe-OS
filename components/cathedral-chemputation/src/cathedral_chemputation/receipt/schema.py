"""
schema.py — JSON Schema para receipts científicos de chemputation
"""

SCHEMATIC_RECEIPT = {
    "$schema": "https://cathedral.ark/schemas/receipt/v1",
    "type": "object",
    "required": ["receipt_id", "timestamp", "domain", "version", "data_hash", "merkle_root"],
    "properties": {
        "receipt_id": {
            "type": "string",
            "pattern": "^chem_[a-f0-9]{12}_[0-9]+$"
        },
        "timestamp": {"type": "number"},
        "domain": {
            "type": "string",
            "const": "chemputation"
        },
    }
}
