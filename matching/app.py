"""
Values matching API.

POST /emit       — agent publishes user's values (with consent)
GET  /match/{id} — find most aligned users
GET  /values     — list all canonical values
GET  /user/{id}  — get a user's canonical values
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .dedup import find_duplicate
from .matcher import find_matches
from .store import Store

app = FastAPI(
    title="Values Matching Engine",
    description="Match humans by their sources of meaning.",
    version="0.1.0",
)

# Store initialized on startup, configurable via env or direct init
_store: Optional[Store] = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def set_store(store: Store) -> None:
    global _store
    _store = store


# -- Models --

class ValuePayload(BaseModel):
    title: str
    policies: list[str]


class EmitRequest(BaseModel):
    user_id: str
    values: list[ValuePayload]


class EmitResult(BaseModel):
    user_id: str
    accepted: int
    deduplicated: int


class MatchResult(BaseModel):
    user_id: str
    shared: list[str]
    unique_self: list[str]
    unique_other: list[str]
    alignment: float
    resonance: float


class CanonicalValue(BaseModel):
    id: str
    title: str
    policies: list[str]


# -- Endpoints --

@app.post("/emit", response_model=EmitResult)
def emit_values(req: EmitRequest) -> EmitResult:
    """
    Receive values from a Hermes agent.

    For each value:
    1. Check if it duplicates an existing canonical value
    2. If yes, link user to that canonical
    3. If no, create new canonical and link
    """
    store = get_store()
    canonicals = store.all_canonicals()
    accepted = 0
    deduplicated = 0

    for v in req.values:
        dup_id = find_duplicate(v.title, v.policies, canonicals)

        if dup_id:
            store.link_user(req.user_id, dup_id, v.title)
            deduplicated += 1
        else:
            new_id = store.add_canonical(v.title, v.policies)
            store.link_user(req.user_id, new_id, v.title)
            # Add to running list so subsequent values in this batch dedup
            canonicals.append({
                "id": new_id,
                "title": v.title,
                "policies": v.policies,
            })
            accepted += 1

    return EmitResult(
        user_id=req.user_id,
        accepted=accepted,
        deduplicated=deduplicated,
    )


@app.get("/match/{user_id}", response_model=list[MatchResult])
def match_user(user_id: str, top_n: int = 10) -> list[MatchResult]:
    """Find the most aligned users."""
    store = get_store()
    if not store.user_values(user_id):
        raise HTTPException(404, f"No values found for user {user_id}")
    results = find_matches(user_id, store, top_n=top_n)
    return [MatchResult(**r) for r in results]


@app.get("/values", response_model=list[CanonicalValue])
def list_values() -> list[CanonicalValue]:
    """List all canonical values in the graph."""
    store = get_store()
    return [CanonicalValue(**v) for v in store.all_canonicals()]


@app.get("/user/{user_id}", response_model=list[CanonicalValue])
def user_values(user_id: str) -> list[CanonicalValue]:
    """Get a user's canonical values."""
    store = get_store()
    values = store.user_values(user_id)
    if not values:
        raise HTTPException(404, f"No values found for user {user_id}")
    return [CanonicalValue(**v) for v in values]
