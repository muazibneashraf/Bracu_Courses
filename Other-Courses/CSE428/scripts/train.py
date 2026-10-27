from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import torch

# Allow running from repo root without installing the package.
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from cse428_pets.engine import evaluate, train_one_epoch  # noqa: E402
from cse428_pets.models import UNetMultiTask  # noqa: E402
from cse428_pets.splits import make_splits  # noqa: E402
from cse428_pets.torch_dataset import OxfordPetsMultiTaskTorchDataset  # noqa: E402


def set_seed(seed: int) -> None:
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train U-Net / Attention U-Net (segmentation + classification)")
    p.add_argument("--model", choices=["unet", "attunet"], default="unet")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--image-size", type=int, default=256)
    p.add_argument("--base-channels", type=int, default=64, help="U-Net width multiplier (e.g., 32 for faster CPU)")
    p.add_argument("--val-ratio", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--seg-weight", type=float, default=1.0)
    p.add_argument("--cls-weight", type=float, default=1.0)
    p.add_argument("--max-rotate-deg", type=float, default=10.0)
    p.add_argument("--device", type=str, default="auto", help="auto|cpu|cuda")
    p.add_argument("--run-name", type=str, default="")
    p.add_argument("--out-dir", type=str, default=str(REPO_ROOT / "runs"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    splits = make_splits(repo_root=REPO_ROOT, val_ratio=args.val_ratio, seed=args.seed)

    train_ds = OxfordPetsMultiTaskTorchDataset(
        splits.train,
        image_size=args.image_size,
        augment=True,
        max_rotate_deg=args.max_rotate_deg,
        mask_mode="binary",
    )
    val_ds = OxfordPetsMultiTaskTorchDataset(
        splits.val,
        image_size=args.image_size,
        augment=False,
        max_rotate_deg=0.0,
        mask_mode="binary",
    )

    pin = device.type == "cuda"
    train_loader = torch.utils.data.DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=pin,
    )
    val_loader = torch.utils.data.DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=pin,
    )

    use_attention = args.model == "attunet"
    model = UNetMultiTask(num_classes=37, use_attention=use_attention, base_channels=args.base_channels)
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    ts = time.strftime("%Y%m%d_%H%M%S")
    run_name = args.run_name.strip() or f"{args.model}_{ts}"
    out_dir = Path(args.out_dir) / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "config.json").write_text(
        json.dumps(
            {
                **vars(args),
                "device_resolved": str(device),
                "run_name": run_name,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    history_path = out_dir / "history.csv"
    with history_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "epoch",
                "train_loss",
                "train_loss_seg",
                "train_loss_cls",
                "val_loss",
                "val_loss_seg",
                "val_loss_cls",
                "val_miou",
                "val_dice_fg",
                "val_pixel_accuracy",
                "val_acc",
                "val_precision",
                "val_recall",
                "val_f1",
            ],
        )
        writer.writeheader()

        best_val_miou = -1.0

        for epoch in range(1, args.epochs + 1):
            train_loss, train_loss_seg, train_loss_cls = train_one_epoch(
                model=model,
                loader=train_loader,
                optimizer=optimizer,
                device=device,
                seg_weight=args.seg_weight,
                cls_weight=args.cls_weight,
            )

            val_stats = evaluate(
                model=model,
                loader=val_loader,
                device=device,
                seg_weight=args.seg_weight,
                cls_weight=args.cls_weight,
                threshold=0.5,
                num_classes=37,
            )

            row = {
                "epoch": epoch,
                "train_loss": train_loss,
                "train_loss_seg": train_loss_seg,
                "train_loss_cls": train_loss_cls,
                "val_loss": val_stats.loss,
                "val_loss_seg": val_stats.loss_seg,
                "val_loss_cls": val_stats.loss_cls,
                "val_miou": val_stats.seg_metrics.get("miou", float("nan")),
                "val_dice_fg": val_stats.seg_metrics.get("dice_fg", float("nan")),
                "val_pixel_accuracy": val_stats.seg_metrics.get("pixel_accuracy", float("nan")),
                "val_acc": val_stats.cls_metrics.get("accuracy", float("nan")),
                "val_precision": val_stats.cls_metrics.get("precision", float("nan")),
                "val_recall": val_stats.cls_metrics.get("recall", float("nan")),
                "val_f1": val_stats.cls_metrics.get("f1", float("nan")),
            }
            writer.writerow(row)
            f.flush()

            print(
                f"Epoch {epoch:03d}/{args.epochs} "
                f"train_loss={train_loss:.4f} val_loss={val_stats.loss:.4f} "
                f"val_mIoU={row['val_miou']:.4f} val_F1={row['val_f1']:.4f}"
            )

            # Save checkpoints
            ckpt = {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "val_miou": row["val_miou"],
            }
            torch.save(ckpt, out_dir / "last.pt")

            if row["val_miou"] > best_val_miou:
                best_val_miou = row["val_miou"]
                torch.save(ckpt, out_dir / "best.pt")

    print(f"Run saved to: {out_dir}")


if __name__ == "__main__":
    main()
