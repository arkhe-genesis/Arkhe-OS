import asyncio
from arkhe_timechain.core import TemporalChain, EventType
from arkhe_timechain.ma_s2_integration import MA_S2_TimechainIntegration
import os

async def main():
    if os.path.exists("timechain.db"):
        os.remove("timechain.db")

    tc = TemporalChain(storage_backend="sqlite", storage_config={"path": "timechain.db"})

    # Test ancorar
    anchor = await tc.anchor_event(
        event_type=EventType.CUSTOM,
        payload={"msg": "Hello World"},
        metadata={"user": "admin"}
    )
    print(f"Anchored event: {anchor.event.event_id}, position: {anchor.position}")

    # Test query
    events = await tc.query_events(event_type=EventType.CUSTOM)
    print(f"Queried {len(events)} events. First event payload: {events[0].payload}")

    # Test MA-S2
    mas2 = MA_S2_TimechainIntegration(tc)
    seal = await mas2.log_control_execution("CVS-0.1", {"status": "compliant"}, {"scan_id": "123"})
    print(f"MA-S2 log seal: {seal}")

    proof = await mas2.generate_compliance_proof(["CVS-0.1"])
    print(f"Compliance proof events: {proof['event_count']}")

    valid = await tc.verify_chain()
    print(f"Chain valid: {valid}")

asyncio.run(main())
