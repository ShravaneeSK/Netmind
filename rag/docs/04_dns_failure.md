# Fault class: dns_failure

## dns_failure: signature
dns_time is -1 and dns_response_ms is -1 (or error replies appear), dns_fail_count rises and http_time is -1. Pings to an IP address still work, so gateway_latency and internet_latency are normal. The network works but names cannot be resolved.

## dns_failure: likely causes
- The DNS server is down or unreachable.
- A wrong DNS address is handed out in the DHCP settings.
- A firewall blocks DNS (port 53, UDP and TCP).
- An outage at the upstream resolver, often the ISP's.
- A misspelled or non-existent domain. This is not an outage: the server still replies with an error, so dns_response_ms stays above 0 while dns_fail_count rises.

## dns_failure: how to check
Ping 8.8.8.8, which works if the internet is fine. Then run nslookup example.com, which fails if DNS is the problem. Try another resolver with nslookup example.com 1.1.1.1. If that works, the original DNS server is at fault.

## dns_failure: how to fix
Set a working DNS server, for example 1.1.1.1 or 8.8.8.8, in the router or in the DHCP settings. Restart the router or its DNS service. Check that the firewall allows port 53. Flush the client DNS cache with ipconfig /flushdns. Severity is High, because most services stop working without name resolution.
