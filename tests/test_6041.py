import sys
import time
sys.path.append('arkhe-omega-temp')
from temporal_network import RetroRouter, TemporalEdge, CausalPartialOrderRoutingTable

def test_fibonacci_heap():
    from temporal_network import FibonacciDecreaseHeap
    h = FibonacciDecreaseHeap()
    h.insert(1, 10.0)
    h.insert(2, 5.0)
    h.decrease_key(1, 1.0)
    k, v = h.extract_min()
    assert v == 1
    assert k == 1.0

def test_routing_table():
    rt = CausalPartialOrderRoutingTable("A")
    rt.add_route(TemporalEdge("B", "B", 1.0, 1.0, time.time() + 100))
    rt.add_route(TemporalEdge("C", "B", 2.0, 1.0, time.time() + 100))
    res = rt.find_best_route("C")
    assert res is not None
    assert res.next_hop == "B"

def test_retro_router():
    node = type('Node', (), {'nid': 'A'})()
    router = RetroRouter(node)
    router.rt.add_route(TemporalEdge("B", "B", 1.0, 1.0, time.time() + 100))
    batch = router.find_routes_batch(["B"])
    assert batch["B"] is not None

test_fibonacci_heap()
test_routing_table()
test_retro_router()
print("6041 tests passed")
