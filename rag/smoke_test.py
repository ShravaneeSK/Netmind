"""Smoke test: can ChromaDB embed and search text on this PC?"""
import chromadb

client = chromadb.EphemeralClient()
col = client.create_collection("smoke")
col.add(
    ids=["dns", "wifi", "dhcp"],
    documents=[
        "If DNS lookups fail but pinging an IP address works, the DNS server is the problem.",
        "A weak Wi-Fi signal causes high latency, jitter and packet loss.",
        "A DHCP server hands out IP addresses to devices that join the network.",
    ],
)
res = col.query(query_texts=["name resolution keeps failing"], n_results=3)
for doc, dist in zip(res["documents"][0], res["distances"][0]):
    print(round(dist, 3), "|", doc)
