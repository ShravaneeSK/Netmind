from sqlalchemy import Column, DateTime, Float, Integer, String, func

from .database import Base


class Telemetry(Base):
    """One reading sent by the ESP32 node (schema v2, Source 1)."""

    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    received_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    rssi = Column(Float, nullable=False)
    gateway_latency = Column(Float, nullable=False)
    internet_latency = Column(Float, nullable=False)
    dns_time = Column(Float, nullable=False)
    packet_loss = Column(Float, nullable=False)
    jitter = Column(Float, nullable=False)
    http_time = Column(Float, nullable=False)
    reconnect_count = Column(Integer, nullable=False)
    free_heap = Column(Integer, nullable=False)
    cpu_load = Column(Float, nullable=False)
    dhcp_clients = Column(Integer, nullable=False)
    dhcp_leases_active = Column(Integer, nullable=False)
    dhcp_pool_free = Column(Integer, nullable=False)
    client_rssi_avg = Column(Float, nullable=False)


class PacketFeatures(Base):
    """One 5-second window of packet features from Wireshark/tshark (schema v2, Source 2)."""

    __tablename__ = "packet_features"

    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    dns_response_ms = Column(Float, nullable=False)
    dns_fail_count = Column(Integer, nullable=False)
    tcp_retrans = Column(Integer, nullable=False)
    dhcp_offer_ms = Column(Float, nullable=False)
    icmp_unreach = Column(Integer, nullable=False)
    pkt_rate = Column(Float, nullable=False)
    byte_rate = Column(Float, nullable=False)


class Prediction(Base):
    """ML output for one telemetry reading (filled from Stage 5)."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    telemetry_id = Column(Integer, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    anomaly_score = Column(Float, nullable=True)
    fault_label = Column(String(30), nullable=True)
    severity = Column(String(10), nullable=True)