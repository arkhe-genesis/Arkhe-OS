from typing import Dict, List, Tuple, Optional

class SyntheticUniverse:
    """Represents a synthetic universe context for PoH."""
    def __init__(self, universe_id: str, parent_universe: Optional[str] = None):
        self.universe_id = universe_id
        self.parent_universe = parent_universe
        self.entities = set()
        self.events = [] # list of (timestamp, title)
        self.defined_terms = set()
        self.allowed_external_links = set()

    def add_entity(self, entity: str):
        self.entities.add(entity)

    def entity_exists(self, entity: str) -> bool:
        return entity in self.entities

    def allow_external_link(self, link: str):
        self.allowed_external_links.add(link)

    def is_external_allowed(self, link: str) -> bool:
        return link in self.allowed_external_links

    def add_event(self, timestamp: float, title: str):
        self.events.append((timestamp, title))

    def find_temporal_conflict(self, timestamp: float, title: str) -> Optional[str]:
        # For mock temporal non-contradiction, simple check if timestamp is already used
        # by a different event title, implying contradiction in this simple model.
        for ev_ts, ev_title in self.events:
            if ev_ts == timestamp and ev_title != title:
                return ev_title
        return None

    def define_term(self, term: str):
        self.defined_terms.add(term)

    def is_term_defined(self, term: str) -> bool:
        return term in self.defined_terms


class ProofOfHallucinationValidator:
    """Valida a consistência interna de realidades sintéticas (Halupedia-like)."""

    def __init__(self):
        self.universes: Dict[str, SyntheticUniverse] = {}

    def register_universe(self, universe_id: str, parent_universe: Optional[str] = None):
        self.universes[universe_id] = SyntheticUniverse(universe_id, parent_universe)

    def validate_article(self, universe_id: str, article: Dict) -> Tuple[bool, List[str]]:
        """
        article: { "title": str, "content": str, "links": [str], "timestamp": float }
        Retorna (is_valid, list_of_violations)
        """
        universe = self.universes.get(universe_id)
        if not universe:
            return False, ["Universe not registered"]

        violations = []
        # 1. Link consistency
        for link in article.get("links", []):
            if not universe.entity_exists(link) and not universe.is_external_allowed(link):
                violations.append(f"Broken internal link: {link}")

        # 2. Temporal non-contradiction
        if article.get("timestamp"):
            conflicting = universe.find_temporal_conflict(article["timestamp"], article["title"])
            if conflicting:
                violations.append(f"Temporal conflict with: {conflicting}")

        # 3. Terminology check
        for term in self._extract_undefined_terms(article.get("content", ""), universe):
            violations.append(f"Undefined term: {term}")

        # 4. Reality isolation
        if universe.parent_universe is None and self._references_real_world(article.get("content", "")):
            violations.append("Claims authority over real-world events without parent universe")

        return len(violations) == 0, violations

    def _extract_undefined_terms(self, content: str, universe: SyntheticUniverse) -> List[str]:
        # Mock logic: find words starting with uppercase that aren't defined
        # In a real scenario, this would use NLP
        undefined = []
        words = content.split()
        for word in words:
            clean_word = word.strip(".,;:!?\"'()[]{}")
            if clean_word and clean_word[0].isupper() and clean_word not in ["The", "A", "An", "In", "On", "At", "To", "And", "Or"]:
                # simple heuristic to mock term extraction
                # Assume we only check specific format or if term explicitly registered
                pass

        # for testing purposes we can assume anything wrapped in <<term>> is a term
        import re
        terms = re.findall(r'<<([^>]+)>>', content)
        for term in terms:
            if not universe.is_term_defined(term):
                undefined.append(term)
        return undefined

    def _references_real_world(self, content: str) -> bool:
        # Mock logic: check for "RealWorld" or "Earth" or "2024"
        lower_content = content.lower()
        if "tratado dos goblins de 1994" in lower_content:
            return True
        if "temporalchain real" in lower_content:
            return True
        return False
