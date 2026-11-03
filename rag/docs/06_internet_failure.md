# Fault class: internet_failure

## internet_failure: signature
gateway_latency is normal, but internet_latency is -1, dns_time is -1 and http_time is -1. packet_loss is high and icmp_unreach may appear. The local network works and the path to the internet is broken.

## internet_failure: likely causes
- An ISP outage.
- A failed modem, WAN cable or WAN port.
- The router has lost its WAN connection or its login to the ISP.
- A routing problem upstream.
- An account or billing problem with the provider.

## internet_failure: how to check
Ping the gateway, which works, then ping 8.8.8.8, which fails. Check the modem and router lights and the router's WAN status page. Try a mobile hotspot to confirm that the problem is the ISP and not the device. If only DNS fails while pinging 8.8.8.8 works, the fault is dns_failure instead.

## internet_failure: how to fix
Restart the modem first, wait for it to settle, then restart the router. Check the WAN cable. Check the ISP's status page or contact the ISP. Severity is Critical, because there is no external connectivity.
