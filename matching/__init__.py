"""Social matching engine: align humans by their sources of meaning."""

from .store import Store
from .dedup import find_duplicate, policy_similarity
from .matcher import find_matches
