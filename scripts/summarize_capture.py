#!/usr/bin/env python3
"""Summarize a MESS engine-stats diagnostic capture using only stdlib."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

CONFIGURATION_FIELDS = (
    "depth_model_variant",
    "depth_model_display_name",
    "depth_backend",
    "depth_input_data_type",
    "depth_input_width",
    "depth_input_height",
    "depth_output_width",
    "depth_output_height",
    "face_backend",
    "session_target_fps",
)

LATENCY_FROM_FPS_METRICS = (
    "depth_model_fps",
    "depth_total_fps",
    "foreground_model_fps",
    "foreground_total_fps",
    "face_completion_fps",
)

RATE_METRICS = (
    "presented_avg_60_fps",
    "presented_fps",
)

DIRECT_LATENCY_METRICS = (
    "face_latency_ms",
    "face_detector_ms",
    "face_landmarks_ms",
)


def read_json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def percentile(values: list[float], value: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * value / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def values_for(rows: list[dict[str, Any]], metric: str) -> list[float]:
    return [float(row[metric]) for row in rows if isinstance(row.get(metric), (int, float))]


def print_latency_from_fps(rows: list[dict[str, Any]], metric: str) -> None:
    rates = [value for value in values_for(rows, metric) if value > 0]
    if not rates:
        print(f"{metric}: not_recorded")
        return
    latencies = [1000.0 / value for value in rates]
    print(
        f"{metric}: samples={len(rates)} median_fps={statistics.median(rates):.3f} "
        f"implied_ms_median={statistics.median(latencies):.3f} "
        f"implied_ms_p90={percentile(latencies, 90):.3f} "
        f"implied_ms_p99={percentile(latencies, 99):.3f}"
    )


def print_rate(rows: list[dict[str, Any]], metric: str) -> None:
    values = values_for(rows, metric)
    if not values:
        print(f"{metric}: not_recorded")
        return
    print(
        f"{metric}: samples={len(values)} median={statistics.median(values):.3f} "
        f"p10={percentile(values, 10):.3f} p90={percentile(values, 90):.3f} "
        f"p99={percentile(values, 99):.3f}"
    )


def print_latency(rows: list[dict[str, Any]], metric: str) -> None:
    values = values_for(rows, metric)
    if not values:
        print(f"{metric}: not_recorded")
        return
    print(
        f"{metric}: samples={len(values)} median={statistics.median(values):.3f} "
        f"p90={percentile(values, 90):.3f} p99={percentile(values, 99):.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()

    events = read_json_lines(args.capture / "events.jsonl")
    records = read_json_lines(args.capture / "streams" / "engine-stats.jsonl")
    rows = [record.get("fields", {}) for record in records]
    rows = [row for row in rows if float(row.get("elapsed_s", 0)) >= 1]
    if not rows:
        parser.error("capture contains no engine-stats samples at or after one second")

    configuration = next(
        (event.get("fields", {}) for event in events if event.get("name") == "capture.configuration"),
        {},
    )
    ended = next(
        (event.get("fields", {}) for event in events if event.get("name") == "capture.ended"),
        None,
    )
    duration = max(float(row["elapsed_s"]) for row in rows)
    complete = "yes" if ended is not None else "no"
    dropped_events = ended.get("dropped_events", "unknown") if ended is not None else "unknown"

    print(
        f"capture={args.capture.name} duration_s={duration:.2f} samples={len(rows)} "
        f"complete={complete} dropped_events={dropped_events}"
    )
    if configuration:
        print("configuration:")
        for field in CONFIGURATION_FIELDS:
            if field in configuration:
                print(f"  {field}={configuration[field]}")
    else:
        print("configuration: not_recorded")

    for metric in LATENCY_FROM_FPS_METRICS:
        print_latency_from_fps(rows, metric)
    for metric in RATE_METRICS:
        print_rate(rows, metric)
    for metric in DIRECT_LATENCY_METRICS:
        print_latency(rows, metric)

    face_counts = values_for(rows, "face_count")
    if face_counts:
        print(
            f"face_count: samples={len(face_counts)} median={statistics.median(face_counts):.3f} "
            f"min={min(face_counts):.0f} max={max(face_counts):.0f}"
        )
    else:
        print("face_count: not_recorded")


if __name__ == "__main__":
    main()
