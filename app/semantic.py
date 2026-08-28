"""semantic.py — Local embedding-backed fallback fact classifier.

Closes the recall gap of the regex cue lists: hand-written patterns cannot
cover every user domain (researchers, casual chatter, medicine, law...).
Anything the regex tier cannot categorize is scored here against short
canonical descriptions of each fact category using the SAME local embedding
model cognee already uses (fastembed / all-MiniLM-L6-v2 by default).

Properties:
    - zero API cost, fully offline, deterministic per model version
    - lazy: the model loads on first classification, never at import time
    - fail-open: any error here simply means "no extra fact", never a crash
    - tunable: CLIMEM_SEMANTIC=0 disables the tier entirely;
      CLIMEM_SEMANTIC_THRESHOLD moves the precision/recall trade-off
"""

import os

# Read config eagerly (cheap), load the model lazily (expensive).
ENABLED = os.getenv("CLIMEM_SEMANTIC", "1").strip().lower() not in {
    "0", "false", "no", "off",
}
try:
    # Margin by which the best fact-category must beat the small-talk
    # reference (cosine units). Calibrated on MiniLM-class models:
    # real-world facts measured >= ~+0.06, small talk <= ~+0.07 and often
    # negative. Default 0.10 biases toward precision — a missed fact is
    # cheaper than junk memories injected into every future request.
    THRESHOLD = float(os.getenv("CLIMEM_SEMANTIC_THRESHOLD", "0.10"))
except ValueError:
    THRESHOLD = 0.10

MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

# Reference embedding: what ordinary small talk looks like. A sentence only
# becomes a fact if some category matches it CLEARLY better than this does.
CHITCHAT_DESCRIPTION = (
    "Just a greeting, thanks, a short remark, or a question about time or "
    "weather; ordinary chat with nothing worth remembering."
)

# Canonical descriptions per filter.py fact category. Written as typical
# sentences so the embedding space lines up with how real facts read.
CATEGORY_DESCRIPTIONS = {
    "decision": (
        "We decided to adopt one option over another; a choice was made "
        "about tools, designs, names, or direction."
    ),
    "convention": (
        "Always follow this rule, standard, naming style, or preference "
        "going forward; never do it the other way."
    ),
    "goal": (
        "My goal, plan, ambition, or intention; I want to achieve, study, "
        "learn, build, or improve something."
    ),
    "open_thread": (
        "Unfinished work: a todo, bug, blocker, pending question, or "
        "something still missing and left to do."
    ),
    "identity": (
        "What something is called: a project name, product name, title, "
        "or who someone is."
    ),
    "architecture": (
        "How the system is designed and structured: components, layers, "
        "data flow, pipelines, and workflows."
    ),
    "api": (
        "An interface boundary: endpoints, routes, requests, responses, "
        "payloads, headers, and status codes."
    ),
    "database": (
        "Data storage concerns: databases, tables, schemas, migrations, "
        "indexes, vectors, and persistence."
    ),
    "implementation": (
        "Where things live in code: files, modules, classes, functions, "
        "packages, and how they are implemented."
    ),
    "state": (
        "The current condition or status of something: what exists now, "
        "where it lives, what supports or contains what, findings and "
        "results observed so far."
    ),
}


class _Engine:
    """Lazy singleton around fastembed + cached category vectors."""

    def __init__(self) -> None:
        self._model = None
        self._cat_matrix = None  # (n_categories, dim) normalized numpy

    def _ensure(self):
        if self._model is not None:
            return
        print(f"[semantic] loading embedding model '{MODEL_NAME}' "
              f"(first use downloads ~90MB)...")
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=MODEL_NAME)
        cats = list(CATEGORY_DESCRIPTIONS.keys())
        descs = [CATEGORY_DESCRIPTIONS[c] for c in cats]
        descs.append(CHITCHAT_DESCRIPTION)
        import numpy as np

        matrix = np.vstack([next(self._model.embed([d])) for d in descs])
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        self._cat_matrix = (cats, matrix[:-1], matrix[-1])
        print("[semantic] ready")

    def rank(self, sentence: str):
        """Return [(category, margin)] sorted best-first for one sentence.

        Each entry's score is the sentence's cosine to that category
        description MINUS its cosine to the small-talk reference. Only the
        sign and relative size matter: a positive margin means the
        sentence is more fact-like than small-talk-like for that category,
        and THRESHOLD decides how clearly it must win.
        """
        self._ensure()
        import numpy as np

        q = next(self._model.embed([sentence]))
        norm = float(np.linalg.norm(q))
        if norm == 0.0:
            return []
        q = q / norm
        cats, matrix, chitchat_vec = self._cat_matrix
        scores = (matrix @ q) - float(chitchat_vec @ q)
        ranked = sorted(zip(cats, (float(s) for s in scores)),
                        key=lambda pair: pair[1], reverse=True)
        return ranked


_engine = _Engine()


def classify(sentence: str):
    """
    Classify a sentence that the regex tier could not categorize.

    Returns (category, score) when the best match clears THRESHOLD,
    otherwise None. Never raises — failures degrade to None.
    """
    if not ENABLED or not sentence or len(sentence.split()) < 6:
        return None
    try:
        ranked = _engine.rank(sentence)
    except Exception as exc:  # fail-open: heuristic-only extraction continues
        print(f"[WARN] semantic tier unavailable ({exc!r}); "
              f"continuing with regex cues only")
        return None

    if not ranked:
        return None
    best_cat, best_score = ranked[0]
    if best_score >= THRESHOLD:
        return best_cat, best_score
    return None


def warmup() -> bool:
    """Pre-load the model; used by tests/verification, safe to skip."""
    try:
        _engine._ensure()
        return True
    except Exception:
        return False
