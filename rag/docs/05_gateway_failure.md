# Fault class: gateway_failure

## gateway_failure: signature
gateway_latency is -1, internet_latency is -1, dns_time is -1 and http_time is -1. packet_loss is close to 100 percent and pkt_rate is close to 0. icmp_unreach may appear. rssi can still look good, because the Wi-Fi link may be up while the router no longer forwards traffic.

## gateway_failure: likely causes
- The router crashed, froze, lost power or is overloaded.
- A cable or port between the node and the router has failed.
- Wrong gateway or IP configuration on the client.
- The client lost its DHCP lease and has no valid address.
- Access point client isolation blocks traffic to the gateway.

## gateway_failure: how to check
Ping the gateway address (find it with ipconfig). If the gateway does not reply, nothing beyond it can work. Check the router lights and power, and whether other devices are affected. Compare with internet_failure, where the gateway still replies.

## gateway_failure: how to fix
Power-cycle the router. Check power and cables. Reconnect to Wi-Fi, or renew the lease with ipconfig /renew. Check static IP and gateway settings. Severity is Critical, because the client cannot reach anything.
