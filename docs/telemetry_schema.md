# Telemetry Schema (v2, FROZEN)

NetMind has two data sources. The backend merges them into one record per
5-second window, using the time it receives each one.

## Source 1: ESP32 node (sent every 5 s as JSON)

| Field | Meaning | Unit | Notes |
|---|---|---|---|
| device_id | Node name | string | e.g. "esp32-01" |
| rssi | ESP32's signal to the home router | dBm | -50 good, -80 poor |
| gateway_latency | Time to reach the home router | ms | -1 = timeout |
| internet_latency | Time to reach 8.8.8.8 | ms | -1 = timeout |
| dns_time | Time to resolve a hostname | ms | -1 = failed |
| packet_loss | Share of probes with no reply | % | Last 10 probes |
| jitter | Variation in latency | ms | Std. dev., last 10 probes |
| http_time | Time to fetch a test URL | ms | -1 = failed |
| reconnect_count | Wi-Fi reconnects since boot | count | |
| free_heap | ESP32 free RAM | bytes | |
| cpu_load | Approximate processor load | % | Estimated from loop timing |
| dhcp_clients | Devices connected to the ESP32 AP | count | |
| dhcp_leases_active | Active DHCP leases | count | |
| dhcp_pool_free | Free addresses left in the pool | count | |
| client_rssi_avg | Average signal of connected clients | dBm | -1 if none |

## Source 2: Packet features (Wireshark/tshark on the client PC, per 5 s window)

| Field | Meaning | Unit |
|---|---|---|
| dns_response_ms | DNS query-to-response time on the wire | ms (-1 = no reply) |
| dns_fail_count | DNS errors or unanswered queries | count |
| tcp_retrans | TCP retransmissions | count |
| dhcp_offer_ms | DHCP Discover-to-Offer time | ms (-1 = no offer) |
| icmp_unreach | ICMP "unreachable" messages | count |
| pkt_rate | Packets per second | pkts/s |
| byte_rate | Bytes per second | B/s |

## Rules
1. Field names and units never change after this point. New fields may be added.
2. A failed measurement is stored as -1, never left empty.
3. The backend adds `timestamp`. The ESP32 has no clock.
4. Packet captures (.pcap/.pcapng) are never committed to Git.

## Sample ESP32 reading
{"device_id": "esp32-01", "rssi": -62, "gateway_latency": 4.2,
 "internet_latency": 31.5, "dns_time": 18, "packet_loss": 0,
 "jitter": 2.1, "http_time": 240, "reconnect_count": 0,
 "free_heap": 214000, "cpu_load": 12, "dhcp_clients": 1,
 "dhcp_leases_active": 1, "dhcp_pool_free": 9, "client_rssi_avg": -48}