import argparse
import json
import math
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import coremltools as ct
import numpy as np
from PIL import Image
from coremltools.proto import FeatureTypes_pb2


EXPECTED_COREMLTOOLS_VERSION = "9.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare image-input and tensor-FP16 DA2 Core ML packages."
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--width", type=int, default=448)
    parser.add_argument("--height", type=int, default=336)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--maximum-normalized-rmse", type=float, default=0.002)
    parser.add_argument("--maximum-absolute-error", type=float, default=0.02)
    parser.add_argument("--warmups", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    return parser.parse_args()


def make_samples(width: int, height: int) -> list[tuple[str, np.ndarray]]:
    x = np.linspace(0, 255, width, dtype=np.uint8)[None, :]
    y = np.linspace(0, 255, height, dtype=np.uint8)[:, None]
    gradient = np.stack(
        [
            np.broadcast_to(x, (height, width)),
            np.broadcast_to(y, (height, width)),
            ((x.astype(np.uint16) + y.astype(np.uint16)) // 2).astype(np.uint8),
        ],
        axis=-1,
    )

    tile = max(1, min(width, height) // 16)
    yy, xx = np.indices((height, width))
    checker_value = (((xx // tile) + (yy // tile)) % 2 * 255).astype(np.uint8)
    checker = np.stack(
        [checker_value, np.roll(checker_value, tile // 2, axis=0), 255 - checker_value],
        axis=-1,
    )

    random = np.random.default_rng(0).integers(
        0,
        256,
        size=(height, width, 3),
        dtype=np.uint8,
    )
    return [("gradient", gradient), ("checker", checker), ("random-seed-0", random)]


def feature_kind(feature) -> str:
    return feature.type.WhichOneof("Type")


def validate_contracts(baseline_spec, candidate_spec, width: int, height: int) -> None:
    baseline_input = baseline_spec.description.input[0]
    baseline_output = baseline_spec.description.output[0]
    candidate_input = candidate_spec.description.input[0]
    candidate_output = candidate_spec.description.output[0]
    if feature_kind(baseline_input) != "imageType":
        raise ValueError("Baseline input must be an image")
    if (baseline_input.type.imageType.width, baseline_input.type.imageType.height) != (
        width,
        height,
    ):
        raise ValueError("Baseline image dimensions do not match the requested shape")
    if feature_kind(baseline_output) != "imageType":
        raise ValueError("Baseline output must be an image")
    if (baseline_output.type.imageType.width, baseline_output.type.imageType.height) != (
        width,
        height,
    ):
        raise ValueError("Baseline depth dimensions do not match the requested shape")
    if feature_kind(candidate_input) != "multiArrayType":
        raise ValueError("Candidate input must be a multi-array")
    if list(candidate_input.type.multiArrayType.shape) != [1, 3, height, width]:
        raise ValueError("Candidate input shape does not match planar NCHW")
    if candidate_input.type.multiArrayType.dataType != FeatureTypes_pb2.ArrayFeatureType.FLOAT16:
        raise ValueError("Candidate input must be FLOAT16")
    if feature_kind(candidate_output) != "multiArrayType":
        raise ValueError("Candidate output must be a multi-array")
    if list(candidate_output.type.multiArrayType.shape) != [1, 1, height, width]:
        raise ValueError("Candidate output shape is incorrect")
    if candidate_output.type.multiArrayType.dataType != FeatureTypes_pb2.ArrayFeatureType.FLOAT16:
        raise ValueError("Candidate output must be FLOAT16")


def depth_array(value, width: int, height: int) -> np.ndarray:
    result = np.asarray(value, dtype=np.float32).squeeze()
    if result.shape != (height, width):
        raise ValueError(f"Expected depth output {(height, width)}, got {result.shape}")
    return result


def predict_milliseconds(model: ct.models.MLModel, model_input) -> float:
    start = time.perf_counter_ns()
    model.predict({"image": model_input})
    return (time.perf_counter_ns() - start) / 1_000_000.0


def summarize(values: list[float]) -> dict[str, float]:
    samples = np.asarray(values, dtype=np.float64)
    return {
        "minimum": float(np.min(samples)),
        "median": float(np.median(samples)),
        "p90": float(np.percentile(samples, 90)),
        "p99": float(np.percentile(samples, 99)),
        "maximum": float(np.max(samples)),
        "mean": float(np.mean(samples)),
    }


def main() -> None:
    args = parse_args()
    if ct.__version__ != EXPECTED_COREMLTOOLS_VERSION:
        raise ValueError(
            f"Expected coremltools {EXPECTED_COREMLTOOLS_VERSION}, got {ct.__version__}"
        )
    if args.width <= 0 or args.height <= 0:
        raise ValueError("Width and height must be positive")
    if args.maximum_normalized_rmse <= 0 or args.maximum_absolute_error <= 0:
        raise ValueError("Validation thresholds must be positive")
    if args.warmups < 0 or args.iterations <= 0:
        raise ValueError("Warmups must be nonnegative and iterations must be positive")

    baseline_path = args.baseline.expanduser().resolve()
    candidate_path = args.candidate.expanduser().resolve()
    baseline_spec = ct.utils.load_spec(str(baseline_path))
    candidate_spec = ct.utils.load_spec(str(candidate_path))
    validate_contracts(baseline_spec, candidate_spec, args.width, args.height)

    baseline = ct.models.MLModel(
        str(baseline_path),
        compute_units=ct.ComputeUnit.CPU_AND_GPU,
    )
    candidate = ct.models.MLModel(
        str(candidate_path),
        compute_units=ct.ComputeUnit.CPU_AND_GPU,
    )

    samples = []
    all_passed = True
    for name, pixels in make_samples(args.width, args.height):
        image = Image.fromarray(pixels)
        baseline_output = depth_array(
            baseline.predict({"image": image})["depth"],
            args.width,
            args.height,
        )
        planar_input = np.transpose(pixels, (2, 0, 1))[None].astype(np.float16)
        candidate_output = depth_array(
            candidate.predict({"image": planar_input})["depth"],
            args.width,
            args.height,
        )

        if not np.isfinite(baseline_output).all() or not np.isfinite(candidate_output).all():
            raise ValueError(f"{name} produced nonfinite output")
        difference = baseline_output - candidate_output
        mae = float(np.mean(np.abs(difference)))
        maximum_absolute_error = float(np.max(np.abs(difference)))
        rmse = float(np.sqrt(np.mean(np.square(difference))))
        reference_range = max(float(np.ptp(baseline_output)), 1e-12)
        reference_peak = max(float(np.max(np.abs(baseline_output))), 1e-12)
        normalized_rmse = rmse / reference_peak
        psnr = 20.0 * math.log10(reference_range / max(rmse, 1e-12))
        passed = (
            normalized_rmse <= args.maximum_normalized_rmse
            and maximum_absolute_error <= args.maximum_absolute_error
        )
        all_passed = all_passed and passed
        samples.append(
            {
                "name": name,
                "passed": passed,
                "mae": mae,
                "maximum_absolute_error": maximum_absolute_error,
                "rmse": rmse,
                "normalized_rmse": normalized_rmse,
                "psnr_db": psnr,
                "baseline_range": [
                    float(np.min(baseline_output)),
                    float(np.max(baseline_output)),
                ],
                "candidate_range": [
                    float(np.min(candidate_output)),
                    float(np.max(candidate_output)),
                ],
            }
        )

    timing_pixels = make_samples(args.width, args.height)[0][1]
    timing_image = Image.fromarray(timing_pixels)
    timing_tensor = np.transpose(timing_pixels, (2, 0, 1))[None].astype(np.float16)
    for index in range(args.warmups):
        if index % 2 == 0:
            baseline.predict({"image": timing_image})
            candidate.predict({"image": timing_tensor})
        else:
            candidate.predict({"image": timing_tensor})
            baseline.predict({"image": timing_image})

    baseline_timings = []
    candidate_timings = []
    for index in range(args.iterations):
        if index % 2 == 0:
            baseline_timings.append(predict_milliseconds(baseline, timing_image))
            candidate_timings.append(predict_milliseconds(candidate, timing_tensor))
        else:
            candidate_timings.append(predict_milliseconds(candidate, timing_tensor))
            baseline_timings.append(predict_milliseconds(baseline, timing_image))

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "macos": platform.mac_ver()[0],
            "machine": platform.machine(),
        },
        "coremltools_version": ct.__version__,
        "compute_units": "CPU_AND_GPU",
        "baseline": baseline_path.name,
        "candidate": candidate_path.name,
        "input_shape": [1, 3, args.height, args.width],
        "thresholds": {
            "maximum_normalized_rmse": args.maximum_normalized_rmse,
            "maximum_absolute_error": args.maximum_absolute_error,
        },
        "passed": all_passed,
        "samples": samples,
        "timing": {
            "scope": (
                "synchronous Core ML prediction with reused PIL-image baseline "
                "and planar-FP16 candidate inputs"
            ),
            "warmups": args.warmups,
            "iterations": args.iterations,
            "baseline_milliseconds": summarize(baseline_timings),
            "candidate_milliseconds": summarize(candidate_timings),
        },
    }
    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
