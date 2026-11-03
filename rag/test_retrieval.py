"""Retrieval test: one plain-language question per fault class.

Top-1 = the best chunk belongs to the right fault. Top-3 = the right fault appears
among the three best chunks. Queries describe symptoms and avoid the fault names.
"""
from search import search

QUERIES = {
    "normal": "everything looks healthy and nothing needs to be done",
    "weak_signal": "the signal strength is very low because the node is far from the router",
    "congestion": "the link is saturated by large downloads even though the signal is strong",
    "dns_failure": "names will not resolve but pinging an IP address works",
    "gateway_failure": "the router does not answer pings and nothing can be reached",
    "internet_failure": "the router works locally but the connection to the provider is down",
    "device_overload": "the microcontroller is almost out of memory and its processor is maxed out",
    "intermittent_loss": "packet loss comes and goes in bursts and the readings alternate between good and bad",
    "dhcp_failure": "devices get a 169.254 address and the address pool is exhausted",
}


def main():
    top1 = top3 = 0
    print(f"{'expected':18} {'top-1 result':32} top-3 hit")
    for expected, query in QUERIES.items():
        hits = search(query, n=3, exclude_glossary=True)
        first = hits[0]
        ok1 = first["fault"] == expected
        ok3 = any(h["fault"] == expected for h in hits)
        top1 += ok1
        top3 += ok3
        label = f"{first['fault']}/{first['section']}"
        print(f"{expected:18} {label:32} {'yes' if ok3 else 'NO'}{'' if ok1 else '   (top-1 differs)'}")

    total = len(QUERIES)
    print(f"\nTop-1: {top1}/{total}   Top-3: {top3}/{total}")

    print('\nFiltered search: "how do I fix this", dns_failure notes only')
    for h in search("how do I fix this", n=2, fault="dns_failure"):
        print(f"  {h['distance']:.3f}  {h['fault']} / {h['section']}")


if __name__ == "__main__":
    main()
