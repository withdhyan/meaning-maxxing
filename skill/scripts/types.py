"""
Value types for the moral graph.

A value is a source of meaning — not a preference, goal, or principle —
expressed as attention policies: concrete things to attend to when
navigating a domain of life.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AttentionPolicy:
    """A single attention policy within a value.

    Format: CAPITALIZED_PLURAL_NOUN + qualifying phrase.
    Example: "MOMENTS where telling a difficult truth opens a new possibility"
    """

    text: str

    def __str__(self) -> str:
        return self.text


@dataclass
class Value:
    """A source of meaning, articulated as attention policies."""

    id: str
    title: str  # 2-5 words
    policies: list[AttentionPolicy]
    description: Optional[str] = None  # first-person micro-story
    embedding: Optional[list[float]] = None
    created_at: float = field(default_factory=time.time)
    source_context: Optional[str] = None  # conversation excerpt that surfaced it

    @property
    def policies_text(self) -> str:
        return "; ".join(str(p) for p in self.policies)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "policies": [p.text for p in self.policies],
            "description": self.description,
            "embedding": self.embedding,
            "created_at": self.created_at,
            "source_context": self.source_context,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Value:
        return cls(
            id=d["id"],
            title=d["title"],
            policies=[AttentionPolicy(text=t) for t in d["policies"]],
            description=d.get("description"),
            embedding=d.get("embedding"),
            created_at=d.get("created_at", time.time()),
            source_context=d.get("source_context"),
        )


@dataclass
class Edge:
    """A wiser-than relationship between two values.

    source_id's value is considered less wise than wiser_id's value
    within the given context.
    """

    source_id: str
    wiser_id: str
    context: str  # the domain or situation where this relationship holds
    confidence: float = 0.0  # 0-1, accumulated from evidence
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "wiser_id": self.wiser_id,
            "context": self.context,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Edge:
        return cls(
            source_id=d["source_id"],
            wiser_id=d["wiser_id"],
            context=d["context"],
            confidence=d.get("confidence", 0.0),
            created_at=d.get("created_at", time.time()),
        )


@dataclass
class Upgrade:
    """A narrative explaining how one value is a wiser version of another.

    This is the moral graph's deepest artifact: a story of growth.
    """

    source_id: str  # the earlier value
    wiser_id: str  # the deeper value
    clarification: str  # what the earlier value was really about
    story: str  # first-person narrative of the transition
    mapping: list[dict]  # how each old policy maps to the new understanding
    likelihood: str  # A-F grade
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "wiser_id": self.wiser_id,
            "clarification": self.clarification,
            "story": self.story,
            "mapping": self.mapping,
            "likelihood": self.likelihood,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Upgrade:
        return cls(
            source_id=d["source_id"],
            wiser_id=d["wiser_id"],
            clarification=d["clarification"],
            story=d["story"],
            mapping=d.get("mapping", []),
            likelihood=d.get("likelihood", "C"),
            created_at=d.get("created_at", time.time()),
        )


@dataclass
class MoralGraph:
    """The complete moral graph: values, their relationships, and growth narratives."""

    values: list[Value] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    upgrades: list[Upgrade] = field(default_factory=list)
    pagerank: dict[str, float] = field(default_factory=dict)  # value_id -> score

    def get_value(self, value_id: str) -> Optional[Value]:
        for v in self.values:
            if v.id == value_id:
                return v
        return None

    def get_edges_from(self, value_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source_id == value_id]

    def get_edges_to(self, value_id: str) -> list[Edge]:
        return [e for e in self.edges if e.wiser_id == value_id]

    def top_values(self, n: int = 5) -> list[Value]:
        """Return the n highest-ranked values by PageRank."""
        ranked = sorted(
            self.values,
            key=lambda v: self.pagerank.get(v.id, 0.0),
            reverse=True,
        )
        return ranked[:n]

    def to_dict(self) -> dict:
        return {
            "values": [v.to_dict() for v in self.values],
            "edges": [e.to_dict() for e in self.edges],
            "upgrades": [u.to_dict() for u in self.upgrades],
            "pagerank": self.pagerank,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MoralGraph:
        return cls(
            values=[Value.from_dict(v) for v in d.get("values", [])],
            edges=[Edge.from_dict(e) for e in d.get("edges", [])],
            upgrades=[Upgrade.from_dict(u) for u in d.get("upgrades", [])],
            pagerank=d.get("pagerank", {}),
        )
