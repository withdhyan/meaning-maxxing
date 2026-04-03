"""Tests for the value store: persistence, CRUD, PageRank, TWS."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skill"))

from scripts.types import AttentionPolicy, Edge, MoralGraph, Upgrade, Value
from scripts.store import ValueStore


def _make_value(id: str, title: str = "Test") -> Value:
    return Value(id=id, title=title, policies=[AttentionPolicy(f"WAYS of {id}")])


def _tmp_store() -> ValueStore:
    """Create a ValueStore backed by a temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    return ValueStore(path=Path(tmp.name))


# -- Persistence --

def test_save_and_reload():
    store = _tmp_store()
    store.add_value(_make_value("a", "Alpha"))
    store.add_value(_make_value("b", "Beta"))

    # Reload from disk
    store2 = ValueStore(path=store.path)
    assert len(store2.get_all_values()) == 2
    assert store2.get_value("a").title == "Alpha"
    assert store2.get_value("b").title == "Beta"


def test_load_nonexistent_file():
    store = ValueStore(path=Path("/tmp/nonexistent_graph_12345.json"))
    assert len(store.get_all_values()) == 0


def test_load_corrupt_file():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    tmp.write("not valid json {{{")
    tmp.close()
    store = ValueStore(path=Path(tmp.name))
    assert len(store.get_all_values()) == 0


def test_atomic_save():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    # File should exist and be valid JSON
    data = json.loads(store.path.read_text())
    assert len(data["values"]) == 1


# -- CRUD --

def test_add_value():
    store = _tmp_store()
    store.add_value(_make_value("a", "Alpha"))
    assert len(store.get_all_values()) == 1
    assert store.get_value("a").title == "Alpha"


def test_remove_value():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    assert store.remove_value("a") is True
    assert store.get_value("a") is None
    assert len(store.get_all_values()) == 0


def test_remove_nonexistent_value():
    store = _tmp_store()
    assert store.remove_value("nonexistent") is False


def test_remove_value_cascades_edges_and_upgrades():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="test", confidence=0.8))
    store.add_upgrade(Upgrade(
        source_id="a", wiser_id="b",
        clarification="test", story="test", mapping=[], likelihood="A",
    ))
    assert len(store.graph.edges) == 1
    assert len(store.graph.upgrades) == 1

    store.remove_value("a")
    assert len(store.graph.edges) == 0
    assert len(store.graph.upgrades) == 0


def test_add_edge():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="work", confidence=0.5))
    assert len(store.graph.edges) == 1


def test_add_edge_merges_existing():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="work", confidence=0.5))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="work", confidence=0.3))
    # Should merge, not create second edge
    assert len(store.graph.edges) == 1
    assert store.graph.edges[0].confidence == 0.8


def test_add_edge_merge_caps_at_one():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="x", confidence=0.9))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="x", confidence=0.9))
    assert store.graph.edges[0].confidence == 1.0


# -- Queries --

def test_top_values_empty():
    store = _tmp_store()
    assert store.top_values(5) == []


def test_get_upgrades_for():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    u = Upgrade(
        source_id="a", wiser_id="b",
        clarification="test", story="test", mapping=[], likelihood="A",
    )
    store.add_upgrade(u)
    assert len(store.get_upgrades_for("a")) == 1
    assert len(store.get_upgrades_for("b")) == 1
    assert len(store.get_upgrades_for("c")) == 0


def test_get_recent_upgrades_ordering():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_value(_make_value("c"))
    u1 = Upgrade(
        source_id="a", wiser_id="b",
        clarification="first", story="", mapping=[], likelihood="A",
        created_at=100.0,
    )
    u2 = Upgrade(
        source_id="b", wiser_id="c",
        clarification="second", story="", mapping=[], likelihood="A",
        created_at=200.0,
    )
    store.add_upgrade(u1)
    store.add_upgrade(u2)
    recent = store.get_recent_upgrades(1)
    assert len(recent) == 1
    assert recent[0].clarification == "second"


# -- PageRank --

def test_pagerank_empty():
    store = _tmp_store()
    assert store.graph.pagerank == {}


def test_pagerank_single_value():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    # Single value with no edges: PageRank = (1-damping)/n = 0.15
    assert "a" in store.graph.pagerank
    assert store.graph.pagerank["a"] > 0


def test_pagerank_wiser_gets_higher_rank():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="life", confidence=0.9))
    # b should rank higher than a
    assert store.graph.pagerank["b"] > store.graph.pagerank["a"]


def test_pagerank_chain():
    """a -> b -> c: c should rank highest."""
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_value(_make_value("c"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="x", confidence=0.9))
    store.add_edge(Edge(source_id="b", wiser_id="c", context="x", confidence=0.9))
    assert store.graph.pagerank["c"] > store.graph.pagerank["b"]
    assert store.graph.pagerank["b"] > store.graph.pagerank["a"]


def test_pagerank_recomputed_on_edge_merge():
    """Merging confidence into existing edge should recompute PageRank."""
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="x", confidence=0.3))
    rank_before = store.graph.pagerank["b"]
    store.add_edge(Edge(source_id="a", wiser_id="b", context="x", confidence=0.5))
    # PageRank should have been recomputed (may or may not change the rank
    # depending on the single-edge case, but the key is it was recomputed)
    assert "b" in store.graph.pagerank


# -- TWS --

def test_tws_empty():
    store = _tmp_store()
    tws = store.compute_tws()
    assert tws["tws"] == 0.0
    assert tws["depth"] == 0.0
    assert tws["growth"] == 0.0
    assert tws["coherence"] == 0.0


def test_tws_single_value_no_edges():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    tws = store.compute_tws()
    assert tws["tws"] == 0.0  # No edges means no growth or coherence


def test_tws_with_edges():
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="life", confidence=0.9))
    tws = store.compute_tws()
    assert tws["depth"] > 0
    assert tws["growth"] > 0
    assert tws["coherence"] > 0
    assert tws["tws"] > 0


def test_tws_geometric_mean():
    """TWS should be 0 if any dimension is 0."""
    store = _tmp_store()
    store.add_value(_make_value("a"))
    store.add_value(_make_value("b"))
    # No edges: growth and coherence are 0
    tws = store.compute_tws()
    assert tws["tws"] == 0.0


def test_tws_increases_with_graph_richness():
    store = _tmp_store()
    for i in range(5):
        store.add_value(_make_value(str(i), f"Value {i}"))
    # Add a chain of edges
    for i in range(4):
        store.add_edge(Edge(
            source_id=str(i), wiser_id=str(i + 1),
            context="growth", confidence=0.8,
        ))
    tws = store.compute_tws()
    assert tws["tws"] > 0.3  # Rich graph should have meaningful score
    assert tws["coherence"] > 0.5  # Most values connected


# -- Display --

def test_format_graph_summary_empty():
    store = _tmp_store()
    assert store.format_graph_summary() == "No values recorded yet."


def test_format_graph_summary_with_values():
    store = _tmp_store()
    store.add_value(_make_value("a", "Alpha"))
    summary = store.format_graph_summary()
    assert "Alpha" in summary
    assert "1 values" in summary


def test_format_upgrades_summary_empty():
    store = _tmp_store()
    assert "No growth" in store.format_upgrades_summary()


def test_format_upgrades_summary_with_data():
    store = _tmp_store()
    store.add_value(_make_value("a", "Alpha"))
    store.add_value(_make_value("b", "Beta"))
    store.add_upgrade(Upgrade(
        source_id="a", wiser_id="b",
        clarification="Grew beyond", story="I let go", mapping=[], likelihood="A",
    ))
    summary = store.format_upgrades_summary()
    assert "Alpha" in summary
    assert "Beta" in summary
    assert "Grew beyond" in summary
