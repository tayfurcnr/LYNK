import pytest
import time
import random
from lynk.core.frame_router import route_frame
from lynk.core.frame_codec import parse_mesh_frame
from lynk.application.telemetry.tools.cache import reset_cache, get_device_hop_count

class VirtualNetwork:
    """Simulates a mesh network with multiple nodes and custom connectivity."""
    def __init__(self):
        self.nodes = {} # node_id -> MockInterface
        
    def add_node(self, node_id, interface):
        self.nodes[node_id] = interface

    def broadcast_from(self, src_id, frame_bytes, reachable_nodes):
        """Delivers a frame from src_id to a list of reachable node IDs."""
        for dst_id in reachable_nodes:
            if dst_id in self.nodes:
                # We need to simulate the hardware reception
                try:
                    frame_dict = parse_mesh_frame(frame_bytes)
                    # Use a small delay to simulate air time
                    self.nodes[dst_id].receive(frame_bytes, frame_dict)
                except (ValueError, KeyError) as e:
                    # Log parsing errors but continue
                    pass

class MockMeshInterface:
    def __init__(self, node_id, network, reachable_ids):
        self.node_id = node_id
        self.network = network
        self.reachable_ids = reachable_ids
        self.received_frames = []

    def send(self, frame_bytes):
        """Physical Layer Send"""
        self.network.broadcast_from(self.node_id, frame_bytes, self.reachable_ids)

    def receive(self, frame_bytes, frame_dict):
        """Physical Layer Receive -> Pass to Router"""
        self.received_frames.append(frame_dict)
        # In a real app, this is called by the UART listener
        # We simulate routing logic here
        from lynk.core.frame_router import route_frame
        route_frame(frame_dict, self)

@pytest.fixture(autouse=True)
def setup_mesh():
    from lynk.shared.config import manager
    manager._config = {
        "vehicle": {"id": 1, "team_id": 0},
        "protocol": {"start_byte": 0x24, "start_byte_2": 0x24, "version": 1},
        "relay": {"enabled": True, "max_hops": 3, "delay_ms": 1}
    }
    reset_cache()
    from lynk.core.relay_cache import get_relay_cache
    get_relay_cache()._cache.clear()
    
    from lynk.core.sequence_manager import get_sequence_manager
    sm = get_sequence_manager()
    sm._out_seq = 0
    sm._in_seq_map.clear()
    
    yield

def test_multi_hop_relay_depth():
    """
    Test a linear topology: Node 1 <-> Node 2 <-> Node 3 <-> Node 4
    Node 1 sends a packet. Node 4 should receive it after 3 hops.
    """
    net = VirtualNetwork()
    
    # 1 sees 2 | 2 sees 1,3 | 3 sees 2,4 | 4 sees 3
    # Note: We need to mock load_device_id and load_team_id globally or per-call
    # This is tricky because route_frame uses load_device_id() from frame_codec
    
    # Let's monkeypatch load_device_id for each router call or use a more isolated router
    import lynk.core.frame_router as fr
    import lynk.core.frame_codec as fc
    
    # We will track how many times Node 4 receives the same packet
    node_4_receivings = []

    def custom_route(node_id, frame_dict, interface):
        import lynk.shared.config.manager as sm
        # Mocking global state for the duration of this call
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(fc, "load_device_id", lambda: node_id)
            mp.setattr(fc, "load_team_id", lambda: 0)
            return fr.route_frame(frame_dict, interface)

    # Simplified simulation for this test
    # We'll just verify the logic of hop_count incrementing
    from lynk.core.frame_codec import build_mesh_frame
    
    # Original frame from Node 1
    packet = build_mesh_frame(frame_type='T', src_id=1, dst_id=0xFF, payload=b"hello", seq_num=100)
    
    # Hop 1 (Node 2 receives and relays)
    # To bypass replay checking, we'll manually increment the seq map or mock it
    from lynk.core.sequence_manager import get_sequence_manager
    sm = get_sequence_manager()

    frame_at_2 = parse_mesh_frame(packet)
    assert frame_at_2['hop_count'] == 0
    
    # Simulate Relay at Node 2
    class RelayInterface:
        def __init__(self): self.sent_frames = []
        def send(self, f): self.sent_frames.append(f)
        
    iface_2 = RelayInterface()
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(fc, "load_device_id", lambda: 2)
        fr.relay_frame(frame_at_2, iface_2)
    
    # Before parsing next jump, reset the in_seq_map for test purposes
    sm._in_seq_map.clear()
    relayed_by_2 = parse_mesh_frame(iface_2.sent_frames[0])
    assert relayed_by_2['hop_count'] == 1
    
    # Hop 2 (Node 3 receives and relays)
    iface_3 = RelayInterface()
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(fc, "load_device_id", lambda: 3)
        fr.relay_frame(relayed_by_2, iface_3)
        
    sm._in_seq_map.clear()
    relayed_by_3 = parse_mesh_frame(iface_3.sent_frames[0])
    assert relayed_by_3['hop_count'] == 2

    # Hop 3 (Node 4 receives - TTL Limit Check)
    # If max_hops is 3, hop_count=3 should NOT be relayed further
    # Let's verify should_relay_frame returns False at hop 3
    relayed_by_3['hop_count'] = 3
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(fc, "load_device_id", lambda: 4)
        assert fr.should_relay_frame(relayed_by_3) == False # TTL Exceeded

def test_source_suppression_prevents_loop():
    """Verify that a node does not relay its own packet if it comes back."""
    import lynk.core.frame_router as fr
    import lynk.core.frame_codec as fc
    
    my_packet = {
        "src_id": 1,
        "dst_id": 0xFF,
        "hop_count": 1,
        "frame_type": ord('T'),
        "team_id": 0,
        "seq_num": 500
    }
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(fc, "load_device_id", lambda: 1) # I am node 1
        assert fr.should_relay_frame(my_packet) == False # Suppression triggered

