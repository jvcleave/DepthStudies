import argparse
import math
import types
from collections import Counter
from pathlib import Path

import coremltools as ct
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from depth_anything_v2.dpt import DepthAnythingV2


MODEL_CONFIGS = {
    "vits": {"encoder": "vits", "features": 64, "out_channels": [48, 96, 192, 384]},
    "vitb": {"encoder": "vitb", "features": 128, "out_channels": [96, 192, 384, 768]},
    "vitl": {"encoder": "vitl", "features": 256, "out_channels": [256, 512, 1024, 1024]},
    "vitg": {"encoder": "vitg", "features": 384, "out_channels": [1536, 1536, 1536, 1536]},
}


class CoreMLDepthAnythingV2(nn.Module):
    def __init__(self, model: DepthAnythingV2):
        super().__init__()
        self.model = model.eval()
        self.register_buffer(
            "mean",
            torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1),
        )
        self.register_buffer(
            "std",
            torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        image = (image - self.mean) / self.std
        depth = self.model(image)
        return depth.unsqueeze(1)


class NormalizePixelTensor(nn.Module):
    """Keep 0...255 scaling inside the graph-specific tensor model."""

    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.register_buffer(
            "pixel_scale",
            torch.tensor(1.0 / 255.0, dtype=torch.float32),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.model(image * self.pixel_scale)


def stock_depth_head_forward(
    depth_head: nn.Module,
    out_features,
    patch_h: int,
    patch_w: int,
) -> torch.Tensor:
    out = []
    for i, x in enumerate(out_features):
        if depth_head.use_clstoken:
            x, cls_token = x[0], x[1]
            readout = cls_token.unsqueeze(1).expand_as(x)
            x = depth_head.readout_projects[i](torch.cat((x, readout), -1))
        else:
            x = x[0]

        x = x.permute(0, 2, 1).reshape((x.shape[0], x.shape[-1], patch_h, patch_w))
        x = depth_head.projects[i](x)
        x = depth_head.resize_layers[i](x)
        out.append(x)

    layer_1, layer_2, layer_3, layer_4 = out

    layer_1_rn = depth_head.scratch.layer1_rn(layer_1)
    layer_2_rn = depth_head.scratch.layer2_rn(layer_2)
    layer_3_rn = depth_head.scratch.layer3_rn(layer_3)
    layer_4_rn = depth_head.scratch.layer4_rn(layer_4)

    path_4 = depth_head.scratch.refinenet4(layer_4_rn, size=layer_3_rn.shape[2:])
    path_3 = depth_head.scratch.refinenet3(path_4, layer_3_rn, size=layer_2_rn.shape[2:])
    path_2 = depth_head.scratch.refinenet2(path_3, layer_2_rn, size=layer_1_rn.shape[2:])
    path_1 = depth_head.scratch.refinenet1(path_2, layer_1_rn)

    out = depth_head.scratch.output_conv1(path_1)
    out = F.interpolate(
        out,
        (int(patch_h * 14), int(patch_w * 14)),
        mode="bilinear",
        align_corners=True,
    )
    out = depth_head.scratch.output_conv2(out)
    return out


class CoreMLDepthAnythingV2Stock(nn.Module):
    def __init__(self, model: DepthAnythingV2):
        super().__init__()
        self.model = model.eval()
        self.register_buffer(
            "mean",
            torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1),
        )
        self.register_buffer(
            "std",
            torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        image = (image - self.mean) / self.std
        patch_h, patch_w = image.shape[-2] // 14, image.shape[-1] // 14
        features = self.model.pretrained.get_intermediate_layers(
            image,
            self.model.intermediate_layer_idx[self.model.encoder],
            return_class_token=True,
        )
        depth = stock_depth_head_forward(self.model.depth_head, features, patch_h, patch_w)
        depth = F.relu(depth)
        return depth


def model_patch_grid(width: int, height: int, patch_size: int = 14) -> tuple[int, int]:
    if width % patch_size != 0 or height % patch_size != 0:
        raise ValueError("Width and height must both be multiples of the patch size.")
    return width // patch_size, height // patch_size


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Depth Anything V2 to Core ML.")
    parser.add_argument(
        "--encoder",
        default="vits",
        choices=sorted(MODEL_CONFIGS.keys()),
        help="Backbone to export. Realtime experiments should start with vits.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("checkpoints/depth_anything_v2_vits.pth"),
        help="Path to the PyTorch checkpoint.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=448,
        help="Fixed model input width. Should stay a multiple of 14.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=336,
        help="Fixed model input height. Should stay a multiple of 14.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("DepthAnythingV2SmallRealtime.mlpackage"),
        help="Output mlpackage path.",
    )
    parser.add_argument(
        "--compute-precision",
        default="float16",
        choices=["float16", "float32"],
        help="Core ML compute precision for the exported mlprogram.",
    )
    parser.add_argument(
        "--pos-embed-interpolation",
        default="bilinear",
        choices=["bilinear", "bicubic", "precomputed-bicubic"],
        help="Interpolation mode for DINOv2 positional embeddings during export.",
    )
    parser.add_argument(
        "--model-semantics",
        default="optimized",
        choices=["optimized", "stock"],
        help="Use the current optimized export path or a stock-semantics path for comparison.",
    )
    parser.add_argument(
        "--attention-implementation",
        default="decomposed",
        choices=["decomposed", "sdpa"],
        help="Keep the source attention sequence or replace it in memory with native SDPA.",
    )
    parser.add_argument(
        "--input-representation",
        default="image-f32",
        choices=["image-f32", "tensor-f16"],
        help=(
            "Core ML input contract. image-f32 preserves the deployable image package; "
            "tensor-f16 creates the graph-specific 0...255 planar tensor."
        ),
    )
    return parser.parse_args()


def load_model(encoder: str, checkpoint_path: Path) -> DepthAnythingV2:
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    model = DepthAnythingV2(**MODEL_CONFIGS[encoder])
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint)
    model.eval()
    return model


def patch_positional_interpolation(model: DepthAnythingV2, mode: str) -> None:
    if mode == "bicubic":
        return

    def interpolate_pos_encoding(self, x, w, h):
        previous_dtype = x.dtype
        npatch = x.shape[1] - 1
        N = self.pos_embed.shape[1] - 1
        if npatch == N and w == h:
            return self.pos_embed
        pos_embed = self.pos_embed.float()
        class_pos_embed = pos_embed[:, 0]
        patch_pos_embed = pos_embed[:, 1:]
        dim = x.shape[-1]
        w0 = w // self.patch_size
        h0 = h // self.patch_size
        w0, h0 = w0 + self.interpolate_offset, h0 + self.interpolate_offset

        sqrt_N = math.sqrt(N)
        patch_pos_embed = torch.nn.functional.interpolate(
            patch_pos_embed.reshape(1, int(sqrt_N), int(sqrt_N), dim).permute(0, 3, 1, 2),
            size=(int(w0), int(h0)),
            mode=mode,
            align_corners=False,
            antialias=self.interpolate_antialias,
        )

        patch_pos_embed = patch_pos_embed.permute(0, 2, 3, 1).reshape(1, -1, dim)
        return torch.cat((class_pos_embed.unsqueeze(0), patch_pos_embed), dim=1).to(previous_dtype)

    model.pretrained.interpolate_pos_encoding = types.MethodType(
        interpolate_pos_encoding,
        model.pretrained,
    )


def precompute_bicubic_positional_embedding(
    model: DepthAnythingV2,
    width: int,
    height: int,
) -> None:
    patch_w, patch_h = model_patch_grid(width, height, model.pretrained.patch_size)
    token_count = patch_w * patch_h + 1
    dummy_tokens = torch.zeros(1, token_count, model.pretrained.embed_dim, dtype=torch.float32)
    with torch.no_grad():
        cached_pos_embed = model.pretrained.interpolate_pos_encoding(dummy_tokens, height, width)
    model.pretrained.register_buffer("_export_pos_embed", cached_pos_embed, persistent=False)

    def interpolate_pos_encoding(self, x, w, h):
        if int(w) == height and int(h) == width:
            return self._export_pos_embed.to(x.dtype)
        raise ValueError(
            f"Export-only positional embedding override expected {height}x{width}, got {w}x{h}"
        )

    model.pretrained.interpolate_pos_encoding = types.MethodType(
        interpolate_pos_encoding,
        model.pretrained,
    )


def install_sdpa_attention(model: DepthAnythingV2) -> int:
    from depth_anything_v2.dinov2_layers.attention import Attention

    def sdpa_forward(attention: Attention, x: torch.Tensor) -> torch.Tensor:
        batch_size, token_count, channel_count = x.shape
        head_dimension = channel_count // attention.num_heads
        expected_scale = head_dimension**-0.5
        if not math.isclose(attention.scale, expected_scale):
            raise ValueError(
                "Native DA2 SDPA export requires the default inverse-square-root attention scale"
            )
        qkv = attention.qkv(x).reshape(
            batch_size,
            token_count,
            3,
            attention.num_heads,
            head_dimension,
        )
        qkv = qkv.permute(2, 0, 3, 1, 4)
        query, key, value = qkv.unbind(0)
        x = F.scaled_dot_product_attention(
            query,
            key,
            value,
            dropout_p=0.0,
            is_causal=False,
        )
        x = x.transpose(1, 2).reshape(batch_size, token_count, channel_count)
        x = attention.proj(x)
        return attention.proj_drop(x)

    attention_count = 0
    for module in model.modules():
        if isinstance(module, Attention):
            module.forward = types.MethodType(sdpa_forward, module)
            attention_count += 1
    if attention_count == 0:
        raise ValueError("DA2 model did not contain any attention modules")
    return attention_count


def operation_inventory(mlmodel: ct.models.MLModel) -> Counter[str]:
    counts: Counter[str] = Counter()
    specification = mlmodel.get_spec()
    for function in specification.mlProgram.functions.values():
        for block in function.block_specializations.values():
            counts.update(operation.type for operation in block.operations)
    return counts


def main() -> None:
    args = parse_args()

    if args.width % 14 != 0 or args.height % 14 != 0:
        raise ValueError("Width and height must both be multiples of 14.")
    if args.attention_implementation == "sdpa" and args.input_representation == "tensor-f16":
        raise ValueError("Combined DA2 SDPA and tensor-FP16 export is outside this experiment")

    model = load_model(args.encoder, args.checkpoint)
    if args.pos_embed_interpolation == "precomputed-bicubic":
        precompute_bicubic_positional_embedding(model, args.width, args.height)
    else:
        patch_positional_interpolation(model, args.pos_embed_interpolation)
    wrapped_model = (
        CoreMLDepthAnythingV2Stock(model).eval()
        if args.model_semantics == "stock"
        else CoreMLDepthAnythingV2(model).eval()
    )

    torch.manual_seed(0)
    if args.input_representation == "image-f32":
        conversion_model = wrapped_model
        example_input = torch.rand(1, 3, args.height, args.width, dtype=torch.float32)
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
        example_input = torch.randint(
            0,
            256,
            (1, 3, args.height, args.width),
            dtype=torch.int32,
        ).to(torch.float32)
        conversion_model = NormalizePixelTensor(wrapped_model).eval()
        with torch.no_grad():
            direct_output = wrapped_model(example_input * (1.0 / 255.0))
            tensor_wrapper_output = conversion_model(example_input)
        wrapper_difference = direct_output - tensor_wrapper_output
        wrapper_maximum_absolute_error = wrapper_difference.abs().max().item()
        print(
            "PyTorch tensor-wrapper validation: "
            f"max_abs={wrapper_maximum_absolute_error:.9f}"
        )
        if wrapper_maximum_absolute_error > 1e-6:
            raise ValueError("DA2 tensor wrapper exceeded the PyTorch equivalence threshold")
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

    with torch.no_grad():
        reference_output = conversion_model(example_input)
    if args.attention_implementation == "sdpa":
        attention_count = install_sdpa_attention(model)
        with torch.no_grad():
            candidate_output = conversion_model(example_input)
        difference = reference_output - candidate_output
        maximum_absolute_error = difference.abs().max().item()
        root_mean_square_error = difference.square().mean().sqrt().item()
        reference_peak = max(reference_output.abs().max().item(), 1e-12)
        normalized_root_mean_square_error = root_mean_square_error / reference_peak
        print(
            "PyTorch SDPA validation: "
            f"attention_modules={attention_count}, "
            f"max_abs={maximum_absolute_error:.9f}, "
            f"normalized_rmse={normalized_root_mean_square_error:.9f}"
        )
        if maximum_absolute_error > 1e-5 or normalized_root_mean_square_error > 1e-5:
            raise ValueError("DA2 SDPA rewrite exceeded the PyTorch equivalence threshold")
    expected_output_shape = (1, 1, args.height, args.width)
    if tuple(reference_output.shape) != expected_output_shape:
        raise ValueError(
            f"Expected output shape {expected_output_shape}, got {tuple(reference_output.shape)}"
        )
    if not torch.isfinite(reference_output).all():
        raise ValueError("DA2 produced nonfinite output before conversion")
    traced_model = torch.jit.trace(conversion_model, example_input)

    compute_precision = (
        ct.precision.FLOAT16 if args.compute_precision == "float16" else ct.precision.FLOAT32
    )

    minimum_deployment_target = (
        ct.target.iOS18
        if args.attention_implementation == "sdpa"
        else ct.target.iOS16
    )
    mlmodel = ct.convert(
        traced_model,
        convert_to="mlprogram",
        compute_precision=compute_precision,
        minimum_deployment_target=minimum_deployment_target,
        inputs=coreml_inputs,
        outputs=coreml_outputs,
    )

    mlmodel.short_description = (
        f"Custom Depth Anything V2 {args.encoder} export for MessApp realtime testing."
    )
    if args.input_representation == "image-f32":
        mlmodel.input_description["image"] = (
            "RGB image scaled to [0, 1] by Core ML, then normalized with ImageNet mean/std."
        )
    else:
        mlmodel.input_description["image"] = (
            "Planar float16 RGB tensor in 0...255; scaling and ImageNet normalization are in the graph."
        )
    mlmodel.output_description["depth"] = "Single-channel half-float relative depth map."
    mlmodel.user_defined_metadata["DA2AttentionImplementation"] = (
        args.attention_implementation
    )
    mlmodel.user_defined_metadata["DA2InputRepresentation"] = args.input_representation

    operation_counts = operation_inventory(mlmodel)
    if args.attention_implementation == "sdpa":
        if operation_counts["scaled_dot_product_attention"] != attention_count:
            raise ValueError(
                "Core ML conversion did not preserve all DA2 attention blocks as native SDPA"
            )
        if operation_counts["matmul"] != 0 or operation_counts["softmax"] != 0:
            raise ValueError("Core ML conversion decomposed one or more DA2 attention blocks")
    print(
        "Core ML attention inventory: "
        f"scaled_dot_product_attention={operation_counts['scaled_dot_product_attention']}, "
        f"matmul={operation_counts['matmul']}, "
        f"softmax={operation_counts['softmax']}"
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    mlmodel.save(str(args.output))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
