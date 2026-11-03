# NetMind telemetry glossary

## telemetry glossary: data sources
NetMind merges two data sources into one record per 5-second window. The ESP32 node sends 15 fields (signal, latency, DNS, loss, jitter, HTTP, memory, CPU and DHCP counters). A packet collector on the client PC analyses its own traffic with Wireshark/tshark and sends 7 packet features. The PC is the client under test.

## telemetry glossary: failed measurements
A value of -1 means a measurement was attempted and failed, for example no reply or a timeout. It is a real signal and not missing data. dhcp_offer_ms is different: 0 means no DHCP exchange happened in the window, and -1 means a DHCP request got no reply.

## telemetry glossary: ESP32 fields
- rssi: signal strength from the ESP32 to the router, in dBm. Closer to 0 is stronger. Above -67 is good, below -75 is weak, below -85 is very weak.
- gateway_latency: time to reach the router, in ms. Normal is under 10 ms.
- internet_latency: time to reach 8.8.8.8, in ms. Normal is 15-60 ms.
- dns_time: time to resolve a hostname, in ms. Normal is under 100 ms.
- packet_loss: percentage of probes with no reply over the last 10 probes.
- jitter: variation in latency, in ms.
- http_time: time to fetch a test web page, in ms.
- reconnect_count: number of Wi-Fi reconnects since boot.
- free_heap: free RAM on the ESP32, in bytes. Below 20000 is critically low.
- cpu_load: approximate processor load, in percent. Above 80 is high.
- dhcp_clients, dhcp_leases_active, dhcp_pool_free: devices connected to the ESP32 access point, active DHCP leases, and addresses still free in the pool.
- client_rssi_avg: average signal strength of the devices connected to the ESP32 access point.

## telemetry glossary: packet features
- dns_response_ms: median DNS reply time seen on the wire, in ms.
- dns_fail_count: DNS error replies plus unanswered queries. A "no such domain" reply counts here even though the server answered.
- tcp_retrans: TCP retransmissions, meaning packets that had to be sent again.
- dhcp_offer_ms: time from DHCP request to reply.
- icmp_unreach: ICMP "destination unreachable" messages.
- pkt_rate and byte_rate: packets and bytes per second.

## telemetry glossary: severity levels
Severity is rule-based. Each fault has a base level (None, Low, Medium, High or Critical). It is raised one step when measurements cross a threshold, for example weak_signal with rssi below -85 dBm, or device_overload with free_heap below 20000 bytes. gateway_failure and internet_failure are Critical, dns_failure and dhcp_failure are High, and the others start at Medium.
