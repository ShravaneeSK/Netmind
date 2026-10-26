# Fault Classes (v2, FROZEN)

| ID | Label | Expected signature |
|---|---|---|
| 0 | normal | rssi > -67, gateway_latency < 10, internet_latency 15-60, dns_time < 100, packet_loss 0, tcp_retrans low |
| 1 | weak_signal | rssi < -75 (or client_rssi_avg low), gateway_latency rising, jitter high, some loss, tcp_retrans rising |
| 2 | congestion | rssi good, gateway and internet latency both high (> 150), jitter high, http_time high, tcp_retrans high |
| 3 | dns_failure | dns_time = -1, dns_response_ms = -1, dns_fail_count rising, but pings by IP normal |
| 4 | gateway_failure | gateway_latency = -1, internet_latency = -1, dns_time = -1, packet_loss near 100, icmp_unreach may appear |
| 5 | internet_failure | gateway_latency normal, internet_latency = -1, dns_time = -1, http_time = -1 |
| 6 | device_overload | free_heap low, cpu_load high, timings erratic while the network is fine, rssi good |
| 7 | intermittent_loss | packet_loss fluctuating (10-50%), latency spikes, jitter high, tcp_retrans spiky |
| 8 | dhcp_failure | dhcp_offer_ms = -1 or very high, dhcp_pool_free = 0, or the client has no IP, while the ESP32's own link is fine |

These signatures are starting hypotheses. In Stage 4 you will check them
against real measurements and adjust them if the data says otherwise.

# Severity levels
None (no fault) | Low | Medium | High | Critical

Severity is rule-based (see backend/app/severity.py): a base level per fault class,
raised one step when measurements cross a threshold.

The rules that map a fault to a severity level are defined in Stage 5.