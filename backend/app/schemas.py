from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TelemetryIn(BaseModel):
    """What the ESP32 sends (schema v2, Source 1). -1 means a failed measurement."""

    device_id: str = Field(min_length=1, max_length=50)
    rssi: float
    gateway_latency: float = Field(ge=-1)
    internet_latency: float = Field(ge=-1)
    dns_time: float = Field(ge=-1)
    packet_loss: float = Field(ge=0, le=100)
    jitter: float = Field(ge=0)
    http_time: float = Field(ge=-1)
    reconnect_count: int = Field(ge=0)
    free_heap: int = Field(ge=0)
    cpu_load: float = Field(ge=0, le=100)
    dhcp_clients: int = Field(ge=0)
    dhcp_leases_active: int = Field(ge=0)
    dhcp_pool_free: int = Field(ge=0)
    client_rssi_avg: float


class TelemetryOut(TelemetryIn):
    id: int
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PacketFeaturesIn(BaseModel):
    """What the packet collector sends (schema v2, Source 2)."""

    dns_response_ms: float = Field(ge=-1)
    dns_fail_count: int = Field(ge=0)
    tcp_retrans: int = Field(ge=0)
    dhcp_offer_ms: float = Field(ge=-1)
    icmp_unreach: int = Field(ge=0)
    pkt_rate: float = Field(ge=0)
    byte_rate: float = Field(ge=0)


class PacketFeaturesOut(PacketFeaturesIn):
    id: int
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)