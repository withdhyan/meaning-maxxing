"""
Value store: persistence and graph operations.

Stores the moral graph as a JSON file on disk. Provides PageRank
computation, value lookup, and graph mutation operations.

Storage location: ~/.hermes/values/graph.json
"""

from __future__ import annotations

import json
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
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        closed = False
        try:
            os.write(fd, data.encode())
            os.close(fd)
            closed = True
            os.replace(tmp, self.path)
        except BaseException:
            if not closed:
                os.close(fd)
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
                self._recompute_pagerank()
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

    # -- The Wisdom Score (TWS) --

    def compute_tws(self) -> dict:
        """Compute The Wisdom Score — a composite metric of the user's moral landscape.

        TWS combines three dimensions:

        1. **Depth** (0-1): How much PageRank concentrates in top values.
           High depth means clear, strong commitments. Measured as the ratio
           of max PageRank to uniform PageRank.

        2. **Growth** (0-1): How much moral evolution has occurred. Measured
           as the ratio of upgrade edges to total possible edges, scaled by
           confidence. A graph with many high-confidence upgrades shows a
           person who is actively deepening.

        3. **Coherence** (0-1): How interconnected the value landscape is.
           Measured as the fraction of values that participate in at least
           one edge. A coherent graph means values relate to each other —
           they're not isolated fragments.

        Returns a dict with individual dimension scores and the composite TWS.
        The composite is the geometric mean of the three dimensions — all
        three must be present for a high score. You can't fake wisdom with
        volume alone.
        """
        values = self.graph.values
        edges = self.graph.edges
        pagerank = self.graph.pagerank

        n = len(values)
        if n == 0:
            return {"depth": 0.0, "growth": 0.0, "coherence": 0.0, "tws": 0.0}

        # Depth: how much PageRank concentrates (Gini-like)
        # Compare the spread between max and min rank.
        if pagerank and n > 1:
            ranks = list(pagerank.values())
            rank_range = max(ranks) - min(ranks)
            # Normalize: max possible range approaches 1.0 for extreme graphs
            depth = min(1.0, rank_range * n)
        else:
            depth = 0.0

        # Growth: upgrade density weighted by confidence
        if n > 1 and edges:
            # Scale: 0.5 total weighted confidence across a few edges is healthy
            weighted_edges = sum(e.confidence for e in edges)
            growth = min(1.0, weighted_edges / (n * 0.5))
        else:
            growth = 0.0

        # Coherence: fraction of values with at least one edge
        if n > 1:
            connected_ids = set()
            for e in edges:
                connected_ids.add(e.source_id)
                connected_ids.add(e.wiser_id)
            value_ids = {v.id for v in values}
            coherence = len(connected_ids & value_ids) / n
        else:
            coherence = 0.0

        # Geometric mean — all three must be nonzero for a positive TWS
        if depth > 0 and growth > 0 and coherence > 0:
            tws = (depth * growth * coherence) ** (1.0 / 3.0)
        else:
            tws = 0.0

        return {
            "depth": round(depth, 3),
            "growth": round(growth, 3),
            "coherence": round(coherence, 3),
            "tws": round(tws, 3),
        }

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
                lines.append(self._format_upgrade(u))

        tws = self.compute_tws()
        if tws["tws"] > 0:
            lines.append("")
            lines.append(
                f"TWS: {tws['tws']:.2f} "
                f"(depth: {tws['depth']:.2f}, "
                f"growth: {tws['growth']:.2f}, "
                f"coherence: {tws['coherence']:.2f})"
            )

        return "\n".join(lines)

    def format_upgrades_summary(self) -> str:
        """Human-readable summary of growth trajectories."""
        upgrades = self.graph.upgrades
        if not upgrades:
            return "No growth trajectories recorded yet."

        lines = ["Growth trajectories:\n"]
        for u in upgrades:
            src = self.get_value(u.source_id)
            wiser = self.get_value(u.wiser_id)
            src_name = src.title if src else u.source_id
            wiser_name = wiser.title if wiser else u.wiser_id
            lines.append(f"**{src_name}** \u2192 **{wiser_name}**")
            lines.append(f"  {u.clarification}")
            if u.story:
                lines.append(f"  _{u.story}_")
            lines.append("")

        return "\n".join(lines)

    def _format_upgrade(self, u: Upgrade) -> str:
        src = self.get_value(u.source_id)
        wiser = self.get_value(u.wiser_id)
        src_name = src.title if src else u.source_id
        wiser_name = wiser.title if wiser else u.wiser_id
        return f"  {src_name} \u2192 {wiser_name}: {u.clarification}"
