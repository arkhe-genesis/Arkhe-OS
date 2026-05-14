from collections import defaultdict
import math
from typing import List, Dict, Tuple

class Substrato8SearchEngine:
    def __init__(self):
        self.documents: Dict[int, str] = {}
        # word -> set of doc_ids
        self.inverted_index: Dict[str, set] = defaultdict(set)
        self.doc_lengths: Dict[int, int] = {}
        # doc_id -> word -> term frequency
        self.term_freqs: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def _tokenize(self, text: str) -> List[str]:
        # Very basic tokenization
        return text.lower().replace(".", "").replace(",", "").split()

    def index_document(self, doc_id: int, text: str):
        self.documents[doc_id] = text
        tokens = self._tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)

        for token in tokens:
            self.inverted_index[token].add(doc_id)
            self.term_freqs[doc_id][token] += 1

    def search(self, query: str) -> List[Tuple[int, float]]:
        """Returns doc_ids and scores sorted by relevance (TF-IDF)."""
        tokens = self._tokenize(query)
        scores: Dict[int, float] = defaultdict(float)
        total_docs = len(self.documents)

        for token in tokens:
            if token not in self.inverted_index:
                continue

            doc_freq = len(self.inverted_index[token])
            idf = math.log(total_docs / (1 + doc_freq))

            for doc_id in self.inverted_index[token]:
                tf = self.term_freqs[doc_id][token] / self.doc_lengths[doc_id]
                scores[doc_id] += tf * idf

        # Sort by score descending
        sorted_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_results

if __name__ == "__main__":
    search_engine = Substrato8SearchEngine()

    search_engine.index_document(1, "The quick brown fox jumps over the lazy dog.")
    search_engine.index_document(2, "A lazy dog sleeps all day.")
    search_engine.index_document(3, "The fox is quick and smart.")

    query = "quick fox"
    results = search_engine.search(query)

    print(f"Results for '{query}':")
    for doc_id, score in results:
        print(f"Doc {doc_id} (score {score:.4f}): {search_engine.documents[doc_id]}")
