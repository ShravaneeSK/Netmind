"""Build the NetMind knowledge-base index from rag/docs/*.md.

Each '## ' section becomes one chunk (heading included, so it makes sense on its own),
tagged with the fault class and section name. The index is rebuilt from scratch on
every run and stored in rag/store (not committed to Git).
"""
import re
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
STORE = ROOT / "store"
COLLECTION = "netmind_kb"


def fault_from_name(stem):
    return re.sub(r"^\d+_", "", stem)


def split_sections(text):
    sections, current = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current:
        sections.append(current)
    return ["\n".join(s).strip() for s in sections]


def main():
    files = sorted(DOCS.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files in {DOCS}")

    ids, docs, metas = [], [], []
    print(f"{'file':28} sections")
    for f in files:
        sections = split_sections(f.read_text(encoding="utf-8"))
        fault = fault_from_name(f.stem)
        for i, chunk in enumerate(sections):
            heading = chunk.splitlines()[0][3:]
            section = heading.split(": ", 1)[1] if ": " in heading else heading
            ids.append(f"{f.stem}#{i}")
            docs.append(chunk)
            metas.append({"fault": fault, "section": section, "source": f.name})
        print(f"{f.name:28} {len(sections)}")

    client = chromadb.PersistentClient(path=str(STORE))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(COLLECTION)
    col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"\nIndexed {col.count()} chunks into {STORE}")

    query = "name resolution keeps failing but pinging an IP address works"
    res = col.query(query_texts=[query], n_results=3)
    print(f'\nSanity query: "{query}"')
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        print(f"  {dist:.3f}  {meta['fault']} / {meta['section']}")


if __name__ == "__main__":
    main()
