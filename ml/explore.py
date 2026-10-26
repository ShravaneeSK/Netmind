"""Look at the dataset before training: balance, missing values, sentinels, feature signal."""
import argparse
from pathlib import Path

import pandas as pd
from sklearn.feature_selection import mutual_info_classif

DATA = Path(__file__).resolve().parent / "data"
SENTINELS = ["gateway_latency", "internet_latency", "dns_time", "http_time",
             "dns_response_ms", "dhcp_offer_ms"]
KEY = ["rssi", "gateway_latency", "internet_latency", "dns_time", "packet_loss", "cpu_load",
       "free_heap", "dhcp_pool_free", "dns_response_ms", "dns_fail_count", "pkt_rate"]
NON_FEATURES = ["id", "received_at", "device_id", "fault_label", "packet_matched", "packet_gap_s"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(DATA / "sim_dataset.csv"))
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    print(f"Rows: {len(df)}   Columns: {df.shape[1]}")

    print("\n== Rows per class ==")
    print(df["fault_label"].value_counts().to_string())

    print("\n== Rows with no packet window ==")
    print(int((~df["packet_matched"]).sum()))

    print("\n== Median of key features per class ==")
    pd.set_option("display.width", 220)
    print(df.groupby("fault_label")[KEY].median().round(1).T.to_string())

    print("\n== Count of -1 (failed measurement) per class ==")
    print((df[SENTINELS] == -1).groupby(df["fault_label"]).sum().to_string())

    print("\n== normal rows with pkt_rate < 60 (likely real collector rows, not simulated) ==")
    n = df[(df["fault_label"] == "normal") & (df["pkt_rate"] < 60)]
    print(len(n), "rows", list(n["id"])[:10])

    X = df.drop(columns=NON_FEATURES).fillna(-2)
    mi = pd.Series(mutual_info_classif(X, df["fault_label"], random_state=0), index=X.columns)
    print("\n== Features ranked by how much they tell the classes apart ==")
    print(mi.sort_values(ascending=False).round(2).to_string())


if __name__ == "__main__":
    main()
