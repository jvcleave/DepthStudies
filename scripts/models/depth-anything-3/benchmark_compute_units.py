#!/usr/bin/env python3
"""Compare fixed Core ML compute-unit choices for one DA3 image package."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import coremltools as ct
import numpy as np
from PIL import Image


EXPECTED_COREMLTOOLS_VERSION = "9.0"
DEFAULT_COMPUTE_UNITS = ("CPU_AND_GPU", "CPU_AND_NE", "ALL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark one DA3 Core ML image package with alternating fixed "
            "compute-unit configurations."
        )
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--input-size", type=int, default=392)
    parser.add_argument("--warmups", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument(
        "--compute-units",
        default=",".join(DEFAULT_COMPUTE_UNITS),
        help="Comma-separated Core ML compute units.",
    )
    parser.add_argument("--minimum-cosine", type=float, default=0.999)
    parser.add_argument("--maximum-mean-absolute-error", type=float, default=0.01)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with file_path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def developer_tools_version() -> str:
    result = subprocess.run(
        ["xcodebuild", "-version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def parse_compute_units(value: str) -> list[str]:
    names = [item.strip() for item in value.split(",") if item.strip()]
    if not names:
        raise ValueError("At least one compute-unit name is required")
    if len(names) != len(set(names)):
        raise ValueError("Compute-unit names must be unique")
    for name in names:
        if not hasattr(ct.ComputeUnit, name):
            expected = ", ".join(unit.name for unit in ct.ComputeUnit)
            raise ValueError(f"Unknown compute unit {name!r}; expected one of {expected}")
    if "CPU_AND_GPU" not in names:
        raise ValueError("CPU_AND_GPU is required as the output-agreement reference")
    return names


def validate_contract(model_path: Path, input_size: int) -> tuple[str, str]:
    specification = ct.utils.load_spec(str(model_path))
    if len(specification.description.input) != 1:
        raise ValueError("Expected one model input")
    if len(specification.description.output) != 1:
        raise ValueError("Expected one model output")
    model_input = specification.description.input[0]
    model_output = specification.description.output[0]
    if model_input.type.WhichOneof("Type") != "imageType":
        raise ValueError("Expected an image input")
    dimensions = (model_input.type.imageType.width, model_input.type.imageType.height)
    if dimensions != (input_size, input_size):
        raise ValueError(
            f"Expected {input_size} x {input_size} input, got {dimensions[0]} x {dimensions[1]}"
        )
    if model_output.type.WhichOneof("Type") != "imageType":
        raise ValueError("Expected an image output")
    return model_input.name, model_output.name


def rotated(values: list[str], index: int) -> list[str]:
    offset = index % len(values)
    return values[offset:] + values[:offset]


def summarize(timings: list[float]) -> dict[str, float]:
    samples = np.asarray(timings, dtype=np.float64)
    return {
        "minimum": float(np.min(samples)),
        "median": float(np.median(samples)),
        "p90": float(np.percentile(samples, 90)),
        "p99": float(np.percentile(samples, 99)),
        "maximum": float(np.max(samples)),
        "mean": float(np.mean(samples)),
    }


def output_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32).squeeze()
    if array.ndim != 2:
        raise ValueError(f"Expected a two-dimensional depth map, got shape {array.shape}")
    if not np.isfinite(array).all():
        raise ValueError("Depth output contains nonfinite values")
    return array


def compare_outputs(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    if reference.shape != candidate.shape:
        raise ValueError(
            f"Output shape mismatch: reference {reference.shape}, candidate {candidate.shape}"
        )
    reference_values = reference.astype(np.float64, copy=False).reshape(-1)
    candidate_values = candidate.astype(np.float64, copy=False).reshape(-1)
    difference = reference_values - candidate_values
    absolute_difference = np.abs(difference)
    denominator = np.linalg.norm(reference_values) * np.linalg.norm(candidate_values)
    cosine = float(np.dot(reference_values, candidate_values) / max(denominator, 1e-12))
    rmse = float(np.sqrt(np.mean(np.square(difference))))
    reference_peak = max(float(np.max(np.abs(reference_values))), 1e-12)
    return {
        "cosine_similarity": max(-1.0, min(1.0, cosine)),
        "mean_absolute_error": float(np.mean(absolute_difference)),
        "maximum_absolute_error": float(np.max(absolute_difference)),
        "rmse": rmse,
        "normalized_rmse": rmse / reference_peak,
    }


def main() -> None:
    args = parse_args()
    if platform.system() != "Darwin":
        raise RuntimeError("Core ML prediction requires macOS")
    if ct.__version__ != EXPECTED_COREMLTOOLS_VERSION:
        raise ValueError(
            f"Expected coremltools {EXPECTED_COREMLTOOLS_VERSION}, got {ct.__version__}"
        )
    if args.input_size <= 0:
        raise ValueError("Input size must be positive")
    if args.warmups < 0 or args.iterations <= 0:
        raise ValueError("Warmups must be nonnegative and iterations must be positive")
    if args.minimum_cosine <= 0 or args.minimum_cosine > 1:
        raise ValueError("Minimum cosine must be in (0, 1]")
    if args.maximum_mean_absolute_error <= 0:
        raise ValueError("Maximum mean absolute error must be positive")

    model_path = args.model.expanduser().resolve()
    image_path = args.image.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if not model_path.is_dir():
        raise FileNotFoundError(model_path)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    input_name, output_name = validate_contract(model_path, args.input_size)
    compute_unit_names = parse_compute_units(args.compute_units)
    image = Image.open(image_path).convert("RGB").resize(
        (args.input_size, args.input_size),
        Image.Resampling.BICUBIC,
    )
    models = {
        name: ct.models.MLModel(
            str(model_path),
            compute_units=getattr(ct.ComputeUnit, name),
        )
        for name in compute_unit_names
    }

    latest_outputs: dict[str, np.ndarray] = {}
    for warmup_index in range(args.warmups):
        for name in rotated(compute_unit_names, warmup_index):
            prediction = models[name].predict({input_name: image})[output_name]
            latest_outputs[name] = output_array(prediction)

    timings = {name: [] for name in compute_unit_names}
    for iteration in range(args.iterations):
        for name in rotated(compute_unit_names, iteration):
            start = time.perf_counter_ns()
            prediction = models[name].predict({input_name: image})[output_name]
            elapsed_milliseconds = (time.perf_counter_ns() - start) / 1_000_000.0
            timings[name].append(elapsed_milliseconds)
            latest_outputs[name] = output_array(prediction)

    reference = latest_outputs["CPU_AND_GPU"]
    comparisons = {}
    all_passed = True
    for name in compute_unit_names:
        comparison = compare_outputs(reference, latest_outputs[name])
        comparison["passed"] = (
            comparison["cosine_similarity"] >= args.minimum_cosine
            and comparison["mean_absolute_error"] <= args.maximum_mean_absolute_error
        )
        all_passed = all_passed and bool(comparison["passed"])
        comparisons[name] = comparison

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "macos": platform.mac_ver()[0],
            "machine": platform.machine(),
            "python": platform.python_version(),
            "developer_tools": developer_tools_version(),
        },
        "coremltools_version": ct.__version__,
        "model": {
            "name": model_path.name,
            "tree_sha256": sha256_tree(model_path),
            "input_name": input_name,
            "output_name": output_name,
            "input_size": [args.input_size, args.input_size],
        },
        "image": {
            "name": image_path.name,
            "sha256": sha256_file(image_path),
        },
        "protocol": {
            "scope": "synchronous Core ML prediction with one reused resized PIL image",
            "warmups_per_compute_unit": args.warmups,
            "iterations_per_compute_unit": args.iterations,
            "alternating_order": True,
            "compute_units": compute_unit_names,
        },
        "thresholds": {
            "minimum_cosine": args.minimum_cosine,
            "maximum_mean_absolute_error": args.maximum_mean_absolute_error,
        },
        "passed": all_passed,
        "timing_milliseconds": {
            name: {
                "summary": summarize(timings[name]),
                "samples": timings[name],
            }
            for name in compute_unit_names
        },
        "output_comparison_to_cpu_and_gpu": comparisons,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
