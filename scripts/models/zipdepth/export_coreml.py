import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

import coremltools as ct
import numpy as np
import torch


EXPECTED_SOURCE_REVISION = "91f3fd21e131641f51e8d35736d1958350180e3a"
EXPECTED_CHECKPOINT_SHA256 = "627c04fda584133ead4310074884a4a037061b4c01ba86e73e492ea30fab570d"
EXPECTED_PYTHON_VERSION = (3, 9)
EXPECTED_TORCH_VERSION = "2.7.0"
EXPECTED_COREMLTOOLS_VERSION = "9.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the pinned ZipDepth base NPU checkpoint to Core ML."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Clean checkout of the official ZipDepth repository at the pinned revision.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Checkpoint path. Defaults to <source-root>/checkpoints/zipdepth_base_npu.pth.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=384,
        help="Fixed input width. Must be a positive multiple of 32.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=384,
        help="Fixed input height. Must be a positive multiple of 32.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination .mlpackage. The destination must not already exist.",
    )
    parser.add_argument(
        "--input-representation",
        choices=("image-f32", "tensor-f16"),
        default="image-f32",
        help=(
            "Core ML input contract. image-f32 preserves the deployable image "
            "package; tensor-f16 creates the graph-specific 0...255 planar tensor."
        ),
    )
    return parser.parse_args()


def run_git(source_root: Path, arguments: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_inputs(args: argparse.Namespace) -> tuple[Path, Path]:
    if sys.version_info[:2] != EXPECTED_PYTHON_VERSION:
        raise ValueError(
            "Expected Python "
            f"{EXPECTED_PYTHON_VERSION[0]}.{EXPECTED_PYTHON_VERSION[1]}, "
            f"got {sys.version_info.major}.{sys.version_info.minor}."
        )

    source_root = args.source_root.expanduser().resolve()
    if not source_root.is_dir():
        raise ValueError(f"ZipDepth source root does not exist: {source_root}")

    source_revision = run_git(source_root, ["rev-parse", "HEAD"])
    if source_revision != EXPECTED_SOURCE_REVISION:
        raise ValueError(
            f"Expected ZipDepth revision {EXPECTED_SOURCE_REVISION}, got {source_revision}."
        )

    dirty_paths = run_git(source_root, ["status", "--porcelain"])
    if dirty_paths:
        raise ValueError("ZipDepth source checkout must be clean before export.")

    checkpoint_path = (
        args.checkpoint.expanduser().resolve()
        if args.checkpoint
        else source_root / "checkpoints" / "zipdepth_base_npu.pth"
    )
    if not checkpoint_path.is_file():
        raise ValueError(f"ZipDepth checkpoint does not exist: {checkpoint_path}")

    checkpoint_sha256 = file_sha256(checkpoint_path)
    if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError(
            "ZipDepth checkpoint SHA-256 mismatch: "
            f"expected {EXPECTED_CHECKPOINT_SHA256}, got {checkpoint_sha256}."
        )

    if args.width <= 0 or args.height <= 0:
        raise ValueError("Width and height must be positive.")
    if args.width % 32 != 0 or args.height % 32 != 0:
        raise ValueError("Width and height must both be multiples of 32.")

    output_path = args.output.expanduser().resolve()
    if output_path.suffix != ".mlpackage":
        raise ValueError("Output path must use the .mlpackage extension.")
    if output_path.exists():
        raise ValueError(f"Output path already exists: {output_path}")

    torch_version = torch.__version__.split("+")[0]
    if torch_version != EXPECTED_TORCH_VERSION:
        raise ValueError(
            f"Expected PyTorch {EXPECTED_TORCH_VERSION}, got {torch.__version__}. "
            "Use requirements-zipdepth-export.txt."
        )
    if ct.__version__ != EXPECTED_COREMLTOOLS_VERSION:
        raise ValueError(
            f"Expected coremltools {EXPECTED_COREMLTOOLS_VERSION}, got {ct.__version__}. "
            "Use requirements-zipdepth-export.txt."
        )

    return source_root, checkpoint_path


class NormalizePixelTensor(torch.nn.Module):
    """Keep 0...255 normalization inside the graph-specific tensor model."""

    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model
        self.register_buffer(
            "pixel_scale",
            torch.tensor(1.0 / 255.0, dtype=torch.float32),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.model(image * self.pixel_scale)


def main() -> None:
    args = parse_args()
    source_root, checkpoint_path = validate_inputs(args)

    sys.path.insert(0, str(source_root))
    from zipdepth.model.architecture import create_model
    from zipdepth.utils.model_utils import (
        fuse_remaining_conv_bn,
        strip_state_dict_prefixes,
    )

    model = create_model(
        variant="base",
        global_mode="balanced",
        upsample_unfold=False,
    )
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    state_dict = strip_state_dict_prefixes(
        checkpoint.get("model_state_dict", checkpoint)
    )
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    if missing_keys or unexpected_keys:
        raise ValueError(
            "Checkpoint does not match the pinned ZipDepth base NPU architecture: "
            f"missing={missing_keys}, unexpected={unexpected_keys}"
        )

    model = model.eval()
    model.fuse_for_inference()
    fuse_remaining_conv_bn(model)

    torch.manual_seed(0)
    if args.input_representation == "image-f32":
        conversion_model = model
        example_input = torch.rand(
            1,
            3,
            args.height,
            args.width,
            dtype=torch.float32,
        )
        with torch.no_grad():
            example_output = conversion_model(example_input)
        coreml_inputs = [
            ct.ImageType(
                name="image",
                shape=example_input.shape,
                scale=1.0 / 255.0,
                bias=[0.0, 0.0, 0.0],
                color_layout=ct.colorlayout.RGB,
                channel_first=True,
            )
        ]
        coreml_outputs = [
            ct.ImageType(
                name="depth",
                color_layout=ct.colorlayout.GRAYSCALE_FLOAT16,
            )
        ]
    else:
        pixel_input_float32 = torch.randint(
            0,
            256,
            (1, 3, args.height, args.width),
            dtype=torch.int32,
        ).to(torch.float32)
        with torch.no_grad():
            reference_output = model(pixel_input_float32 * (1.0 / 255.0))
        conversion_model = NormalizePixelTensor(model).eval()
        example_input = pixel_input_float32
        with torch.no_grad():
            example_output = conversion_model(example_input)
        difference = reference_output - example_output.float()
        print(
            "PyTorch tensor-wrapper validation: "
            f"mae={difference.abs().mean().item():.9f}, "
            f"max_abs={difference.abs().max().item():.9f}, "
            f"rmse={difference.square().mean().sqrt().item():.9f}"
        )
        coreml_inputs = [
            ct.TensorType(
                name="image",
                shape=example_input.shape,
                dtype=np.float16,
            )
        ]
        coreml_outputs = [
            ct.TensorType(
                name="depth",
                dtype=np.float16,
            )
        ]

    expected_output_shape = (1, 1, args.height, args.width)
    if tuple(example_output.shape) != expected_output_shape:
        raise ValueError(
            f"Expected output shape {expected_output_shape}, got {tuple(example_output.shape)}."
        )
    if not torch.isfinite(example_output).all():
        raise ValueError("ZipDepth produced nonfinite output before conversion.")

    traced_model = torch.jit.trace(conversion_model, example_input)
    mlmodel = ct.convert(
        traced_model,
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT16,
        minimum_deployment_target=ct.target.iOS16,
        inputs=coreml_inputs,
        outputs=coreml_outputs,
    )

    mlmodel.author = "Fabio Tosi, Luca Bartolomei, Matteo Poggi, Stefano Mattoccia"
    mlmodel.license = "MIT"
    mlmodel.short_description = (
        "ZipDepth base NPU export for MESS relative-depth evaluation."
    )
    if args.input_representation == "image-f32":
        mlmodel.input_description["image"] = (
            "RGB image scaled to [0, 1] by Core ML; ZipDepth applies ImageNet normalization."
        )
    else:
        mlmodel.input_description["image"] = (
            "Planar float16 RGB tensor in 0...255; scaling and ImageNet normalization are in the graph."
        )
    mlmodel.output_description["depth"] = (
        "Single-channel half-float affine-invariant inverse-depth map."
    )
    mlmodel.user_defined_metadata["ZipDepthSourceRevision"] = EXPECTED_SOURCE_REVISION
    mlmodel.user_defined_metadata["ZipDepthCheckpointSHA256"] = (
        EXPECTED_CHECKPOINT_SHA256
    )
    mlmodel.user_defined_metadata["ZipDepthUpsampling"] = "NPU unfold-free"
    mlmodel.user_defined_metadata["ZipDepthInputShape"] = (
        f"1x3x{args.height}x{args.width}"
    )
    mlmodel.user_defined_metadata["ZipDepthInputRepresentation"] = (
        args.input_representation
    )

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mlmodel.save(str(output_path))
    print(f"Saved {output_path}")
    print(f"Source revision: {EXPECTED_SOURCE_REVISION}")
    print(f"Checkpoint SHA-256: {EXPECTED_CHECKPOINT_SHA256}")
    print(
        f"Input/output: {args.input_representation} RGB "
        f"{args.width}x{args.height} -> grayscale float16 depth"
    )


if __name__ == "__main__":
    main()
