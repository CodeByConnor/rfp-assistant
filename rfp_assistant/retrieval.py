"""BM25 retrieval over the knowledge base.

Deliberately not embeddings. This corpus is 11 documents of dense technical
vocabulary, and the requirements share that vocabulary almost verbatim --
"SAML", "HIPAA", "Kafka", "RPO" appear on both sides. Lexical matching is a
strong baseline here, costs nothing, needs no model download, and runs in
milliseconds.

The gold answer key records the document each labeled requirement should cite,
so retrieval quality is measurable (`python -m rfp_assistant eval-retrieval`).
Add embeddings when that measurement says lexical matching is not enough, not
before.

Two properties matter more than raw ranking quality:

1. Access filtering happens before scoring, not after.
2. The score is reported, so the caller can refuse to answer on weak evidence.
   That threshold is what turns "the model found nothing relevant" into an
   honest `Needs Input` rather than a confident guess.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .knowledge import INTERNAL, PUBLIC, Chunk

K1 = 1.5
B = 0.75

TOKEN_RE = re.compile(r"[a-z0-9]+")

# Words carrying no discriminating power in an RFP corpus, where nearly every
# sentence is "describe your approach to ...".
STOPWORDS = frozenset("""
a an and are as at be been by can confirm describe do does for from has have
how in is it its may must of on or our provide should state such support the
their there these this those to what when where whether which will with within
you your platform vendor requirement please any all
""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class BM25Retriever:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self._tokens = [tokenize(f"{c.heading} {c.text}") for c in chunks]
        self._lengths = [len(t) for t in self._tokens]
        self._avg_len = sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        self._freqs = [Counter(t) for t in self._tokens]

        df = Counter()
        for tokens in self._tokens:
            for term in set(tokens):
                df[term] += 1
        n = len(chunks)
        self._idf = {
            term: math.log(1 + (n - count + 0.5) / (count + 0.5))
            for term, count in df.items()
        }

    def _score(self, index: int, query_terms: list[str]) -> float:
        freqs = self._freqs[index]
        length = self._lengths[index]
        score = 0.0
        for term in query_terms:
            tf = freqs.get(term, 0)
            if not tf:
                continue
            idf = self._idf.get(term, 0.0)
            denom = tf + K1 * (1 - B + B * length / self._avg_len) if self._avg_len else tf
            score += idf * (tf * (K1 + 1)) / denom
        return score

    def search(self, query: str, *, role: str = PUBLIC, top_k: int = 4) -> list[Hit]:
        """Rank chunks for a query, restricted to what `role` may see.

        A `public` role sees only public chunks. An `internal` role sees
        everything. Chunks the role cannot see are excluded from the candidate
        set entirely -- they are never scored, so they cannot surface through a
        ranking bug or a threshold change.
        """
        query_terms = tokenize(query)
        if not query_terms:
            return []

        allowed = (
            range(len(self.chunks))
            if role == INTERNAL
            else [i for i, c in enumerate(self.chunks) if c.access == PUBLIC]
        )

        scored = [(self._score(i, query_terms), i) for i in allowed]
        scored = [(s, i) for s, i in scored if s > 0]
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [Hit(chunk=self.chunks[i], score=s) for s, i in scored[:top_k]]

    def documents_for(self, query: str, *, role: str = PUBLIC, top_k: int = 4) -> list[str]:
        seen: list[str] = []
        for hit in self.search(query, role=role, top_k=top_k):
            if hit.chunk.doc not in seen:
                seen.append(hit.chunk.doc)
        return seen

    def best_passage(self, query: str, chunks: list[Chunk]) -> str:
        """The single passage across `chunks` that best matches `query`.

        Scored by the summed IDF of the query terms a passage shares, with ties
        going to the higher-ranked chunk. Returns "" if nothing overlaps.
        """
        terms = set(tokenize(query))
        best, best_score = "", 0.0
        for chunk in chunks:
            for passage in split_passages(chunk.text):
                score = sum(self._idf.get(t, 0.0) for t in terms & set(tokenize(passage)))
                if score > best_score:
                    best, best_score = passage, score
        return best


BULLET_RE = re.compile(r"^\s*(?:[-*]|\|)\s")


def split_passages(text: str) -> list[str]:
    """Split chunk text at bullet and table-row boundaries.

    Paragraphs are deliberately kept whole. Splitting on blank lines as well
    separated a question in the past-answers library from the answer beneath
    it saying "route to Legal", and that escalation went unseen.
    """
    passages: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if BULLET_RE.match(line) and any(part.strip() for part in current):
            passages.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        passages.append("\n".join(current))
    return [p for p in passages if p.strip()]
