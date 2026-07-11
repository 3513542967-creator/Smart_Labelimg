from __future__ import annotations

import argparse
from pathlib import Path

import torch
from mobile_sam import sam_model_registry
from mobile_sam.utils.onnx import SamOnnxModel


class ImageEncoder(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.encoder = model.image_encoder

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.encoder(image)


def export(checkpoint: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    model = sam_model_registry["vit_t"](checkpoint=str(checkpoint)).eval()

    torch.onnx.export(
        ImageEncoder(model).eval(),
        (torch.randn(1, 3, 1024, 1024),),
        str(output_dir / "mobile_sam_encoder.onnx"),
        input_names=["image"],
        output_names=["image_embeddings"],
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )

    decoder = SamOnnxModel(model=model, return_single_mask=False).eval()
    embed_size = model.prompt_encoder.image_embedding_size
    inputs = (
        torch.randn(1, model.prompt_encoder.embed_dim, *embed_size),
        torch.randint(0, 1024, (1, 2, 2), dtype=torch.float32),
        torch.ones(1, 2, dtype=torch.float32),
        torch.zeros(1, 1, 256, 256),
        torch.zeros(1),
        torch.tensor([720, 1280], dtype=torch.float32),
    )
    torch.onnx.export(
        decoder,
        inputs,
        str(output_dir / "mobile_sam_decoder.onnx"),
        input_names=["image_embeddings", "point_coords", "point_labels", "mask_input", "has_mask_input", "orig_im_size"],
        output_names=["masks", "iou_predictions", "low_res_masks"],
        dynamic_axes={"point_coords": {1: "num_points"}, "point_labels": {1: "num_points"}, "masks": {2: "height", 3: "width"}},
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=Path("models/mobile_sam.pt"))
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    args = parser.parse_args()
    export(args.checkpoint, args.output_dir)
