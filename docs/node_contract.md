# Node contract (v1)

Any measurement node (the PC probe now, an ESP32 later) feeds NetMind through
POST /telemetry using schema v2 (docs/telemetry_schema.md). This file says what a node
must do, so that the rest of the system needs no change when a new node type is added.

## Device types

| Type | device_id convention | Status |
|---|---|---|
| pc | pc-<name>, for example pc-probe | implemented (probe/probe_node.py) |
| esp32 | esp32-<nn>, for example esp32-01 | planned |
| sim | esp32-sim and demo | simulator and demo only, never reported as results |

The part of the id before the first "-" names the type, except esp32-sim and demo, which
are sim. Models are trained and used per type.

## Required behaviour

1. Send one POST /telemetry about every 5 seconds.
2. Send all 15 fields. A failed measurement is -1. Never send null.
3. No clock is needed on the node. The backend adds received_at.
4. Use the units of the schema.
5. Send JSON with Content-Type application/json. From Stage 14 an X-API-Key header is required.

## Field provenance

| Field | PC probe | ESP32 (planned) |
|---|---|---|
| rssi | netsh signal quality converted to dBm (approximate) | WiFi.RSSI() to the router |
| gateway_latency | ping to the default gateway | ping or TCP connect to the router |
| internet_latency | ping to 8.8.8.8 | ping or TCP connect to 8.8.8.8 |
| dns_time | dnspython query to the system DNS | hostname lookup timing |
| packet_loss | percent lost of 5 pings to 8.8.8.8 | percent lost of the last 10 probes |
| jitter | standard deviation of those ping times | standard deviation of the last 10 probe times |
| http_time | GET https://example.com | HTTP GET timing |
| reconnect_count | Wi-Fi reconnects seen by the probe | reconnects since boot |
| free_heap | free PC memory in bytes | ESP.getFreeHeap() |
| cpu_load | psutil CPU percent | estimated from loop timing |
| dhcp_clients, dhcp_leases_active, dhcp_pool_free | 0 (a PC is not an access point) | measured from the ESP32 DHCP server |
| client_rssi_avg | same as rssi | mean RSSI of the connected clients |

## Fault classes per type

- pc: 8 classes (no dhcp_failure)
- esp32: 9 classes
- sim: 9 classes

## Consequences

- rssi, free_heap and cpu_load differ in scale and meaning between types, so a model
  trained on one type must not be used for another.
- A new node type needs three things: a profile in the training code, its own real
  dataset, and a model bundle named <type>_*.joblib.

## Checklist for adding the ESP32

1. Flash a ready-made NAT router and confirm that a laptop gets an address and internet.
2. Write the firmware: probes, the 15 fields, POST /telemetry every 5 seconds.
3. Add the DHCP and client fields.
4. Run labelled fault experiments and collect a real dataset for the esp32 type.
5. Train and evaluate the esp32 profile.
6. Check the dashboard device selector and the per-type severity rules.
