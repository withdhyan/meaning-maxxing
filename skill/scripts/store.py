"""
Value store: persistence and graph operations.

Stores the moral graph as a JSON file on disk. Provides PageRank
computation, value lookup, and graph mutation operations.

Storage location: ~/.hermes/values/graph.json
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Optional

from .types import Edge, MoralGraph, Upgrade, Value

DEFAULT_STORE_PATH = Path.home() / ".hermes" / "values" / "graph.json"


class ValueStore:
    """Persistent moral graph backed by a JSON file."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or DEFAULT_STORE_PATH
        self.graph = self._load()

    def _load(self) -> MoralGraph:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                return MoralGraph.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                return MoralGraph()
        return MoralGraph()

    def save(self) -> None:
        """Persist the graph to disk atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(self.graph.to_dict(), indent=2)
        # Atomic write: temp file + rename
        fd, tmp = tempfile.mkstemp(
            dir=self.path.parent, suffix=".tmp"
        )
        try:
            os.write(fd, data.encode())
            os.close(fd)
            os.replace(tmp, self.path)
        except BaseException:
            os.close(fd) if not os.get_inheritable(fd) else None
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # -- Mutations --

    def add_value(self, value: Value) -> None:
        self.graph.values.append(value)
        self._recompute_pagerank()
        self.save()

    def add_edge(self, edge: Edge) -> None:
        # Merge with existing edge if same source/wiser pair
        for existing in self.graph.edges:
            if (existing.source_id == edge.source_id
                    and existing.wiser_id == edge.wiser_id):
                existing.confidence = min(1.0, existing.confidence + edge.confidence)
                self.save()
                return
        self.graph.edges.append(edge)
        self._recompute_pagerank()
        self.save()

    def add_upgrade(self, upgrade: Upgrade) -> None:
        self.graph.upgrades.append(upgrade)
        self.save()

    def remove_value(self, value_id: str) -> bool:
        before = len(self.graph.values)
        self.graph.values = [v for v in self.graph.values if v.id != value_id]
        if len(self.graph.values) < before:
            # Clean up related edges and upgrades
            self.graph.edges = [
                e for e in self.graph.edges
                if e.source_id != value_id and e.wiser_id != value_id
            ]
            self.graph.upgrades = [
                u for u in self.graph.upgrades
                if u.source_id != value_id and u.wiser_id != value_id
            ]
            self._recompute_pagerank()
            self.save()
            return True
        return False

    # -- Queries --

    def get_all_values(self) -> list[Value]:
        return list(self.graph.values)

    def get_value(self, value_id: str) -> Optional[Value]:
        return self.graph.get_value(value_id)

    def top_values(self, n: int = 5) -> list[Value]:
        return self.graph.top_values(n)

    def get_upgrades_for(self, value_id: str) -> list[Upgrade]:
        return [
            u for u in self.graph.upgrades
            if u.source_id == value_id or u.wiser_id == value_id
        ]

    def get_recent_upgrades(self, n: int = 3) -> list[Upgrade]:
        sorted_upgrades = sorted(
            self.graph.upgrades, key=lambda u: u.created_at, reverse=True
        )
        return sorted_upgrades[:n]

    # -- PageRank --

    def _recompute_pagerank(self) -> None:
        """Weighted PageRank over the wiser-than graph.

        Damping factor 0.85, 100 iterations. Edge weights are confidence scores.
        Higher rank = more values consider this one "wiser" = deeper commitment.
        """
        values = self.graph.values
        edges = self.graph.edges

        if not values:
            self.graph.pagerank = {}
            return

        n = len(values)
        ids = [v.id for v in values]
        id_to_idx = {vid: i for i, vid in enumerate(ids)}

        # Initialize uniform
        rank = [1.0 / n] * n
        damping = 0.85

        # Build adjacency: edge from source to wiser means
        # "wiser receives rank from source"
        outgoing_weight = [0.0] * n
        incoming: list[list[tuple[int, float]]] = [[] for _ in range(n)]

        for edge in edges:
            src_idx = id_to_idx.get(edge.source_id)
            dst_idx = id_to_idx.get(edge.wiser_id)
            if src_idx is None or dst_idx is None:
                continue
            weight = edge.confidence if edge.confidence > 0 else 0.1
            outgoing_weight[src_idx] += weight
            incoming[dst_idx].append((src_idx, weight))

        for _ in range(100):
            new_rank = [(1.0 - damping) / n] * n
            for i in range(n):
                for src_idx, weight in incoming[i]:
                    if outgoing_weight[src_idx] > 0:
                        new_rank[i] += (
                            damping * rank[src_idx] * weight
                            / outgoing_weight[src_idx]
                        )
            rank = new_rank

        self.graph.pagerank = {ids[i]: rank[i] for i in range(n)}

    # -- Display --

    def format_graph_summary(self) -> str:
        """Human-readable summary of the moral graph."""
        values = self.graph.values
        if not values:
            return "No values recorded yet."

        lines = [f"Moral graph: {len(values)} values, {len(self.graph.edges)} edges\n"]

        top = self.top_values(min(7, len(values)))
        for i, v in enumerate(top, 1):
            score = self.graph.pagerank.get(v.id, 0.0)
            lines.append(f"{i}. **{v.title}** (rank: {score:.3f})")
            for p in v.policies:
                lines.append(f"   - {p}")
            if v.description:
                lines.append(f"   _{v.description}_")
            lines.append("")

        if self.graph.upgrades:
            lines.append("Growth trajectories:")
            for u in self.get_recent_upgrades(3):
                src = self.get_value(u.source_id)
                wiser = self.get_value(u.wiser_id)
                src_name = src.title if src else u.source_id
                wiser_name = wiser.title if wiser else u.wiser_id
                lines.append(f"  {src_name} → {wiser_name}: {u.clarification}")

        return "\n".join(lines)
