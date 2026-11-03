# Fault class: normal

## normal: signature
A healthy network. rssi is above -67 dBm, gateway_latency is under 10 ms, internet_latency is 15-60 ms, dns_time is under 100 ms, packet_loss is 0, jitter is low, cpu_load is moderate, free_heap is healthy, dns_fail_count is 0 and dhcp_offer_ms is 0 because no DHCP exchange happened.

## normal: likely causes
Nothing is wrong. Single odd readings, such as one retransmission or one slow DNS lookup, are part of normal operation.

## normal: how to check
Compare the reading with the recent baseline. Act only if the deviation repeats over several windows.

## normal: how to fix
No action is needed. If the anomaly detector flags a reading that the classifier calls normal, the reading is unusual but matches no known fault. Watch the trend over the next windows and compare it with the baseline, because it could be the start of a new kind of problem.
