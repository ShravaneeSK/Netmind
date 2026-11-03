# Fault class: intermittent_loss

## intermittent_loss: signature
packet_loss fluctuates between about 10 and 50 percent, latency spikes appear, jitter is high and tcp_retrans comes in bursts. Readings alternate between good and bad. reconnect_count may rise.

## intermittent_loss: likely causes
- A marginal signal or interference that comes and goes.
- A failing cable or loose connector.
- Overheating or failing network hardware.
- An unstable power supply.
- Driver or firmware bugs.
- Channel contention with neighbouring networks.

## intermittent_loss: how to check
Run an extended ping and look at the pattern: periodic loss points to a scheduled source such as a timer or a microwave oven, and random loss points to signal or hardware. Test at different times and locations. Swap cables. Watch reconnect_count. Unlike weak_signal, rssi may look acceptable between the drops.

## intermittent_loss: how to fix
Change the Wi-Fi channel. Replace suspect cables and connectors. Update firmware and drivers. Use a stable power supply. Reposition the node or the access point. Severity is Medium, rising to High when packet loss exceeds 30 percent.
