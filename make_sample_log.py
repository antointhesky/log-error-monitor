#!/usr/bin/env python3
"""Create a fake application log for testing log_monitor.py."""

import os
import random
from datetime import datetime, timedelta

random.seed(42)

COMPONENTS = ["OrderGateway", "MarketData", "RiskCheck", "DataCapture"]
INFO = ["Heartbeat OK", "Order {n} accepted", "Snapshot saved", "Session started"]
WARN = ["Slow response {n}ms from exchange", "Retrying request {n}"]
ERRORS = [
    "Connection timeout after {n}s",
    "Order {n} rejected: invalid price",
    "Feed gap detected, missing {n} messages",
    "Disk write failed at 0x{h}",
]


def line(ts, level, comp, msg):
    return f"{ts:%Y-%m-%d %H:%M:%S},{random.randint(0, 999):03d} {level} [{comp}] {msg}"


def main(path="sample_logs/app.log", lines=600):
    ts = datetime(2026, 10, 24, 7, 15, 0)
    out = []
    for i in range(lines):
        ts += timedelta(seconds=random.randint(1, 8))
        roll = random.random()
        comp = random.choice(COMPONENTS)
        n, h = random.randint(1, 9999), f"{random.randint(0, 65535):04x}"
        if roll < 0.78:
            out.append(line(ts, "INFO", comp, random.choice(INFO).format(n=n)))
        elif roll < 0.92:
            out.append(line(ts, "WARN", comp, random.choice(WARN).format(n=n)))
        else:
            out.append(line(ts, "ERROR", comp, random.choice(ERRORS).format(n=n, h=h)))
        if i == 400:  # simulate an incident: a burst of feed errors
            for _ in range(25):
                ts += timedelta(seconds=1)
                out.append(line(ts, "ERROR", "MarketData",
                                "Feed gap detected, missing %d messages" % random.randint(5, 50)))
    out.insert(100, "this line is corrupted and has no timestamp")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")
    print(f"Wrote {len(out)} lines to {path}")


if __name__ == "__main__":
    main()