# Fault class: device_overload

## device_overload: signature
free_heap is low and cpu_load is high (over 80 percent), while rssi is good. Timings are erratic and probes are slow even though the network itself may be fine. gateway_latency and internet_latency can be inflated by the node and not by the network.

## device_overload: likely causes
- Too many tasks or probes running on the ESP32.
- A memory leak, which shows as free_heap falling steadily over time.
- Too many clients connected to the ESP32 access point.
- Heavy logging or large buffers.
- Forwarding too much traffic for the small processor.

## device_overload: how to check
Watch the free_heap trend. A steady fall points to a leak. Watch cpu_load while changing the probe rate. Check dhcp_clients. Restart the node: if readings return to normal and then degrade again, the node is the problem and not the network. Measurements from an overloaded node are unreliable.

## device_overload: how to fix
Reduce the probe frequency. Fix memory leaks. Limit the number of connected clients. Reduce logging and buffer sizes. Add a watchdog that restarts the node. Severity is Medium, rising to High when free_heap is below 20000 bytes or cpu_load is above 97 percent.
