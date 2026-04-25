"""
Episodic Memory — past interaction recall with similarity search.

Stores past query/response pairs and allows retrieval of similar past
interactions. This helps the agent learn from experience: "I've seen a
query like this before, and here's how I handled it."

Uses simple keyword-based similarity (no vector DB required for this lab).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re


@dataclass
class Episode:
    """A single past interaction stored in episodic memory."""
    query: str
    response: str
    agent_used: str
    tool_calls: List[str]
    task_type: str           # filing_lookup, entity_resolution, risk_assessment
    success: bool
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EpisodicMemory:
    """
    Long-term memory of past query/response pairs.

    Think of this like a case file archive — when a new case comes in,
    you can search past cases for similar situations and see how they
    were handled. This improves consistency and helps avoid repeating mistakes.
    """

    def __init__(self, max_episodes: int = 100):
        self._episodes: List[Episode] = []
        self._max_episodes = max_episodes

    # ------------------------------------------------------------------
    # TODO 1: Implement store_episode()
    # Create an Episode from the given parameters and append it.
    # If we exceed max_episodes, remove the oldest episode (FIFO).
    # ------------------------------------------------------------------
    def store_episode(
        self,
        query: str,
        response: str,
        agent_used: str,
        tool_calls: List[str],
        task_type: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a completed interaction as an episode."""
        # TODO: Create an Episode with timestamp = datetime.utcnow().isoformat()
        # TODO: Append to self._episodes
        # TODO: If len exceeds max_episodes, pop the oldest (index 0)
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement _extract_keywords()
    # Extract meaningful keywords from a query string.
    # Steps:
    #   1. Lowercase the text
    #   2. Split into words (use re.findall(r'\b\w+\b', text))
    #   3. Remove stopwords (STOPWORDS set provided below)
    #   4. Remove words shorter than 3 characters
    #   5. Return as a set of unique keywords
    # ------------------------------------------------------------------
    STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "must", "ought",
        "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
        "neither", "each", "every", "all", "any", "few", "more", "most",
        "other", "some", "such", "no", "only", "same", "than", "too", "very",
        "for", "of", "in", "on", "at", "to", "from", "by", "with", "about",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "what",
        "which", "who", "whom", "this", "that", "these", "those", "its",
        "their", "his", "her", "our", "your", "find", "show", "get", "tell",
        "give", "look", "many", "much",
    }

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        # TODO: Implement keyword extraction as described above
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement _similarity_score()
    # Compute Jaccard similarity between two sets of keywords:
    #   intersection / union (return 0.0 if union is empty)
    # ------------------------------------------------------------------
    def _similarity_score(self, keywords_a: set, keywords_b: set) -> float:
        """Compute Jaccard similarity between two keyword sets."""
        # TODO: Compute |A ∩ B| / |A ∪ B|
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement recall()
    # Find the top-k most similar past episodes to the given query.
    # Steps:
    #   1. Extract keywords from the query
    #   2. For each episode, extract keywords from episode.query
    #   3. Compute similarity score
    #   4. Optionally filter by task_type if provided
    #   5. Sort by similarity descending
    #   6. Return top-k as list of (episode, score) tuples
    #   7. Only return episodes with score > min_similarity (default 0.1)
    # ------------------------------------------------------------------
    def recall(
        self,
        query: str,
        k: int = 3,
        task_type: Optional[str] = None,
        min_similarity: float = 0.1,
    ) -> List[Tuple[Episode, float]]:
        """Recall similar past episodes."""
        # TODO: Implement similarity-based retrieval
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement get_success_rate()
    # Return the success rate for a given task_type.
    # Filter episodes by task_type, compute successes / total.
    # Return 0.0 if no episodes match.
    # ------------------------------------------------------------------
    def get_success_rate(self, task_type: str) -> float:
        """Get the success rate for a specific task type."""
        # TODO: Filter and compute success rate
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement get_stats()
    # Return a dict with:
    #   - total_episodes
    #   - episodes_by_type: {task_type: count}
    #   - success_rate_by_type: {task_type: rate}
    #   - oldest_episode_timestamp (or None)
    #   - newest_episode_timestamp (or None)
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about stored episodes."""
        # TODO: Compute and return stats
        pass

    @property
    def episodes(self) -> List[Episode]:
        """Return all episodes."""
        return self._episodes

    def __len__(self) -> int:
        return len(self._episodes)
