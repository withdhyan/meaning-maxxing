"""Tests for types: round-trip serialization, edge cases, invariants."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skill"))

from scripts.types import AttentionPolicy, Edge, MoralGraph, Upgrade, Value


# -- Value --

def test_value_round_trip():
    v = Value(
        id="abc",
        title="Quiet Stewardship",
        policies=[
            AttentionPolicy("MOMENTS where care is given without being asked"),
            AttentionPolicy("SIGNS that something fragile is being tended"),
        ],
        description="I'm watering the plants before anyone wakes up.",
        source_context="User talked about tending a garden.",
    )
    d = v.to_dict()
    v2 = Value.from_dict(d)
    assert v2.id == "abc"
    assert v2.title == "Quiet Stewardship"
    assert len(v2.policies) == 2
    assert v2.policies[0].text == "MOMENTS where care is given without being asked"
    assert v2.description == "I'm watering the plants before anyone wakes up."
    assert v2.source_context == "User talked about tending a garden."


def test_value_from_dict_missing_optional_fields():
    d = {"id": "x", "title": "Test", "policies": ["WAYS of being"]}
    v = Value.from_dict(d)
    assert v.description is None
    assert v.embedding is None
    assert v.source_context is None
    assert v.created_at > 0


def test_value_policies_text():
    v = Value(
        id="a", title="T",
        policies=[AttentionPolicy("MOMENTS of joy"), AttentionPolicy("SIGNS of care")],
    )
    assert v.policies_text == "MOMENTS of joy; SIGNS of care"


def test_attention_policy_str():
    p = AttentionPolicy("CHOICES that honor the long game")
    assert str(p) == "CHOICES that honor the long game"


# -- Edge --

def test_edge_round_trip():
    e = Edge(source_id="a", wiser_id="b", context="work", confidence=0.8)
    d = e.to_dict()
    e2 = Edge.from_dict(d)
    assert e2.source_id == "a"
    assert e2.wiser_id == "b"
    assert e2.context == "work"
    assert e2.confidence == 0.8


def test_edge_defaults():
    e = Edge(source_id="a", wiser_id="b", context="life")
    assert e.confidence == 0.0
    assert e.created_at > 0


# -- Upgrade --

def test_upgrade_round_trip():
    u = Upgrade(
        source_id="a",
        wiser_id="b",
        clarification="Was really about safety.",
        story="I realized I was hiding behind rules.",
        mapping=[{"old_policy": "X", "new_understanding": "Y"}],
        likelihood="A",
    )
    d = u.to_dict()
    u2 = Upgrade.from_dict(d)
    assert u2.source_id == "a"
    assert u2.clarification == "Was really about safety."
    assert u2.mapping == [{"old_policy": "X", "new_understanding": "Y"}]
    assert u2.likelihood == "A"


def test_upgrade_from_dict_defaults():
    d = {
        "source_id": "a",
        "wiser_id": "b",
        "clarification": "test",
        "story": "test",
    }
    u = Upgrade.from_dict(d)
    assert u.mapping == []
    assert u.likelihood == "C"


# -- MoralGraph --

def test_moral_graph_empty():
    g = MoralGraph()
    assert g.values == []
    assert g.edges == []
    assert g.upgrades == []
    assert g.pagerank == {}
    assert g.get_value("x") is None
    assert g.top_values(5) == []


def test_moral_graph_round_trip():
    v1 = Value(id="a", title="Alpha", policies=[AttentionPolicy("WAYS of being")])
    v2 = Value(id="b", title="Beta", policies=[AttentionPolicy("SIGNS of growth")])
    e = Edge(source_id="a", wiser_id="b", context="life", confidence=0.9)
    u = Upgrade(
        source_id="a", wiser_id="b",
        clarification="Grew", story="I grew", mapping=[], likelihood="A",
    )
    g = MoralGraph(
        values=[v1, v2], edges=[e], upgrades=[u], pagerank={"a": 0.3, "b": 0.7}
    )

    d = g.to_dict()
    g2 = MoralGraph.from_dict(d)
    assert len(g2.values) == 2
    assert len(g2.edges) == 1
    assert len(g2.upgrades) == 1
    assert g2.pagerank == {"a": 0.3, "b": 0.7}


def test_moral_graph_get_value():
    v = Value(id="abc", title="Test", policies=[])
    g = MoralGraph(values=[v])
    assert g.get_value("abc") is v
    assert g.get_value("xyz") is None


def test_moral_graph_top_values_respects_pagerank():
    v1 = Value(id="a", title="Low", policies=[])
    v2 = Value(id="b", title="High", policies=[])
    g = MoralGraph(values=[v1, v2], pagerank={"a": 0.1, "b": 0.9})
    top = g.top_values(1)
    assert len(top) == 1
    assert top[0].id == "b"


def test_moral_graph_edges_from_to():
    e1 = Edge(source_id="a", wiser_id="b", context="x")
    e2 = Edge(source_id="b", wiser_id="c", context="y")
    g = MoralGraph(edges=[e1, e2])
    assert len(g.get_edges_from("a")) == 1
    assert len(g.get_edges_from("b")) == 1
    assert len(g.get_edges_to("b")) == 1
    assert len(g.get_edges_to("c")) == 1
    assert len(g.get_edges_from("c")) == 0
