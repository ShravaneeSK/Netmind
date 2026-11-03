# Fault class: dhcp_failure

## dhcp_failure: signature
dhcp_offer_ms is -1, meaning a DHCP request got no reply. dhcp_pool_free is 0, or dhcp_clients and dhcp_leases_active are 0 even though a device is trying to join. pkt_rate is very low. The client may end up with a self-assigned address that starts with 169.254.

## dhcp_failure: likely causes
- The address pool is exhausted, because there are too many clients or stale leases.
- The DHCP service has stopped or crashed.
- A second, rogue DHCP server is giving out wrong settings.
- The ESP32 access point has reached its client limit, which is small (a few devices, configurable up to roughly 10).
- A lease time that is too long, so old leases are never freed.

## dhcp_failure: how to check
Run ipconfig on the client: an address starting with 169.254 means DHCP failed. Compare dhcp_leases_active with the pool size. Capture with Wireshark using the filter dhcp and look for Discover packets with no Offer reply.

## dhcp_failure: how to fix
Enlarge the pool. Shorten the lease time. Restart the DHCP service. Remove stale leases and disconnect unused devices. Make sure only one DHCP server is active. Renew the lease on the client with ipconfig /renew. Severity is High, because new devices cannot join the network.
