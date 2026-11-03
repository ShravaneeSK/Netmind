# Fault class: weak_signal

## weak_signal: signature
rssi is below -75 dBm (and client_rssi_avg is low), gateway_latency is rising, jitter is high, some packet loss appears and tcp_retrans rises. The link is up but poor. reconnect_count may increase.

## weak_signal: likely causes
- Distance between the node and the router or access point.
- Walls, metal, concrete, water or large furniture blocking the signal.
- Interference on the 2.4 GHz band from neighbouring networks, microwave ovens, Bluetooth devices or cordless phones.
- Poor antenna placement or orientation.

## weak_signal: how to check
Compare rssi at different positions. Move the node closer to the router and see whether latency and loss improve. Scan nearby networks to see which channel is crowded. The ESP32 supports 2.4 GHz only, so it cannot move to 5 GHz.

## weak_signal: how to fix
Move the node or the access point, and remove obstacles between them. Switch the router to a less crowded channel (1, 6 or 11 do not overlap). Reduce interference sources. Add an access point or range extender. Severity rises to High when rssi is below -85 dBm or packet loss exceeds 15 percent.
