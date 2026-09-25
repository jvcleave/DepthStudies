#!/usr/bin/env python3
"""Summarize a MESS engine-stats diagnostic capture using only stdlib."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

METRICS = (
    "depth_model_fps",
    "depth_total_fps",
    "presented_avg_60_fps",
    "foreground_model_fps",
    "face_latency_ms",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()

    stream = args.capture / "streams" / "engine-stats.jsonl"
    rows = [json.loads(line)["fields"] for line in stream.read_text().splitlines()]
    rows = [row for row in rows if float(row.get("elapsed_s", 0)) >= 1]
    duration = max(float(row["elapsed_s"]) for row in rows)

    print(f"capture={args.capture.name} duration_s={duration:.2f} samples={len(rows)}")
    for metric in METRICS:
        values = [float(row[metric]) for row in rows if metric in row]
        median = statistics.median(values)
        output = f"{metric}: median={median:.3f}"
        if metric.endswith("_fps"):
            output += f" implied_ms={1000.0 / median:.3f}"
        print(output)


if __name__ == "__main__":
    main()
