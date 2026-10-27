from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot training history.csv curves")
    p.add_argument("--run-dir", type=str, required=True)
    p.add_argument("--out", type=str, default="", help="Output PNG path (default: <run-dir>/curves.png)")
    return p.parse_args()


def load_history(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row: dict[str, float] = {}
            for k, v in r.items():
                if k == "epoch":
                    row[k] = float(int(v))
                else:
                    row[k] = float(v)
            rows.append(row)
    return rows


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = Path.cwd() / run_dir

    history_path = run_dir / "history.csv"
    if not history_path.exists():
        raise FileNotFoundError(f"Missing {history_path}")

    out_path = Path(args.out) if args.out else (run_dir / "curves.png")

    rows = load_history(history_path)
    epochs = [int(r["epoch"]) for r in rows]

    plt.figure(figsize=(12, 4))

    plt.subplot(1, 3, 1)
    plt.plot(epochs, [r["train_loss"] for r in rows], label="train")
    plt.plot(epochs, [r["val_loss"] for r in rows], label="val")
    plt.title("Total loss")
    plt.xlabel("epoch")
    plt.legend()

    plt.subplot(1, 3, 2)
    plt.plot(epochs, [r["val_miou"] for r in rows], label="val mIoU")
    plt.plot(epochs, [r["val_dice_fg"] for r in rows], label="val dice")
    plt.title("Segmentation (val)")
    plt.xlabel("epoch")
    plt.legend()

    plt.subplot(1, 3, 3)
    plt.plot(epochs, [r["val_f1"] for r in rows], label="val F1")
    plt.plot(epochs, [r["val_acc"] for r in rows], label="val accuracy")
    plt.title("Classification (val)")
    plt.xlabel("epoch")
    plt.legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
