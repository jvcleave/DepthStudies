import argparse
import math
import types
from pathlib import Path

import coremltools as ct
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


def main() -> None:
    args = parse_args()

    if args.width % 14 != 0 or args.height % 14 != 0:
        raise ValueError("Width and height must both be multiples of 14.")

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

    example_input = torch.rand(1, 3, args.height, args.width, dtype=torch.float32)
    traced_model = torch.jit.trace(wrapped_model, example_input)

    compute_precision = (
        ct.precision.FLOAT16 if args.compute_precision == "float16" else ct.precision.FLOAT32
    )

    mlmodel = ct.convert(
        traced_model,
        convert_to="mlprogram",
        compute_precision=compute_precision,
        minimum_deployment_target=ct.target.iOS16,
        inputs=[
            ct.ImageType(
                name="image",
                shape=example_input.shape,
                scale=1.0 / 255.0,
                bias=[0.0, 0.0, 0.0],
                color_layout=ct.colorlayout.RGB,
                channel_first=True,
            )
        ],
        outputs=[
            ct.ImageType(
                name="depth",
                color_layout=ct.colorlayout.GRAYSCALE_FLOAT16,
            )
        ],
    )

    mlmodel.short_description = (
        f"Custom Depth Anything V2 {args.encoder} export for MessApp realtime testing."
    )
    mlmodel.input_description["image"] = (
        "RGB image input scaled to [0, 1] by Core ML, then normalized with ImageNet mean/std."
    )
    mlmodel.output_description["depth"] = "Single-channel half-float relative depth map."

    args.output.parent.mkdir(parents=True, exist_ok=True)
    mlmodel.save(str(args.output))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
