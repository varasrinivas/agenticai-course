"""
Episodic Memory — past interaction recall with similarity search.
(Solution — fully implemented)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re


@dataclass
class Episode:
    query: str
    response: str
    agent_used: str
    tool_calls: List[str]
    task_type: str
    success: bool
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EpisodicMemory:
    """Long-term memory of past query/response pairs."""

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

    def __init__(self, max_episodes: int = 100):
        self._episodes: List[Episode] = []
        self._max_episodes = max_episodes

    def store_episode(
        self, query: str, response: str, agent_used: str,
        tool_calls: List[str], task_type: str, success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        episode = Episode(
            query=query, response=response, agent_used=agent_used,
            tool_calls=tool_calls, task_type=task_type, success=success,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._episodes.append(episode)
        if len(self._episodes) > self._max_episodes:
            self._episodes.pop(0)

    def _extract_keywords(self, text: str) -> set:
        words = re.findall(r'\b\w+\b', text.lower())
        return {w for w in words if w not in self.STOPWORDS and len(w) >= 3}

    def _similarity_score(self, keywords_a: set, keywords_b: set) -> float:
        union = keywords_a | keywords_b
        if not union:
            return 0.0
        return len(keywords_a & keywords_b) / len(union)

    def recall(
        self, query: str, k: int = 3,
        task_type: Optional[str] = None, min_similarity: float = 0.1,
    ) -> List[Tuple[Episode, float]]:
        query_keywords = self._extract_keywords(query)
        scored = []
        for ep in self._episodes:
            if task_type and ep.task_type != task_type:
                continue
            ep_keywords = self._extract_keywords(ep.query)
            score = self._similarity_score(query_keywords, ep_keywords)
            if score >= min_similarity:
                scored.append((ep, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def get_success_rate(self, task_type: str) -> float:
        matching = [ep for ep in self._episodes if ep.task_type == task_type]
        if not matching:
            return 0.0
        return sum(1 for ep in matching if ep.success) / len(matching)

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for ep in self._episodes:
            types[ep.task_type] = types.get(ep.task_type, 0) + 1
        success_rates = {}
        for t in types:
            success_rates[t] = self.get_success_rate(t)
        return {
            "total_episodes": len(self._episodes),
            "episodes_by_type": types,
            "success_rate_by_type": success_rates,
            "oldest_episode_timestamp": self._episodes[0].timestamp if self._episodes else None,
            "newest_episode_timestamp": self._episodes[-1].timestamp if self._episodes else None,
        }

    @property
    def episodes(self) -> List[Episode]:
        return self._episodes

    def __len__(self) -> int:
        return len(self._episodes)
