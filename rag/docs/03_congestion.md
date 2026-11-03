# Fault class: congestion

## congestion: signature
rssi is good, but gateway_latency and internet_latency are both high (over 150 ms), jitter is high, http_time is high, tcp_retrans is high, and pkt_rate and byte_rate are well above normal. The signal is fine and the link is full.

## congestion: likely causes
- Large downloads, uploads, software updates or video streaming.
- Too many active clients sharing the link.
- One device flooding the network.
- Excess buffering in the router, which delays packets.
- The limited throughput of an ESP32 access point.

## congestion: how to check
Compare pkt_rate and byte_rate with the normal baseline. Pause the heavy transfer and see whether latency drops. Check how many devices are connected (dhcp_clients). Unlike weak_signal, rssi is good here, which is the main way to tell the two apart.

## congestion: how to fix
Pause or schedule heavy transfers. Limit the number of connected devices. Use quality-of-service rules to prioritise important traffic. Move heavy devices to a wired connection. Use a faster uplink if the load is permanent. Severity rises to High when packet loss exceeds 5 percent or internet_latency exceeds 400 ms.
