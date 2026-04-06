"""Tests for the matching engine: store, dedup, matcher, API."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from matching.store import Store
from matching.dedup import policy_similarity, find_duplicate, _policy_words
from matching.matcher import find_matches, _cross_resonance
from matching.app import app, set_store


# -- Fixtures --

@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture
def client(store):
    set_store(store)
    return TestClient(app)


# -- Helper values --

HONESTY_POLICIES = [
    "MOMENTS where telling a difficult truth opens a new possibility",
    "SIGNS that someone is ready to hear what they need to hear",
    "WAYS of speaking that make hard truths land as gifts",
]

STEWARDSHIP_POLICIES = [
    "SIGNS that a system needs quiet tending rather than dramatic intervention",
    "MOMENTS where careful attention prevents larger problems",
    "WAYS of maintaining things so others barely notice the effort",
]

# Similar to honesty — should deduplicate
CANDOR_POLICIES = [
    "MOMENTS where speaking a difficult truth opens new possibility",
    "SIGNS someone is ready to hear hard truths",
    "WAYS of delivering truth that lands as a gift not a wound",
]

COURAGE_POLICIES = [
    "MOMENTS where stepping into fear reveals new ground",
    "CHOICES to act despite uncertainty when something matters",
    "SIGNS that discomfort signals growth rather than danger",
]


# ============================================================
# Store tests
# ============================================================

class TestStore:
    def test_add_and_get_canonical(self, store):
        vid = store.add_canonical("Honesty", HONESTY_POLICIES)
        v = store.get_canonical(vid)
        assert v["title"] == "Honesty"
        assert v["policies"] == HONESTY_POLICIES

    def test_all_canonicals(self, store):
        store.add_canonical("A", ["p1"])
        store.add_canonical("B", ["p2"])
        assert len(store.all_canonicals()) == 2

    def test_link_user(self, store):
        vid = store.add_canonical("Honesty", HONESTY_POLICIES)
        store.link_user("alice", vid, "Generative Honesty")
        vals = store.user_values("alice")
        assert len(vals) == 1
        assert vals[0]["id"] == vid

    def test_link_idempotent(self, store):
        vid = store.add_canonical("Honesty", HONESTY_POLICIES)
        store.link_user("alice", vid, "Honesty")
        store.link_user("alice", vid, "Honesty")
        assert len(store.user_values("alice")) == 1

    def test_users_for_value(self, store):
        vid = store.add_canonical("Honesty", HONESTY_POLICIES)
        store.link_user("alice", vid, "Honesty")
        store.link_user("bob", vid, "Honesty")
        users = store.users_for_value(vid)
        assert set(users) == {"alice", "bob"}

    def test_all_user_ids(self, store):
        v1 = store.add_canonical("A", ["p1"])
        v2 = store.add_canonical("B", ["p2"])
        store.link_user("alice", v1, "A")
        store.link_user("bob", v2, "B")
        assert set(store.all_user_ids()) == {"alice", "bob"}

    def test_get_nonexistent(self, store):
        assert store.get_canonical("nope") is None

    def test_user_values_empty(self, store):
        assert store.user_values("nobody") == []


# ============================================================
# Dedup tests
# ============================================================

class TestDedup:
    def test_identical_policies(self):
        assert policy_similarity(HONESTY_POLICIES, HONESTY_POLICIES) == 1.0

    def test_completely_different(self):
        sim = policy_similarity(HONESTY_POLICIES, STEWARDSHIP_POLICIES)
        assert sim < 0.3

    def test_similar_values_high_similarity(self):
        sim = policy_similarity(HONESTY_POLICIES, CANDOR_POLICIES)
        assert sim > 0.5

    def test_empty_policies(self):
        assert policy_similarity([], HONESTY_POLICIES) == 0.0
        assert policy_similarity([], []) == 0.0

    def test_find_duplicate_found(self):
        existing = [
            {"id": "abc", "title": "Honesty", "policies": HONESTY_POLICIES},
        ]
        dup = find_duplicate("Candor", CANDOR_POLICIES, existing)
        assert dup == "abc"

    def test_find_duplicate_not_found(self):
        existing = [
            {"id": "abc", "title": "Honesty", "policies": HONESTY_POLICIES},
        ]
        dup = find_duplicate("Stewardship", STEWARDSHIP_POLICIES, existing)
        assert dup is None

    def test_policy_words_strips_caps_prefix(self):
        words = _policy_words(["MOMENTS where truth opens possibility"])
        assert "moments" not in words
        assert "truth" in words
        assert "possibility" in words

    def test_policy_words_removes_stopwords(self):
        words = _policy_words(["SIGNS that a person is ready"])
        assert "that" not in words
        assert "person" in words
        assert "ready" in words


# ============================================================
# Matcher tests
# ============================================================

class TestMatcher:
    def _setup_users(self, store):
        """Create 3 users with overlapping values."""
        h = store.add_canonical("Honesty", HONESTY_POLICIES)
        s = store.add_canonical("Stewardship", STEWARDSHIP_POLICIES)
        c = store.add_canonical("Courage", COURAGE_POLICIES)

        store.link_user("alice", h, "Honesty")
        store.link_user("alice", s, "Stewardship")

        store.link_user("bob", h, "Honesty")
        store.link_user("bob", c, "Courage")

        store.link_user("carol", s, "Stewardship")
        store.link_user("carol", c, "Courage")

        return h, s, c

    def test_find_matches(self, store):
        self._setup_users(store)
        matches = find_matches("alice", store)
        assert len(matches) == 2
        # Both bob and carol share 1 value with alice
        user_ids = {m["user_id"] for m in matches}
        assert user_ids == {"bob", "carol"}

    def test_match_shared_values(self, store):
        self._setup_users(store)
        matches = find_matches("alice", store)
        by_user = {m["user_id"]: m for m in matches}
        assert "Honesty" in by_user["bob"]["shared"]
        assert "Stewardship" in by_user["carol"]["shared"]

    def test_match_unique_values(self, store):
        self._setup_users(store)
        matches = find_matches("alice", store)
        by_user = {m["user_id"]: m for m in matches}
        assert "Stewardship" in by_user["bob"]["unique_self"]
        assert "Courage" in by_user["bob"]["unique_other"]

    def test_alignment_score(self, store):
        self._setup_users(store)
        matches = find_matches("alice", store)
        for m in matches:
            # alice shares 1/3 values with each (3 total unique values)
            assert 0.0 < m["alignment"] <= 1.0

    def test_no_values_returns_empty(self, store):
        assert find_matches("nobody", store) == []

    def test_no_other_users_returns_empty(self, store):
        v = store.add_canonical("Solo", ["MOMENTS of solitude"])
        store.link_user("alone", v, "Solo")
        assert find_matches("alone", store) == []

    def test_top_n_limit(self, store):
        h = store.add_canonical("Honesty", HONESTY_POLICIES)
        store.link_user("alice", h, "Honesty")
        for i in range(20):
            store.link_user(f"user_{i}", h, "Honesty")
        matches = find_matches("alice", store, top_n=5)
        assert len(matches) == 5

    def test_cross_resonance_empty(self):
        assert _cross_resonance([], []) == 0.0

    def test_cross_resonance_symmetric(self):
        a = [{"policies": HONESTY_POLICIES}]
        b = [{"policies": STEWARDSHIP_POLICIES}]
        assert _cross_resonance(a, b) == _cross_resonance(b, a)


# ============================================================
# API tests
# ============================================================

class TestAPI:
    def test_emit_new_values(self, client):
        resp = client.post("/emit", json={
            "user_id": "alice",
            "values": [
                {"title": "Honesty", "policies": HONESTY_POLICIES},
                {"title": "Stewardship", "policies": STEWARDSHIP_POLICIES},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["accepted"] == 2
        assert data["deduplicated"] == 0

    def test_emit_deduplicates(self, client):
        # First emit: creates canonicals
        client.post("/emit", json={
            "user_id": "alice",
            "values": [{"title": "Honesty", "policies": HONESTY_POLICIES}],
        })
        # Second emit: similar value should deduplicate
        resp = client.post("/emit", json={
            "user_id": "bob",
            "values": [{"title": "Candor", "policies": CANDOR_POLICIES}],
        })
        data = resp.json()
        assert data["deduplicated"] == 1
        assert data["accepted"] == 0

    def test_emit_within_batch_dedup(self, client):
        resp = client.post("/emit", json={
            "user_id": "alice",
            "values": [
                {"title": "Honesty", "policies": HONESTY_POLICIES},
                {"title": "Candor", "policies": CANDOR_POLICIES},
            ],
        })
        data = resp.json()
        assert data["accepted"] == 1
        assert data["deduplicated"] == 1

    def test_match_endpoint(self, client):
        client.post("/emit", json={
            "user_id": "alice",
            "values": [{"title": "Honesty", "policies": HONESTY_POLICIES}],
        })
        client.post("/emit", json={
            "user_id": "bob",
            "values": [{"title": "Candor", "policies": CANDOR_POLICIES}],
        })
        resp = client.get("/match/alice")
        assert resp.status_code == 200
        matches = resp.json()
        assert len(matches) == 1
        assert matches[0]["user_id"] == "bob"

    def test_match_unknown_user(self, client):
        resp = client.get("/match/nobody")
        assert resp.status_code == 404

    def test_list_values(self, client):
        client.post("/emit", json={
            "user_id": "alice",
            "values": [{"title": "Honesty", "policies": HONESTY_POLICIES}],
        })
        resp = client.get("/values")
        assert resp.status_code == 200
        vals = resp.json()
        assert len(vals) == 1
        assert vals[0]["title"] == "Honesty"

    def test_user_values_endpoint(self, client):
        client.post("/emit", json={
            "user_id": "alice",
            "values": [{"title": "Honesty", "policies": HONESTY_POLICIES}],
        })
        resp = client.get("/user/alice")
        assert resp.status_code == 200
        vals = resp.json()
        assert len(vals) == 1

    def test_user_values_unknown(self, client):
        resp = client.get("/user/nobody")
        assert resp.status_code == 404


# ============================================================
# Emission tests (from skill/scripts/values.py)
# ============================================================

from skill.scripts.values import anonymize_value, prepare_emission, make_value


class TestEmission:
    def test_anonymize_strips_personal(self):
        v = make_value("Test", ["POLICY one"], "personal story", "private context")
        anon = anonymize_value(v)
        assert "title" in anon
        assert "policies" in anon
        assert "description" not in anon
        assert "source_context" not in anon
        assert "id" not in anon

    def test_prepare_emission(self):
        values = [
            make_value("A", ["p1"]),
            make_value("B", ["p2"]),
        ]
        payload = prepare_emission(values, "alice")
        assert payload["user_id"] == "alice"
        assert len(payload["values"]) == 2
        assert "description" not in payload["values"][0]
