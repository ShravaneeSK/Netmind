"""Search the NetMind knowledge base (built by rag/ingest.py)."""
from functools import lru_cache
from pathlib import Path

import chromadb

STORE = Path(__file__).resolve().parent / "store"
COLLECTION = "netmind_kb"


class IndexMissing(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _collection():
    if not STORE.exists():
        raise IndexMissing("Knowledge-base index not found. Run: python rag/ingest.py")
    client = chromadb.PersistentClient(path=str(STORE))
    try:
        return client.get_collection(COLLECTION)
    except Exception as e:
        raise IndexMissing("Knowledge-base index not found. Run: python rag/ingest.py") from e


def search(query, n=3, fault=None, exclude_glossary=False):
    """Return the n best-matching chunks as dicts: fault, section, source, distance, text.

    fault: only search that fault class's notes (for example "dns_failure").
    exclude_glossary: leave the telemetry glossary out of the results.
    """
    where = None
    if fault:
        where = {"fault": fault}
    elif exclude_glossary:
        where = {"fault": {"$ne": "glossary"}}

    res = _collection().query(query_texts=[query], n_results=n, where=where)
    return [
        {
            "fault": meta["fault"],
            "section": meta["section"],
            "source": meta["source"],
            "distance": round(dist, 3),
            "text": doc,
        }
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


SECTION_ORDER = ["signature", "likely causes", "how to check", "how to fix"]


def notes_for(fault):
    """Return the stored sections of one fault class in reading order (no similarity search)."""
    res = _collection().get(where={"fault": fault})
    items = list(zip(res["metadatas"], res["documents"]))
    items.sort(
        key=lambda m: SECTION_ORDER.index(m[0]["section"]) if m[0]["section"] in SECTION_ORDER else 99
    )
    return [{"section": m["section"], "text": d} for m, d in items]
