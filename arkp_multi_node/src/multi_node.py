#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_node.py — Substrato 9013: Multi-No Deploy com qhttp:// Sync
Deploy distribuido com sincronizacao via qhttp:// Wheeler Mesh Protocol.
"""

import asyncio
import hashlib
import json
import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
from collections import defaultdict


class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    DEGRADED = "degraded"


class SyncPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class WheelerMeshNode:
    node_id: str
    host: str
    port: int
    region: str
    status: NodeStatus
    last_heartbeat: float
    reputation_score: float
    capabilities: List[str]
    peers: Set[str] = field(default_factory=set)
    sync_queue: List[Dict] = field(default_factory=list)


@dataclass
class QHTTPMessage:
    message_id: str
    sender: str
    recipient: str
    payload: Dict
    priority: SyncPriority
    timestamp: float
    ttl: int = 5
    signature: Optional[str] = None


class WheelerMeshNetwork:
    """Rede Wheeler Mesh para sincronizacao distribuida."""

    def __init__(self, node_id: str, host: str, port: int, region: str):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.region = region
        self.nodes: Dict[str, WheelerMeshNode] = {}
        self.messages: Dict[str, QHTTPMessage] = {}
        self.merkle_roots: Dict[str, str] = {}
        self.crdt_state: Dict[str, Dict] = defaultdict(dict)
        self._running = False
        self._sync_interval = 30.0

    def register_node(self, node: WheelerMeshNode) -> bool:
        if node.node_id in self.nodes:
            return False
        self.nodes[node.node_id] = node
        for existing_id, existing in self.nodes.items():
            if existing_id != node.node_id:
                node.peers.add(existing_id)
                existing.peers.add(node.node_id)
        return True

    def create_message(self, recipient: str, payload: Dict,
                       priority: SyncPriority = SyncPriority.NORMAL) -> QHTTPMessage:
        msg_id = hashlib.sha3_256(
            f"{self.node_id}:{recipient}:{time.time()}:{random.random()}".encode()
        ).hexdigest()[:16]
        msg = QHTTPMessage(
            message_id=msg_id,
            sender=self.node_id,
            recipient=recipient,
            payload=payload,
            priority=priority,
            timestamp=time.time(),
        )
        msg.signature = hashlib.sha3_256(
            json.dumps({"id": msg_id, "sender": self.node_id, "recipient": recipient,
                        "payload": payload, "timestamp": msg.timestamp}, sort_keys=True).encode()
        ).hexdigest()
        self.messages[msg_id] = msg
        return msg

    async def broadcast_sync(self, payload: Dict,
                             priority: SyncPriority = SyncPriority.NORMAL) -> List[str]:
        sent = []
        for peer_id in self.nodes:
            if peer_id == self.node_id:
                continue
            msg = self.create_message(peer_id, payload, priority)
            success = await self._send_message(msg)
            if success:
                sent.append(peer_id)
        return sent

    async def _send_message(self, msg: QHTTPMessage) -> bool:
        await asyncio.sleep(0.01)
        recipient = self.nodes.get(msg.recipient)
        if not recipient or recipient.status == NodeStatus.OFFLINE:
            return False
        recipient.sync_queue.append({"message_id": msg.message_id, "payload": msg.payload, "timestamp": msg.timestamp})
        return True

    async def sync_crdt(self, key: str, value: Dict) -> Dict:
        current = self.crdt_state.get(key, {})
        merged = self._merge_crdt(current, value)
        self.crdt_state[key] = merged
        await self.broadcast_sync({"type": "crdt_sync", "key": key, "value": merged, "node": self.node_id}, SyncPriority.HIGH)
        return merged

    def _merge_crdt(self, local: Dict, remote: Dict) -> Dict:
        merged = local.copy()
        for k, v in remote.items():
            if k not in merged or v.get("_version", 0) > merged[k].get("_version", 0):
                merged[k] = v
        return merged

    def compute_merkle_root(self, data: List[Dict]) -> str:
        if not data:
            return hashlib.sha3_256(b"empty").hexdigest()
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha3_256(canonical.encode()).hexdigest()

    async def gossip_protocol(self) -> Dict:
        online_peers = [n for n in self.nodes.values() if n.status == NodeStatus.ONLINE and n.node_id != self.node_id]
        if not online_peers:
            return {"gossiped": 0}
        fanout = min(3, len(online_peers))
        targets = random.sample(online_peers, fanout)
        gossip_payload = {"type": "gossip", "node": self.node_id, "known_nodes": list(self.nodes.keys()),
                          "merkle_roots": self.merkle_roots, "timestamp": time.time()}
        gossiped = 0
        for target in targets:
            msg = self.create_message(target.node_id, gossip_payload, SyncPriority.LOW)
            success = await self._send_message(msg)
            if success:
                gossiped += 1
        return {"gossiped": gossiped, "targets": [t.node_id for t in targets]}

    async def heartbeat(self):
        while self._running:
            self.nodes[self.node_id].last_heartbeat = time.time()
            for node in self.nodes.values():
                if node.node_id == self.node_id:
                    continue
                if time.time() - node.last_heartbeat > 60:
                    node.status = NodeStatus.OFFLINE
            await asyncio.sleep(self._sync_interval)

    async def start(self):
        self._running = True
        asyncio.create_task(self.heartbeat())
        print(f"[9013] No {self.node_id} iniciado em {self.host}:{self.port} ({self.region})")

    async def stop(self):
        self._running = False
        self.nodes[self.node_id].status = NodeStatus.OFFLINE
        print(f"[9013] No {self.node_id} offline")

    def get_network_status(self) -> Dict:
        return {
            "node_id": self.node_id,
            "total_nodes": len(self.nodes),
            "online_nodes": sum(1 for n in self.nodes.values() if n.status == NodeStatus.ONLINE),
            "regions": list(set(n.region for n in self.nodes.values())),
            "messages_in_flight": len(self.messages),
            "crdt_keys": list(self.crdt_state.keys()),
            "merkle_roots": self.merkle_roots,
        }


class MultiNodeDeployer:
    """Orquestrador de deploy multi-no."""

    def __init__(self):
        self.networks: Dict[str, WheelerMeshNetwork] = {}
        self._deployments: Dict[str, Dict] = {}

    def create_deployment(self, deployment_id: str, nodes_config: List[Dict]) -> WheelerMeshNetwork:
        seed_config = nodes_config[0]
        seed = WheelerMeshNetwork(seed_config["id"], seed_config["host"], seed_config["port"], seed_config["region"])
        for config in nodes_config:
            node = WheelerMeshNode(
                node_id=config["id"], host=config["host"], port=config["port"], region=config["region"],
                status=NodeStatus.ONLINE, last_heartbeat=time.time(),
                reputation_score=config.get("reputation", 0.8),
                capabilities=config.get("capabilities", ["review", "sync"]),
            )
            seed.register_node(node)
        self.networks[deployment_id] = seed
        self._deployments[deployment_id] = {"nodes": [n["id"] for n in nodes_config], "created_at": time.time(), "status": "active"}
        return seed

    async def deploy_arkhe_cluster(self, deployment_id: str = "arkhe-prod") -> Dict:
        nodes = [
            {"id": "gru-tc-01", "host": "10.0.1.10", "port": 8443, "region": "sa-east-1", "reputation": 0.95, "capabilities": ["review", "sync", "gateway"]},
            {"id": "tky-tc-02", "host": "10.0.2.10", "port": 8443, "region": "ap-northeast-1", "reputation": 0.92, "capabilities": ["review", "sync"]},
            {"id": "fra-tc-03", "host": "10.0.3.10", "port": 8443, "region": "eu-central-1", "reputation": 0.88, "capabilities": ["review", "sync", "bridge"]},
            {"id": "iad-tc-04", "host": "10.0.4.10", "port": 8443, "region": "us-east-1", "reputation": 0.90, "capabilities": ["review", "sync", "verify"]},
            {"id": "sin-tc-05", "host": "10.0.5.10", "port": 8443, "region": "ap-southeast-1", "reputation": 0.87, "capabilities": ["review", "sync"]},
        ]
        network = self.create_deployment(deployment_id, nodes)
        await network.start()
        await network.sync_crdt("review_tasks", {
            "task-001": {"_version": 1, "status": "pending", "node": "gru-tc-01"},
            "task-002": {"_version": 1, "status": "pending", "node": "tky-tc-02"},
        })
        gossip = await network.gossip_protocol()
        return {
            "deployment_id": deployment_id,
            "nodes_deployed": len(nodes),
            "network_status": network.get_network_status(),
            "gossip_round": gossip,
            "merkle_root": network.compute_merkle_root(list(network.crdt_state.values())),
        }