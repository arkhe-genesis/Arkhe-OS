import json
import sqlite3
from pathlib import Path

def extract_training_data(ledger_path: str, output_jsonl: str):
    conn = sqlite3.connect(ledger_path)
    cur = conn.execute(
        "SELECT event_type, payload_json, timestamp, hash FROM ledger_entries ORDER BY id"
    )
    with open(output_jsonl, "w") as f:
        for row in cur:
            event_type, payload_str, ts, h = row
            payload = json.loads(payload_str)

            # Construir par (contexto, afirmação)
            if event_type == "solar_plasma_event":
                context = f"Solar event type: {payload['event_type']} at {ts}"
                statement = json.dumps(payload)
                # Afirmação validada (foi registrada no ledger)
                f.write(json.dumps({
                    "context": context,
                    "statement": statement,
                    "label": "valid",
                    "hash": h,
                    "source": "ledger"
                }) + "\n")

            elif event_type == "inter_branch_rejected":
                context = f"Multiverse message rejected: {payload.get('paradox_type')}"
                statement = json.dumps(payload)
                # Afirmação REJEITADA (exemplo do que NÃO afirmar)
                f.write(json.dumps({
                    "context": context,
                    "statement": statement,
                    "label": "rejected",
                    "reason": payload.get("reason"),
                    "source": "ledger"
                }) + "\n")

    conn.close()
    print(f"Corpus exported to {output_jsonl}")

if __name__ == "__main__":
    extract_training_data("/tmp/arkhe_production.db", "arkhe_corpus.jsonl")