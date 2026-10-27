from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from cse428_pets.engine import evaluate  # noqa: E402
from cse428_pets.models import UNetMultiTask  # noqa: E402
from cse428_pets.splits import make_splits  # noqa: E402
from cse428_pets.torch_dataset import OxfordPetsMultiTaskTorchDataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate a trained run on train/val/test")
    p.add_argument("--run-dir", type=str, required=True, help="Path to a run folder under runs/")
    p.add_argument("--weights", type=str, default="best.pt", help="best.pt|last.pt|path")
    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--num-workers", type=int, default=0)
    return p.parse_args()


def _resolve_device(device_s: str) -> torch.device:
    if device_s == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_s)


def main() -> None:
    args = parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = (REPO_ROOT / run_dir).resolve()

    config_path = run_dir / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config.json in {run_dir}")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    model_name = cfg.get("model", "unet")
    use_attention = model_name == "attunet"
    base_channels = int(cfg.get("base_channels", 64))

    weights_path = Path(args.weights)
    if not weights_path.is_absolute():
        weights_path = run_dir / args.weights
    if not weights_path.exists():
        raise FileNotFoundError(f"Missing weights: {weights_path}")

    device = _resolve_device(args.device)

    splits = make_splits(
        repo_root=REPO_ROOT,
        val_ratio=float(cfg.get("val_ratio", 0.2)),
        seed=int(cfg.get("seed", 42)),
    )

    def make_loader(samples: list, *, shuffle: bool) -> torch.utils.data.DataLoader:
        ds = OxfordPetsMultiTaskTorchDataset(
            samples,
            image_size=int(cfg.get("image_size", 256)),
            augment=False,
            max_rotate_deg=0.0,
            mask_mode="binary",
        )
        return torch.utils.data.DataLoader(
            ds,
            batch_size=args.batch_size,
            shuffle=shuffle,
            num_workers=args.num_workers,
            pin_memory=device.type == "cuda",
        )

    loaders = {
        "train": make_loader(splits.train, shuffle=False),
        "val": make_loader(splits.val, shuffle=False),
        "test": make_loader(splits.test, shuffle=False),
    }

    model = UNetMultiTask(num_classes=37, use_attention=use_attention, base_channels=base_channels)
    ckpt = torch.load(weights_path, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model.to(device)

    seg_weight = float(cfg.get("seg_weight", 1.0))
    cls_weight = float(cfg.get("cls_weight", 1.0))

    results: dict[str, dict] = {}
    for split_name, loader in loaders.items():
        stats = evaluate(
            model=model,
            loader=loader,
            device=device,
            seg_weight=seg_weight,
            cls_weight=cls_weight,
            threshold=0.5,
            num_classes=37,
        )
        results[split_name] = {
            "loss": stats.loss,
            "loss_seg": stats.loss_seg,
            "loss_cls": stats.loss_cls,
            "segmentation": stats.seg_metrics,
            "classification": stats.cls_metrics,
        }

        print(
            f"[{split_name}] mIoU={stats.seg_metrics.get('miou', float('nan')):.4f} "
            f"dice={stats.seg_metrics.get('dice_fg', float('nan')):.4f} "
            f"pixAcc={stats.seg_metrics.get('pixel_accuracy', float('nan')):.4f} | "
            f"acc={stats.cls_metrics.get('accuracy', float('nan')):.4f} "
            f"F1={stats.cls_metrics.get('f1', float('nan')):.4f}"
        )

    out_path = run_dir / "metrics.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
