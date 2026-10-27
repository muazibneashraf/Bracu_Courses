from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision.transforms import InterpolationMode
from torchvision.transforms import functional as TF

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from cse428_pets.dataset import prepare_mask, species_name  # noqa: E402
from cse428_pets.models import UNetMultiTask  # noqa: E402
from cse428_pets.splits import make_splits  # noqa: E402
from cse428_pets.viz import compute_iou_binary, plot_prediction_triplet, plot_random_overlay_grid  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Dataset exploration + demo visualizations")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grid", help="3x3 random mask overlay grid (dataset exploration)")
    g.add_argument("--split", choices=["train", "val", "test", "trainval"], default="trainval")
    g.add_argument("--seed", type=int, default=0)

    d = sub.add_parser("predict", help="Show the required 3-panel prediction layout")
    d.add_argument("--run-dir", type=str, required=True)
    d.add_argument("--weights", type=str, default="best.pt")
    d.add_argument("--split", choices=["train", "val", "test"], default="test")
    d.add_argument("--index", type=int, default=-1, help="Index within the chosen split. Use -1 for random.")
    d.add_argument("--device", type=str, default="auto")

    return p.parse_args()


def _resolve_device(device_s: str) -> torch.device:
    if device_s == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_s)


def _pretty_breed(breed: str) -> str:
    return breed.replace("_", " ")


def main() -> None:
    args = parse_args()

    if args.cmd == "grid":
        splits = make_splits(repo_root=REPO_ROOT, val_ratio=0.2, seed=42)
        if args.split == "train":
            samples = splits.train
        elif args.split == "val":
            samples = splits.val
        elif args.split == "test":
            samples = splits.test
        else:
            samples = [*splits.train, *splits.val]

        plot_random_overlay_grid(samples=samples, label_info=splits.label_info, seed=args.seed)
        return

    # predict
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = (REPO_ROOT / run_dir).resolve()

    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    model_name = cfg.get("model", "unet")
    use_attention = model_name == "attunet"
    image_size = int(cfg.get("image_size", 256))
    base_channels = int(cfg.get("base_channels", 64))

    weights_path = Path(args.weights)
    if not weights_path.is_absolute():
        weights_path = run_dir / args.weights

    device = _resolve_device(args.device)

    splits = make_splits(
        repo_root=REPO_ROOT,
        val_ratio=float(cfg.get("val_ratio", 0.2)),
        seed=int(cfg.get("seed", 42)),
    )

    model = UNetMultiTask(num_classes=37, use_attention=use_attention, base_channels=base_channels)
    ckpt = torch.load(weights_path, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model.to(device)
    model.eval()

    if args.split == "train":
        samples = splits.train
    elif args.split == "val":
        samples = splits.val
    else:
        samples = splits.test

    if args.index < 0:
        idx = random.randint(0, len(samples) - 1)
    else:
        idx = args.index
        if not (0 <= idx < len(samples)):
            raise ValueError(f"Index out of range: {idx} (split size {len(samples)})")

    s = samples[idx]

    # Load and resize for visualization
    img_pil = Image.open(s.image_path).convert("RGB")
    trimap = np.array(Image.open(s.mask_path), dtype=np.uint8)
    mask_true01 = prepare_mask(trimap, mode="binary")

    img_pil = TF.resize(img_pil, size=[image_size, image_size], interpolation=InterpolationMode.BILINEAR)
    mask_pil = Image.fromarray((mask_true01 * 255).astype(np.uint8), mode="L")
    mask_pil = TF.resize(mask_pil, size=[image_size, image_size], interpolation=InterpolationMode.NEAREST)
    mask_true01 = (np.array(mask_pil, dtype=np.uint8) > 127).astype(np.uint8)

    img_rgb = np.array(img_pil, dtype=np.uint8)

    # Model input (normalize)
    x = TF.to_tensor(img_pil)
    x = TF.normalize(x, mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
    x = x.unsqueeze(0).to(device)

    with torch.no_grad():
        seg_logits, cls_logits = model(x)
        seg_prob = torch.sigmoid(seg_logits)[0, 0].detach().cpu().numpy()
        mask_pred01 = (seg_prob >= 0.5).astype(np.uint8)
        pred_class = int(torch.argmax(cls_logits, dim=1).item())

    iou = compute_iou_binary(mask_true01, mask_pred01)

    true_breed = _pretty_breed(splits.label_info.class_id_to_breed.get(s.class_id, str(s.class_id)))
    true_species = species_name(int(s.species_id))
    pred_breed = _pretty_breed(splits.label_info.class_id_to_breed.get(pred_class, str(pred_class)))
    pred_species = species_name(int(splits.label_info.class_id_to_species.get(pred_class, 0)))

    true_label = f"{true_breed}" + f" ({true_species})"
    pred_label = f"{pred_breed}" + f" ({pred_species})"

    plot_prediction_triplet(
        image_rgb=img_rgb,
        mask_true01=mask_true01,
        mask_pred01=mask_pred01,
        true_label=true_label,
        pred_label=pred_label,
        iou=iou,
    )


if __name__ == "__main__":
    main()
